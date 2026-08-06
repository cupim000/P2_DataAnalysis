# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project goal

This repo currently contains only raw e-commerce data (`data/*.csv`) and a brief for the analysis in `.llm/prd.md`. No analysis code, scripts, or output files exist yet — they are to be created as the project progresses.

The requested deliverable (from `.llm/prd.md`): a complete analysis of the CSV files in `data/`, presented as a single-page HTML report in a dark-mode, modern/futuristic theme.

Key constraint from the brief: **do not load all raw data into the LLM context at once**. Instead:
1. Join the tables and compute the needed KPIs first (via a script, not by having the LLM read raw rows).
2. Write the computed KPIs out to smaller intermediate files (e.g. JSON/CSV summaries).
3. Build the HTML presentation from those smaller KPI files, not from the raw CSVs.

There is no build/lint/test tooling yet — no `package.json`, `requirements.txt`, or similar. Whatever language/tooling is used for the KPI-computation step should be introduced deliberately (e.g. a Python script with pandas, or a Node script), and this file should be updated once that choice is made.

## Data files (`data/`)

Four CSVs, joinable on the id columns described below. Row counts include header.

- **`Dadosdoecommerce_clientes.csv`** (50 rows) — customers.
  `id_cliente, nome_cliente, estado, pais, data_cadastro`
- **`Dadosdoecommerce_produtos.csv`** (214 rows) — products.
  `id_produto, nome_produto, categoria, marca, preco_atual, data_criacao`
- **`Dadosdoecommerce_vendas.csv`** (3019 rows) — sales/orders, the fact table.
  `id_venda, data_venda, id_cliente, id_produto, canal_venda, quantidade, preco_unitario`
  Joins to clientes via `id_cliente` and produtos via `id_produto`.
- **`Dadosdoecommercepreco_competidores.csv`** (727 rows) — competitor pricing per product.
  `id_produto, nome_concorrente, preco_concorrente, data_coleta`

### Data quirks to handle during ingestion

- **Decimal separator is a comma, not a period**, and price columns are quoted because of it (e.g. `preco_unitario` = `"64,79"`, `preco_concorrente` = `"65,45"`). Convert `,` → `.` before parsing as float.
- **`Dadosdoecommercepreco_competidores.csv` has malformed rows**: some values in the `id_produto` column contain the entire row concatenated with whitespace (e.g. `"prd_2293732b7542        Mercado Livre        65,45        2026-01-11 17:35:52"`) instead of a clean product id. This needs cleaning/normalization (e.g. extract the leading `prd_...` token) before joining on `id_produto`.
- Dates are strings like `2025-12-13 17:38:09`; parse as datetime.
