# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project layout

The repo holds shared raw data plus two independent implementations of the same analysis/dashboard project:

- **`data/`** — raw e-commerce CSVs, shared by both versions below. Never move or duplicate these; both pipelines read from this single root-level folder.
- **`v1_local/`** — finished pipeline: local Python/pandas scripts that compute KPIs and render a static HTML dashboard. See `v1_local/README.md`.
- **`v2_supabase/`** — second version of the project: same data modeled as relational tables in a Supabase (Postgres) project, with KPIs computed as SQL aggregations instead of pandas. See `v2_supabase/README.md`.
- **`.llm/prd.md`** — original project brief (v1/v2 dashboard).
- **`.llm/prd_bot.md`** — brief for a third, not-yet-started component: a Telegram bot backed by Claude tool-use SQL over the same Supabase database (single `app.py`). It references a `PROJETO_REFERENCIA.md` for schema/business rules that does not exist yet in this repo — create it (or ask for it) before starting that work.
- **`.claude/skills/`, `.agents/skills/`, `skills-lock.json`** — installed Agent Skills (tooling, not project code): `supabase`, `supabase-postgres-best-practices`, and `ui-ux-pro-max` (design-system generator used to build the v2 dashboard's look — see `v2_supabase/design-system/`).

When working in `v1_local/` or `v2_supabase/`, treat each as self-contained: don't reach across into the other version's scripts, and don't write generated output into the sibling folder.

## v1_local — local pipeline

Two-stage pipeline, run via `v1_local/run_pipeline.py` (executes both stages in sequence):

1. `v1_local/scripts/compute_kpis.py` — reads the four CSVs from `../data/` (relative to `v1_local/`), cleans them, joins them, computes KPIs, and writes small JSON summaries to `v1_local/output/kpis/*.json`.
2. `v1_local/scripts/build_presentation.py` — reads only those JSON files (never the raw CSVs) and renders `v1_local/output/apresentacao.html`, a single dark-mode dashboard using Chart.js via CDN.

Run from `v1_local/`:
```bash
pip install -r requirements.txt
python run_pipeline.py
```

Key constraint carried over from the original brief: **don't load all raw CSV data into the LLM context at once** — the KPI-computation stage does that work deterministically and writes small intermediate files; only those small files should be read when building or debugging the presentation.

### Data files (`data/`, at repo root)

Four CSVs, joinable on the id columns described below.

- **`Dadosdoecommerce_clientes.csv`** — customers.
  `id_cliente, nome_cliente, estado, pais, data_cadastro`
- **`Dadosdoecommerce_produtos.csv`** — products.
  `id_produto, nome_produto, categoria, marca, preco_atual, data_criacao`
- **`Dadosdoecommerce_vendas.csv`** — sales/orders, the fact table.
  `id_venda, data_venda, id_cliente, id_produto, canal_venda, quantidade, preco_unitario`
  Joins to clientes via `id_cliente` and produtos via `id_produto`.
- **`Dadosdoecommercepreco_competidores.csv`** — competitor pricing per product.
  `id_produto, nome_concorrente, preco_concorrente, data_coleta`

### Data quirks handled during ingestion

- **Decimal separator is a comma, not a period**, and price columns are quoted because of it (e.g. `preco_unitario` = `"64,79"`, `preco_concorrente` = `"65,45"`). Converted `,` → `.` before parsing as float (`parse_price` in `compute_kpis.py`).
- **`Dadosdoecommercepreco_competidores.csv` has malformed rows**: some values in the `id_produto` column contain the entire row concatenated with whitespace instead of a clean product id. Normalized by extracting the leading `prd_[a-f0-9]+` token via regex before joining.
- Dates are parsed as datetime.

### Known modeling choice worth knowing

For the price-competitiveness KPIs (`compute_competitividade`), the per-product "diferença %" is derived from `preco_atual` vs. the already-aggregated `preco_medio_concorrente` — not from averaging the per-row percentage differences. This matters because average-of-ratios ≠ ratio-of-averages; deriving it from the aggregated price keeps the displayed percentage consistent with the two price columns shown next to it in the dashboard table.

## v2_supabase — Supabase pipeline

Supabase project **AnaliseDadosClaude** (ref `vkgefrcdztxhifzzmtzn`), also wired up as an MCP server in `.mcp.json`. Same source-of-truth `data/` CSVs as v1, but loaded into four Postgres tables (`clientes`, `produtos`, `vendas`, `competidores`, schema `public`) with FKs from `vendas`/`competidores` to `produtos`/`clientes`. RLS is enabled on all four tables with **no policies** — only a direct Postgres connection (`DATABASE_URL`, pooler connection string) or the service-role key can read/write; `anon`/`authenticated` have no API access.

Three scripts, run from `v2_supabase/`, all needing `DATABASE_URL` filled in `v2_supabase/.env` (gitignored):

1. `scripts/load_data.py` — reads the 4 CSVs from `../data/`, cleans them (same logic as v1), `TRUNCATE`s and reinserts all 4 tables. Idempotent; only needed when the source CSVs change.
2. `scripts/compute_kpis.py` — connects to Postgres and computes every KPI as a SQL aggregation (`GROUP BY`, `FILTER`, CTEs) run in the database; only the small aggregated result comes back to Python. Writes the same JSON shape as v1 to `output/kpis/*.json`.
3. `scripts/build_presentation.py` — reads only those JSONs (never touches the database) and renders `output/apresentacao.html`, a dark-mode Chart.js dashboard styled from the design system persisted at `design-system/analise-ecommerce-v2/` (generated via the `ui-ux-pro-max` skill).

`run_pipeline.py` runs steps 2 and 3 in sequence (does not reload data — run `load_data.py` separately for that).

```bash
pip install -r requirements.txt
python scripts/load_data.py      # only when data/ CSVs change
python run_pipeline.py           # KPIs (SQL) + dashboard HTML
```

### Cross-version quirk: orphan `vendas` rows

20 rows in `Dadosdoecommerce_vendas.csv` reference an `id_produto` that doesn't exist in `Dadosdoecommerce_produtos.csv` (dirty source data). v1 doesn't surface this because it uses `merge(how="left")` (the product columns become `NaN`). In v2, `vendas.id_produto` has an FK to `produtos`, so `load_data.py` drops those rows and logs it — `vendas` ends up with 3000 rows instead of 3020, so `numero_pedidos` legitimately differs between the two dashboards (3000 vs 3020). This is expected, not a bug.

### Chart type choice

`build_presentation.py` deliberately avoids pie/donut charts — the `ui-ux-pro-max` skill's chart-selection rules grade them accessibility "C" (color-only differentiation). Category/ranking breakdowns use horizontal bar charts (AAA) and time series use line charts (AA) instead.
