"""
Etapa 1 do pipeline de analise: le os CSVs brutos em data/, limpa e junta
as tabelas, calcula os KPIs e grava arquivos JSON pequenos em output/kpis/.

Nao deve ser necessario reabrir os CSVs brutos depois desta etapa - a
etapa seguinte (build_presentation.py) le apenas os JSONs gerados aqui.
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "output" / "kpis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRODUTO_ID_RE = re.compile(r"(prd_[a-f0-9]+)")


def parse_price(series: pd.Series) -> pd.Series:
    """Converte precos com virgula decimal (ex: '64,79') para float."""
    return series.astype(str).str.replace(",", ".", regex=False).astype(float)


def load_data():
    clientes = pd.read_csv(DATA_DIR / "Dadosdoecommerce_clientes.csv")
    clientes["data_cadastro"] = pd.to_datetime(clientes["data_cadastro"])

    produtos = pd.read_csv(DATA_DIR / "Dadosdoecommerce_produtos.csv")
    produtos["data_criacao"] = pd.to_datetime(produtos["data_criacao"])

    vendas = pd.read_csv(DATA_DIR / "Dadosdoecommerce_vendas.csv")
    vendas["data_venda"] = pd.to_datetime(vendas["data_venda"])
    vendas["preco_unitario"] = parse_price(vendas["preco_unitario"])
    vendas["receita"] = vendas["quantidade"] * vendas["preco_unitario"]

    competidores = pd.read_csv(DATA_DIR / "Dadosdoecommercepreco_competidores.csv")
    # Algumas linhas trazem o id_produto concatenado com o resto da linha
    # (ex: "prd_2293732b7542        Mercado Livre        65,45        ...").
    # Extrai apenas o token do id em qualquer um dos casos.
    competidores["id_produto"] = competidores["id_produto"].astype(str).str.extract(
        PRODUTO_ID_RE
    )[0]
    competidores["preco_concorrente"] = parse_price(competidores["preco_concorrente"])
    competidores["data_coleta"] = pd.to_datetime(competidores["data_coleta"])
    competidores = competidores.dropna(subset=["id_produto"])

    return clientes, produtos, vendas, competidores


def build_vendas_enriquecidas(vendas, produtos, clientes):
    df = vendas.merge(produtos, on="id_produto", how="left", suffixes=("", "_produto"))
    df = df.merge(clientes, on="id_cliente", how="left", suffixes=("", "_cliente"))
    return df


def round2(x):
    return round(float(x), 2)


def compute_vendas_geral(df):
    receita_total = round2(df["receita"].sum())
    numero_pedidos = int(len(df))
    quantidade_total = int(df["quantidade"].sum())
    ticket_medio = round2(receita_total / numero_pedidos)

    por_mes = (
        df.assign(mes=df["data_venda"].dt.to_period("M").astype(str))
        .groupby("mes")["receita"]
        .sum()
        .sort_index()
    )
    receita_por_mes = [
        {"mes": mes, "receita": round2(valor)} for mes, valor in por_mes.items()
    ]

    canal = df.groupby("canal_venda").agg(
        receita=("receita", "sum"), pedidos=("id_venda", "count")
    )
    receita_por_canal = [
        {
            "canal": canal_nome,
            "receita": round2(row["receita"]),
            "pedidos": int(row["pedidos"]),
            "ticket_medio": round2(row["receita"] / row["pedidos"]),
        }
        for canal_nome, row in canal.iterrows()
    ]

    return {
        "receita_total": receita_total,
        "numero_pedidos": numero_pedidos,
        "quantidade_total_itens": quantidade_total,
        "ticket_medio": ticket_medio,
        "receita_por_mes": receita_por_mes,
        "receita_por_canal": receita_por_canal,
    }


def compute_produtos(df, produtos):
    por_produto = df.groupby(["id_produto", "nome_produto"]).agg(
        receita=("receita", "sum"), quantidade=("quantidade", "sum")
    )

    top_receita = por_produto.sort_values("receita", ascending=False).head(10)
    top_10_receita = [
        {"produto": nome, "receita": round2(row["receita"])}
        for (_, nome), row in top_receita.iterrows()
    ]

    top_quantidade = por_produto.sort_values("quantidade", ascending=False).head(10)
    top_10_quantidade = [
        {"produto": nome, "quantidade": int(row["quantidade"])}
        for (_, nome), row in top_quantidade.iterrows()
    ]

    receita_por_categoria = (
        df.groupby("categoria")["receita"].sum().sort_values(ascending=False)
    )
    receita_por_categoria = [
        {"categoria": cat, "receita": round2(val)}
        for cat, val in receita_por_categoria.items()
    ]

    receita_por_marca = (
        df.groupby("marca")["receita"].sum().sort_values(ascending=False).head(10)
    )
    receita_por_marca = [
        {"marca": marca, "receita": round2(val)}
        for marca, val in receita_por_marca.items()
    ]

    preco_medio_categoria = (
        produtos.groupby("categoria")["preco_atual"].mean().sort_values(ascending=False)
    )
    preco_medio_por_categoria = [
        {"categoria": cat, "preco_medio": round2(val)}
        for cat, val in preco_medio_categoria.items()
    ]

    return {
        "top_10_receita": top_10_receita,
        "top_10_quantidade": top_10_quantidade,
        "receita_por_categoria": receita_por_categoria,
        "receita_por_marca": receita_por_marca,
        "preco_medio_por_categoria": preco_medio_por_categoria,
    }


def compute_clientes(df, clientes):
    receita_por_estado = (
        df.groupby("estado")["receita"].sum().sort_values(ascending=False)
    )
    receita_por_estado = [
        {"estado": estado, "receita": round2(val)}
        for estado, val in receita_por_estado.items()
    ]

    clientes_por_estado = clientes.groupby("estado")["id_cliente"].count().sort_values(
        ascending=False
    )
    clientes_por_estado = [
        {"estado": estado, "clientes": int(val)}
        for estado, val in clientes_por_estado.items()
    ]

    novos_por_mes = (
        clientes.assign(mes=clientes["data_cadastro"].dt.to_period("M").astype(str))
        .groupby("mes")["id_cliente"]
        .count()
        .sort_index()
    )
    novos_cadastros_por_mes = [
        {"mes": mes, "novos_clientes": int(val)} for mes, val in novos_por_mes.items()
    ]

    por_cliente = df.groupby(["id_cliente", "nome_cliente"])["receita"].sum()
    ticket_medio_por_cliente = round2(por_cliente.mean())

    top_clientes = por_cliente.sort_values(ascending=False).head(10)
    top_10_clientes = [
        {"cliente": nome, "receita": round2(val)}
        for (_, nome), val in top_clientes.items()
    ]

    return {
        "receita_por_estado": receita_por_estado,
        "clientes_por_estado": clientes_por_estado,
        "novos_cadastros_por_mes": novos_cadastros_por_mes,
        "ticket_medio_por_cliente": ticket_medio_por_cliente,
        "top_10_clientes": top_10_clientes,
    }


def compute_competitividade(competidores, produtos):
    comp = competidores.merge(
        produtos[["id_produto", "nome_produto", "categoria", "preco_atual"]],
        on="id_produto",
        how="inner",
    )
    comp["diff_pct"] = (
        (comp["preco_atual"] - comp["preco_concorrente"]) / comp["preco_concorrente"]
    ) * 100

    por_produto = comp.groupby(["id_produto", "nome_produto", "preco_atual"]).agg(
        preco_medio_concorrente=("preco_concorrente", "mean"),
        preco_min_concorrente=("preco_concorrente", "min"),
        preco_max_concorrente=("preco_concorrente", "max"),
    )
    # Calculada a partir do preco_medio_concorrente (nao pela media das
    # diferencas linha a linha) para que a % bata com as duas colunas de
    # preco exibidas lado a lado na tabela.
    por_produto["diff_pct_medio"] = (
        (por_produto.index.get_level_values("preco_atual") - por_produto["preco_medio_concorrente"])
        / por_produto["preco_medio_concorrente"]
    ) * 100

    mais_caros = por_produto.sort_values(
        ["diff_pct_medio", "preco_atual"], ascending=[False, False]
    ).head(10)
    top_10_mais_caros_que_mercado = [
        {
            "produto": nome,
            "preco_atual": round2(preco_atual),
            "preco_medio_concorrente": round2(row["preco_medio_concorrente"]),
            "diff_pct": round2(row["diff_pct_medio"]),
        }
        for (_, nome, preco_atual), row in mais_caros.iterrows()
    ]

    mais_baratos = por_produto.sort_values(
        ["diff_pct_medio", "preco_atual"], ascending=[True, False]
    ).head(10)
    top_10_mais_baratos_que_mercado = [
        {
            "produto": nome,
            "preco_atual": round2(preco_atual),
            "preco_medio_concorrente": round2(row["preco_medio_concorrente"]),
            "diff_pct": round2(row["diff_pct_medio"]),
        }
        for (_, nome, preco_atual), row in mais_baratos.iterrows()
    ]

    qtd_mais_caro = int((por_produto["diff_pct_medio"] > 0).sum())
    qtd_mais_barato = int((por_produto["diff_pct_medio"] < 0).sum())
    qtd_igual = int((por_produto["diff_pct_medio"] == 0).sum())

    por_concorrente = comp.groupby("nome_concorrente")["diff_pct"].mean().sort_values(
        ascending=False
    )
    breakdown_por_concorrente = [
        {"concorrente": nome, "diff_pct_medio": round2(val)}
        for nome, val in por_concorrente.items()
    ]

    return {
        "produtos_analisados": int(len(por_produto)),
        "produtos_mais_caros_que_mercado": qtd_mais_caro,
        "produtos_mais_baratos_que_mercado": qtd_mais_barato,
        "produtos_no_preco_de_mercado": qtd_igual,
        "top_10_mais_caros_que_mercado": top_10_mais_caros_que_mercado,
        "top_10_mais_baratos_que_mercado": top_10_mais_baratos_que_mercado,
        "breakdown_por_concorrente": breakdown_por_concorrente,
    }


def main():
    clientes, produtos, vendas, competidores = load_data()
    df = build_vendas_enriquecidas(vendas, produtos, clientes)

    kpis = {
        "vendas_geral.json": compute_vendas_geral(df),
        "produtos.json": compute_produtos(df, produtos),
        "clientes.json": compute_clientes(df, clientes),
        "competitividade.json": compute_competitividade(competidores, produtos),
    }

    for filename, payload in kpis.items():
        path = OUT_DIR / filename
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"gravado {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
