# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project layout

The repo holds shared raw data plus two independent implementations of the same analysis/dashboard project:

- **`data/`** — raw e-commerce CSVs, shared by both versions below. Never move or duplicate these; both pipelines read from this single root-level folder.
- **`v1_local/`** — finished pipeline: local Python/pandas scripts that compute KPIs and render a static HTML dashboard. See `v1_local/README.md`.
- **`v2_supabase/`** — second version of the project, built on Supabase. In progress; scaffold only so far (`v2_supabase/scripts/`).
- **`.llm/prd.md`** — original project brief.

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

## v2_supabase

Not yet implemented beyond an empty `scripts/` folder. Update this section once the approach (schema, ingestion method, dashboard tech) is decided.
