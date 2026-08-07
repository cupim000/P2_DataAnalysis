"""
Etapa 1 do pipeline v2 (Supabase): conecta no Postgres do projeto e roda os
KPIs como agregacoes SQL diretamente no banco (GROUP BY / joins), em vez de
puxar as tabelas inteiras para pandas. So o resultado ja agregado (pequeno)
volta para Python e vira JSON em output/kpis/.

A etapa seguinte (build_presentation.py) le apenas esses JSONs - nunca
reabre a conexao com o banco.

Requer DATABASE_URL preenchido em v2_supabase/.env.
"""

import json
import os
from decimal import Decimal
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "kpis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")


def to_jsonable(value):
    """Converte Decimal (retorno padrao do psycopg2 para numeric) em float."""
    if isinstance(value, Decimal):
        return round(float(value), 2)
    return value


def rows(cur, sql, params=None):
    cur.execute(sql, params or ())
    return [{k: to_jsonable(v) for k, v in r.items()} for r in cur.fetchall()]


def one(cur, sql, params=None):
    cur.execute(sql, params or ())
    r = cur.fetchone()
    return {k: to_jsonable(v) for k, v in r.items()} if r else {}


def compute_vendas_geral(cur):
    totais = one(
        cur,
        """
        SELECT
            ROUND(SUM(quantidade * preco_unitario)::numeric, 2) AS receita_total,
            COUNT(*) AS numero_pedidos,
            SUM(quantidade) AS quantidade_total_itens,
            ROUND((SUM(quantidade * preco_unitario) / COUNT(*))::numeric, 2) AS ticket_medio
        FROM vendas
        """,
    )

    receita_por_mes = rows(
        cur,
        """
        SELECT
            TO_CHAR(DATE_TRUNC('month', data_venda), 'YYYY-MM') AS mes,
            ROUND(SUM(quantidade * preco_unitario)::numeric, 2) AS receita
        FROM vendas
        GROUP BY 1
        ORDER BY 1
        """,
    )

    receita_por_canal = rows(
        cur,
        """
        SELECT
            canal_venda AS canal,
            ROUND(SUM(quantidade * preco_unitario)::numeric, 2) AS receita,
            COUNT(*) AS pedidos,
            ROUND((SUM(quantidade * preco_unitario) / COUNT(*))::numeric, 2) AS ticket_medio
        FROM vendas
        GROUP BY canal_venda
        ORDER BY receita DESC
        """,
    )

    return {**totais, "receita_por_mes": receita_por_mes, "receita_por_canal": receita_por_canal}


def compute_produtos(cur):
    top_10_receita = rows(
        cur,
        """
        SELECT p.nome_produto AS produto,
               ROUND(SUM(v.quantidade * v.preco_unitario)::numeric, 2) AS receita
        FROM vendas v
        JOIN produtos p ON p.id_produto = v.id_produto
        GROUP BY p.nome_produto
        ORDER BY receita DESC
        LIMIT 10
        """,
    )

    top_10_quantidade = rows(
        cur,
        """
        SELECT p.nome_produto AS produto,
               SUM(v.quantidade) AS quantidade
        FROM vendas v
        JOIN produtos p ON p.id_produto = v.id_produto
        GROUP BY p.nome_produto
        ORDER BY quantidade DESC
        LIMIT 10
        """,
    )

    receita_por_categoria = rows(
        cur,
        """
        SELECT p.categoria AS categoria,
               ROUND(SUM(v.quantidade * v.preco_unitario)::numeric, 2) AS receita
        FROM vendas v
        JOIN produtos p ON p.id_produto = v.id_produto
        GROUP BY p.categoria
        ORDER BY receita DESC
        """,
    )

    receita_por_marca = rows(
        cur,
        """
        SELECT p.marca AS marca,
               ROUND(SUM(v.quantidade * v.preco_unitario)::numeric, 2) AS receita
        FROM vendas v
        JOIN produtos p ON p.id_produto = v.id_produto
        GROUP BY p.marca
        ORDER BY receita DESC
        LIMIT 10
        """,
    )

    preco_medio_por_categoria = rows(
        cur,
        """
        SELECT categoria, ROUND(AVG(preco_atual)::numeric, 2) AS preco_medio
        FROM produtos
        GROUP BY categoria
        ORDER BY preco_medio DESC
        """,
    )

    return {
        "top_10_receita": top_10_receita,
        "top_10_quantidade": top_10_quantidade,
        "receita_por_categoria": receita_por_categoria,
        "receita_por_marca": receita_por_marca,
        "preco_medio_por_categoria": preco_medio_por_categoria,
    }


def compute_clientes(cur):
    receita_por_estado = rows(
        cur,
        """
        SELECT c.estado AS estado,
               ROUND(SUM(v.quantidade * v.preco_unitario)::numeric, 2) AS receita
        FROM vendas v
        JOIN clientes c ON c.id_cliente = v.id_cliente
        GROUP BY c.estado
        ORDER BY receita DESC
        """,
    )

    clientes_por_estado = rows(
        cur,
        """
        SELECT estado, COUNT(*) AS clientes
        FROM clientes
        GROUP BY estado
        ORDER BY clientes DESC
        """,
    )

    novos_cadastros_por_mes = rows(
        cur,
        """
        SELECT TO_CHAR(DATE_TRUNC('month', data_cadastro), 'YYYY-MM') AS mes,
               COUNT(*) AS novos_clientes
        FROM clientes
        GROUP BY 1
        ORDER BY 1
        """,
    )

    ticket_medio_por_cliente = one(
        cur,
        """
        SELECT ROUND(AVG(receita_cliente)::numeric, 2) AS ticket_medio_por_cliente
        FROM (
            SELECT id_cliente, SUM(quantidade * preco_unitario) AS receita_cliente
            FROM vendas
            GROUP BY id_cliente
        ) t
        """,
    )["ticket_medio_por_cliente"]

    top_10_clientes = rows(
        cur,
        """
        SELECT c.nome_cliente AS cliente,
               ROUND(SUM(v.quantidade * v.preco_unitario)::numeric, 2) AS receita
        FROM vendas v
        JOIN clientes c ON c.id_cliente = v.id_cliente
        GROUP BY c.nome_cliente
        ORDER BY receita DESC
        LIMIT 10
        """,
    )

    return {
        "receita_por_estado": receita_por_estado,
        "clientes_por_estado": clientes_por_estado,
        "novos_cadastros_por_mes": novos_cadastros_por_mes,
        "ticket_medio_por_cliente": ticket_medio_por_cliente,
        "top_10_clientes": top_10_clientes,
    }


def compute_competitividade(cur):
    # Por produto: diff % calculada a partir do preco_medio_concorrente ja
    # agregado (nao da media das diferencas linha a linha), para bater com
    # as duas colunas de preco exibidas lado a lado na tabela do dashboard.
    por_produto_sql = """
        WITH por_produto AS (
            SELECT
                p.id_produto,
                p.nome_produto,
                p.preco_atual,
                AVG(cp.preco_concorrente) AS preco_medio_concorrente
            FROM competidores cp
            JOIN produtos p ON p.id_produto = cp.id_produto
            GROUP BY p.id_produto, p.nome_produto, p.preco_atual
        ),
        com_diff AS (
            SELECT *,
                ((preco_atual - preco_medio_concorrente) / preco_medio_concorrente) * 100 AS diff_pct_medio
            FROM por_produto
        )
        SELECT * FROM com_diff
    """

    resumo = one(
        cur,
        f"""
        WITH com_diff AS ({por_produto_sql})
        SELECT
            COUNT(*) AS produtos_analisados,
            COUNT(*) FILTER (WHERE diff_pct_medio > 0) AS produtos_mais_caros_que_mercado,
            COUNT(*) FILTER (WHERE diff_pct_medio < 0) AS produtos_mais_baratos_que_mercado,
            COUNT(*) FILTER (WHERE diff_pct_medio = 0) AS produtos_no_preco_de_mercado
        FROM com_diff
        """,
    )

    top_10_mais_caros_que_mercado = rows(
        cur,
        f"""
        WITH com_diff AS ({por_produto_sql})
        SELECT nome_produto AS produto,
               ROUND(preco_atual::numeric, 2) AS preco_atual,
               ROUND(preco_medio_concorrente::numeric, 2) AS preco_medio_concorrente,
               ROUND(diff_pct_medio::numeric, 2) AS diff_pct
        FROM com_diff
        ORDER BY diff_pct_medio DESC, preco_atual DESC
        LIMIT 10
        """,
    )

    top_10_mais_baratos_que_mercado = rows(
        cur,
        f"""
        WITH com_diff AS ({por_produto_sql})
        SELECT nome_produto AS produto,
               ROUND(preco_atual::numeric, 2) AS preco_atual,
               ROUND(preco_medio_concorrente::numeric, 2) AS preco_medio_concorrente,
               ROUND(diff_pct_medio::numeric, 2) AS diff_pct
        FROM com_diff
        ORDER BY diff_pct_medio ASC, preco_atual DESC
        LIMIT 10
        """,
    )

    # Breakdown por concorrente: media das diferencas linha a linha (nao a
    # agregada por produto) - mostra o quanto cada concorrente, em media,
    # cobra a mais/menos que o nosso preco, cotacao a cotacao.
    breakdown_por_concorrente = rows(
        cur,
        """
        SELECT
            cp.nome_concorrente AS concorrente,
            ROUND(AVG(((p.preco_atual - cp.preco_concorrente) / cp.preco_concorrente) * 100)::numeric, 2) AS diff_pct_medio
        FROM competidores cp
        JOIN produtos p ON p.id_produto = cp.id_produto
        GROUP BY cp.nome_concorrente
        ORDER BY diff_pct_medio DESC
        """,
    )

    return {
        **resumo,
        "top_10_mais_caros_que_mercado": top_10_mais_caros_que_mercado,
        "top_10_mais_baratos_que_mercado": top_10_mais_baratos_que_mercado,
        "breakdown_por_concorrente": breakdown_por_concorrente,
    }


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url or "[YOUR-PASSWORD]" in database_url:
        raise SystemExit(
            "Preencha DATABASE_URL em v2_supabase/.env com a senha do banco "
            "(https://supabase.com/dashboard/project/vkgefrcdztxhifzzmtzn/settings/database)"
        )

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            kpis = {
                "vendas_geral.json": compute_vendas_geral(cur),
                "produtos.json": compute_produtos(cur),
                "clientes.json": compute_clientes(cur),
                "competitividade.json": compute_competitividade(cur),
            }
    finally:
        conn.close()

    for filename, payload in kpis.items():
        path = OUT_DIR / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"gravado {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
