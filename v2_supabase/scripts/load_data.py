"""
Le os CSVs brutos em ../data/, limpa (mesma logica do v1_local), apaga o
conteudo atual das tabelas e reinsere tudo do zero nas tabelas
clientes/produtos/vendas/competidores do projeto Supabase AnaliseDadosClaude.

Requer DATABASE_URL preenchido em v2_supabase/.env.
"""

import os
import re
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT.parent / "data"

load_dotenv(ROOT / ".env")

PRODUTO_ID_RE = re.compile(r"(prd_[a-f0-9]+)")


def parse_price(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(",", ".", regex=False).astype(float)


def load_data():
    clientes = pd.read_csv(DATA_DIR / "Dadosdoecommerce_clientes.csv")
    clientes["data_cadastro"] = pd.to_datetime(clientes["data_cadastro"])

    produtos = pd.read_csv(DATA_DIR / "Dadosdoecommerce_produtos.csv")
    produtos["data_criacao"] = pd.to_datetime(produtos["data_criacao"])
    produtos["preco_atual"] = parse_price(produtos["preco_atual"])

    vendas = pd.read_csv(DATA_DIR / "Dadosdoecommerce_vendas.csv")
    vendas["data_venda"] = pd.to_datetime(vendas["data_venda"])
    vendas["preco_unitario"] = parse_price(vendas["preco_unitario"])

    competidores = pd.read_csv(DATA_DIR / "Dadosdoecommercepreco_competidores.csv")
    competidores["id_produto"] = competidores["id_produto"].astype(str).str.extract(
        PRODUTO_ID_RE
    )[0]
    competidores["preco_concorrente"] = parse_price(competidores["preco_concorrente"])
    competidores["data_coleta"] = pd.to_datetime(competidores["data_coleta"])
    competidores = competidores.dropna(subset=["id_produto"])

    # data/ traz vendas e cotacoes de concorrentes referenciando alguns
    # id_produto que nao existem em produtos.csv (dado sujo na fonte, nao
    # detectado antes pois v1_local usa merge(how="left")). Sem uma tabela
    # produtos para dar FK, essas linhas nao tem como ser inseridas.
    produto_ids = set(produtos["id_produto"])

    vendas_orfas = ~vendas["id_produto"].isin(produto_ids)
    if vendas_orfas.any():
        print(f"vendas: descartando {vendas_orfas.sum()} linha(s) com id_produto inexistente em produtos")
        vendas = vendas[~vendas_orfas]

    competidores_orfaos = ~competidores["id_produto"].isin(produto_ids)
    if competidores_orfaos.any():
        print(f"competidores: descartando {competidores_orfaos.sum()} linha(s) com id_produto inexistente em produtos")
        competidores = competidores[~competidores_orfaos]

    return clientes, produtos, vendas, competidores


def truncate_all(cur):
    # Ordem respeita as FKs: vendas/competidores referenciam produtos/clientes.
    cur.execute("TRUNCATE TABLE vendas, competidores, produtos, clientes")
    print("Tabelas truncadas: vendas, competidores, produtos, clientes")


def insert(cur, table, cols, df):
    rows = [tuple(r) for r in df[cols].itertuples(index=False, name=None)]
    execute_values(
        cur,
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s ON CONFLICT DO NOTHING",
        rows,
        page_size=500,
    )
    print(f"{table}: {len(rows)} linhas enviadas")


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url or "[YOUR-PASSWORD]" in database_url:
        raise SystemExit(
            "Preencha DATABASE_URL em v2_supabase/.env com a senha do banco "
            "(https://supabase.com/dashboard/project/vkgefrcdztxhifzzmtzn/settings/database)"
        )

    clientes, produtos, vendas, competidores = load_data()

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            truncate_all(cur)
            insert(cur, "clientes", ["id_cliente", "nome_cliente", "estado", "pais", "data_cadastro"], clientes)
            insert(cur, "produtos", ["id_produto", "nome_produto", "categoria", "marca", "preco_atual", "data_criacao"], produtos)
            insert(cur, "vendas", ["id_venda", "data_venda", "id_cliente", "id_produto", "canal_venda", "quantidade", "preco_unitario"], vendas)
            insert(cur, "competidores", ["id_produto", "nome_concorrente", "preco_concorrente", "data_coleta"], competidores)
        conn.commit()
    finally:
        conn.close()

    print("Concluido.")


if __name__ == "__main__":
    main()
