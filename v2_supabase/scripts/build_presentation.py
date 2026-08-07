"""
Etapa 2 do pipeline v2 (Supabase): le apenas os JSONs pequenos gerados por
compute_kpis.py (output/kpis/) e monta o dashboard final em HTML.

Nunca reabre a conexao com o banco - so consome os KPIs ja agregados.

Design system aplicado (gerado com a skill ui-ux-pro-max e persistido em
design-system/analise-ecommerce-v2/): Dark Mode OLED, tipografia Fira Code
(numeros/headings) + Fira Sans (corpo), accent verde para indicadores
positivos / vermelho para negativos. Graficos via Chart.js (CDN), evitando
pizza/donut (grade de acessibilidade C na base de charts da skill) em favor
de barras e linhas (grade AAA/AA).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KPI_DIR = ROOT / "output" / "kpis"
OUT_FILE = ROOT / "output" / "apresentacao.html"

# Paleta do design system persistido (design-system/analise-ecommerce-v2/MASTER.md)
COLOR_BG = "#020617"
COLOR_PRIMARY = "#0F172A"
COLOR_SECONDARY = "#1E293B"
COLOR_MUTED = "#1A1E2F"
COLOR_BORDER = "#334155"
COLOR_FG = "#F8FAFC"
COLOR_ACCENT = "#22C55E"
COLOR_DESTRUCTIVE = "#EF4444"
COLOR_INFO = "#38BDF8"
COLOR_VIOLET = "#A78BFA"
COLOR_AMBER = "#FBBF24"


def load_kpis():
    return {
        "vendas": json.loads((KPI_DIR / "vendas_geral.json").read_text(encoding="utf-8")),
        "produtos": json.loads((KPI_DIR / "produtos.json").read_text(encoding="utf-8")),
        "clientes": json.loads((KPI_DIR / "clientes.json").read_text(encoding="utf-8")),
        "competitividade": json.loads(
            (KPI_DIR / "competitividade.json").read_text(encoding="utf-8")
        ),
    }


def fmt_brl(valor: float) -> str:
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {texto}"


def fmt_num(valor) -> str:
    return f"{valor:,}".replace(",", ".")


def esc(texto) -> str:
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def diff_pill(diff_pct: float) -> str:
    pill_class = "pill-up" if diff_pct >= 0 else "pill-down"
    sign = "+" if diff_pct >= 0 else ""
    arrow = "&#9650;" if diff_pct >= 0 else "&#9660;"
    return f'<span class="pill {pill_class}"><span aria-hidden="true">{arrow}</span> {sign}{diff_pct:.1f}%</span>'


def build_html(k: dict) -> str:
    v = k["vendas"]
    p = k["produtos"]
    c = k["clientes"]
    comp = k["competitividade"]

    data_payload = json.dumps(k, ensure_ascii=False)

    mes_labels = [item["mes"] for item in v["receita_por_mes"]]
    receita_por_mes_max = max((item["receita"] for item in v["receita_por_mes"]), default=0)

    canal_cards = "\n".join(
        f"""<div class="mini-card">
              <span class="mini-label">{esc(item['canal'].replace('_', ' ').title())}</span>
              <span class="mini-value">{fmt_brl(item['receita'])}</span>
              <span class="mini-sub">{fmt_num(item['pedidos'])} pedidos &middot; ticket m&eacute;dio {fmt_brl(item['ticket_medio'])}</span>
            </div>"""
        for item in v["receita_por_canal"]
    )

    top_receita_rows = "\n".join(
        f'<tr><td>{i + 1}</td><td>{esc(item["produto"])}</td><td class="text-right num">{fmt_brl(item["receita"])}</td></tr>'
        for i, item in enumerate(p["top_10_receita"])
    )

    top_quantidade_rows = "\n".join(
        f'<tr><td>{i + 1}</td><td>{esc(item["produto"])}</td><td class="text-right num">{fmt_num(item["quantidade"])} un.</td></tr>'
        for i, item in enumerate(p["top_10_quantidade"])
    )

    top_clientes_rows = "\n".join(
        f'<tr><td>{i + 1}</td><td>{esc(item["cliente"])}</td><td class="text-right num">{fmt_brl(item["receita"])}</td></tr>'
        for i, item in enumerate(c["top_10_clientes"])
    )

    caros_rows = "\n".join(
        f'<tr><td>{esc(item["produto"])}</td><td class="text-right num">{fmt_brl(item["preco_atual"])}</td>'
        f'<td class="text-right num">{fmt_brl(item["preco_medio_concorrente"])}</td>'
        f'<td class="text-right">{diff_pill(item["diff_pct"])}</td></tr>'
        for item in comp["top_10_mais_caros_que_mercado"]
    )

    baratos_rows = "\n".join(
        f'<tr><td>{esc(item["produto"])}</td><td class="text-right num">{fmt_brl(item["preco_atual"])}</td>'
        f'<td class="text-right num">{fmt_brl(item["preco_medio_concorrente"])}</td>'
        f'<td class="text-right">{diff_pill(item["diff_pct"])}</td></tr>'
        for item in comp["top_10_mais_baratos_que_mercado"]
    )

    clientes_estado_rows = "\n".join(
        f'<tr><td>{esc(item["estado"])}</td><td class="text-right num">{fmt_num(item["clientes"])}</td></tr>'
        for item in c["clientes_por_estado"]
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Dashboard E-commerce &mdash; An&aacute;lise v2 (Supabase)</title>
<meta name="description" content="Painel executivo de KPIs de e-commerce computados via SQL no Supabase Postgres.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --color-primary: {COLOR_PRIMARY};
    --color-secondary: {COLOR_SECONDARY};
    --color-accent: {COLOR_ACCENT};
    --color-background: {COLOR_BG};
    --color-foreground: {COLOR_FG};
    --color-muted: {COLOR_MUTED};
    --color-border: {COLOR_BORDER};
    --color-destructive: {COLOR_DESTRUCTIVE};
    --color-info: {COLOR_INFO};
    --color-violet: {COLOR_VIOLET};
    --color-amber: {COLOR_AMBER};
    --space-xs: 0.25rem; --space-sm: 0.5rem; --space-md: 1rem;
    --space-lg: 1.5rem; --space-xl: 2rem; --space-2xl: 3rem; --space-3xl: 4rem;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.35);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.4);
    --shadow-lg: 0 10px 25px rgba(0,0,0,0.45);
    --radius: 12px;
    color-scheme: dark;
  }}

  * {{ box-sizing: border-box; }}

  html {{ scroll-behavior: smooth; }}

  @media (prefers-reduced-motion: reduce) {{
    html {{ scroll-behavior: auto; }}
    * {{ animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }}
  }}

  body {{
    margin: 0;
    background: var(--color-background);
    color: var(--color-foreground);
    font-family: 'Fira Sans', system-ui, -apple-system, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  h1, h2, h3, .num, .mini-value, .kpi-value {{
    font-family: 'Fira Code', 'Fira Sans', monospace;
  }}

  a:focus-visible, button:focus-visible, [tabindex]:focus-visible {{
    outline: 2px solid var(--color-accent);
    outline-offset: 2px;
  }}

  .skip-link {{
    position: absolute; left: -9999px; top: 0; z-index: 100;
    background: var(--color-accent); color: #001a09;
    padding: var(--space-sm) var(--space-md); border-radius: 0 0 8px 0;
    font-weight: 600;
  }}
  .skip-link:focus {{ left: 0; }}

  header.topbar {{
    position: sticky; top: 0; z-index: 20;
    display: flex; align-items: center; justify-content: space-between;
    gap: var(--space-md);
    padding: var(--space-md) var(--space-xl);
    background: rgba(2, 6, 23, 0.85);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--color-border);
    flex-wrap: wrap;
  }}

  .brand {{ display: flex; align-items: center; gap: var(--space-sm); }}
  .brand svg {{ flex-shrink: 0; }}
  .brand-title {{ font-weight: 600; font-size: 1.05rem; letter-spacing: 0.01em; }}
  .brand-sub {{ font-size: 0.75rem; color: #94A3B8; }}

  .source-badge {{
    display: inline-flex; align-items: center; gap: var(--space-xs);
    background: var(--color-muted); border: 1px solid var(--color-border);
    color: #A7F3D0; padding: 6px 12px; border-radius: 999px;
    font-size: 0.78rem; font-weight: 500;
  }}
  .source-badge .dot {{
    width: 8px; height: 8px; border-radius: 50%; background: var(--color-accent);
    box-shadow: 0 0 8px var(--color-accent);
  }}

  nav.tabs {{
    display: flex; gap: var(--space-xs); padding: 0 var(--space-xl);
    overflow-x: auto; border-bottom: 1px solid var(--color-border);
    background: var(--color-background);
    position: sticky; top: 61px; z-index: 19;
  }}
  nav.tabs a {{
    color: #94A3B8; text-decoration: none; font-size: 0.85rem; font-weight: 500;
    padding: var(--space-md) var(--space-sm); white-space: nowrap;
    border-bottom: 2px solid transparent; cursor: pointer;
    transition: color 200ms ease, border-color 200ms ease;
  }}
  nav.tabs a:hover, nav.tabs a:focus-visible {{ color: var(--color-foreground); }}
  nav.tabs a.active {{ color: var(--color-foreground); border-bottom-color: var(--color-accent); }}

  main {{ max-width: 1280px; margin: 0 auto; padding: var(--space-xl); }}

  section {{ margin-bottom: var(--space-3xl); scroll-margin-top: 130px; }}

  .section-head {{ margin-bottom: var(--space-lg); }}
  .section-head h2 {{ margin: 0 0 4px; font-size: 1.3rem; font-weight: 600; }}
  .section-head p {{ margin: 0; color: #94A3B8; font-size: 0.9rem; }}

  .kpi-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: var(--space-md);
  }}

  .card {{
    background: var(--color-primary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: var(--space-lg);
    box-shadow: var(--shadow-md);
    transition: transform 200ms ease, box-shadow 200ms ease, border-color 200ms ease;
  }}
  .card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-lg); border-color: #475569; }}

  .kpi-card {{ display: flex; flex-direction: column; gap: 6px; }}
  .kpi-icon {{
    width: 36px; height: 36px; border-radius: 9px; display: flex;
    align-items: center; justify-content: center; margin-bottom: var(--space-sm);
    background: var(--color-muted); color: var(--color-accent);
  }}
  .kpi-label {{ color: #94A3B8; font-size: 0.82rem; font-weight: 500; }}
  .kpi-value {{ font-size: 1.65rem; font-weight: 600; letter-spacing: -0.01em; }}
  .kpi-sub {{ font-size: 0.78rem; color: #64748B; }}

  .grid-2 {{ display: grid; grid-template-columns: 2fr 1fr; gap: var(--space-md); align-items: stretch; }}
  .grid-equal {{ display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); }}
  @media (max-width: 900px) {{ .grid-2, .grid-equal {{ grid-template-columns: 1fr; }} }}

  .chart-card h3, .table-card h3 {{
    margin: 0 0 var(--space-md); font-size: 0.95rem; font-weight: 600;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .chart-card .chart-wrap {{ position: relative; }}

  .mini-card-row {{ display: flex; flex-direction: column; gap: var(--space-md); height: 100%; }}
  .mini-card {{
    background: var(--color-secondary); border: 1px solid var(--color-border);
    border-radius: var(--radius); padding: var(--space-md); display: flex;
    flex-direction: column; gap: 4px; flex: 1;
  }}
  .mini-label {{ font-size: 0.78rem; color: #94A3B8; font-weight: 500; }}
  .mini-value {{ font-size: 1.25rem; font-weight: 600; }}
  .mini-sub {{ font-size: 0.75rem; color: #64748B; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  thead th {{
    text-align: left; color: #94A3B8; font-weight: 500; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.04em;
    padding: 8px 10px; border-bottom: 1px solid var(--color-border);
    position: sticky; top: 0; background: var(--color-primary);
  }}
  tbody td {{ padding: 9px 10px; border-bottom: 1px solid rgba(51, 65, 85, 0.5); }}
  tbody tr:hover {{ background: rgba(148, 163, 184, 0.06); }}
  tbody tr:last-child td {{ border-bottom: none; }}
  .text-right {{ text-align: right; }}
  .num {{ font-family: 'Fira Code', monospace; font-variant-numeric: tabular-nums; }}
  .table-scroll {{ max-height: 420px; overflow-y: auto; }}

  .pill {{
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
    font-family: 'Fira Code', monospace;
  }}
  .pill-up {{ background: rgba(239, 68, 68, 0.14); color: #FCA5A5; }}
  .pill-down {{ background: rgba(34, 197, 94, 0.14); color: #86EFAC; }}

  .legend-note {{ font-size: 0.75rem; color: #64748B; margin-top: var(--space-sm); }}

  footer {{
    border-top: 1px solid var(--color-border); padding: var(--space-xl);
    text-align: center; color: #64748B; font-size: 0.82rem;
  }}
  footer code {{ color: #94A3B8; }}

  ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: var(--color-border); border-radius: 999px; }}
</style>
</head>
<body>
<a class="skip-link" href="#conteudo">Pular para o conte&uacute;do</a>

<header class="topbar">
  <div class="brand">
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect width="24" height="24" rx="6" fill="{COLOR_ACCENT}" opacity="0.15"/>
      <path d="M4 17V9M9 17V5M14 17V11M19 17V7" stroke="{COLOR_ACCENT}" stroke-width="2" stroke-linecap="round"/>
    </svg>
    <div>
      <div class="brand-title">An&aacute;lise E-commerce &middot; v2</div>
      <div class="brand-sub">Painel executivo de KPIs</div>
    </div>
  </div>
  <span class="source-badge"><span class="dot" aria-hidden="true"></span> Fonte: Supabase Postgres &middot; KPIs via SQL</span>
</header>

<nav class="tabs" aria-label="Se&ccedil;&otilde;es do painel">
  <a href="#visao-geral">Vis&atilde;o Geral</a>
  <a href="#produtos">Produtos</a>
  <a href="#clientes">Clientes</a>
  <a href="#competitividade">Competitividade</a>
</nav>

<main id="conteudo">

  <section id="visao-geral">
    <div class="section-head">
      <h2>Vis&atilde;o Geral</h2>
      <p>Indicadores consolidados de vendas no per&iacute;odo analisado.</p>
    </div>

    <div class="kpi-grid" style="margin-bottom: var(--space-md);">
      <div class="card kpi-card">
        <div class="kpi-icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </div>
        <span class="kpi-label">Receita Total</span>
        <span class="kpi-value">{fmt_brl(v['receita_total'])}</span>
        <span class="kpi-sub">no per&iacute;odo dispon&iacute;vel</span>
      </div>
      <div class="card kpi-card">
        <div class="kpi-icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M3 3h2l2.4 12.4a2 2 0 002 1.6h7.2a2 2 0 002-1.6L20 8H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="20" r="1.4" fill="currentColor"/><circle cx="17" cy="20" r="1.4" fill="currentColor"/></svg>
        </div>
        <span class="kpi-label">Pedidos</span>
        <span class="kpi-value">{fmt_num(v['numero_pedidos'])}</span>
        <span class="kpi-sub">{fmt_num(v['quantidade_total_itens'])} itens vendidos</span>
      </div>
      <div class="card kpi-card">
        <div class="kpi-icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 19V5a1 1 0 011-1h8l7 7-7 7H5a1 1 0 01-1-1z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="14.5" cy="9.5" r="1.4" fill="currentColor"/></svg>
        </div>
        <span class="kpi-label">Ticket M&eacute;dio</span>
        <span class="kpi-value">{fmt_brl(v['ticket_medio'])}</span>
        <span class="kpi-sub">receita / pedido</span>
      </div>
      <div class="card kpi-card">
        <div class="kpi-icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m5-8.13a4 4 0 110 8 4 4 0 010-8zm7 4a3 3 0 100-6 3 3 0 000 6zm-14 0a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <span class="kpi-label">Ticket M&eacute;dio / Cliente</span>
        <span class="kpi-value">{fmt_brl(c['ticket_medio_por_cliente'])}</span>
        <span class="kpi-sub">receita acumulada por cliente</span>
      </div>
    </div>

    <div class="grid-2">
      <div class="card chart-card">
        <h3>Receita por m&ecirc;s</h3>
        <div class="chart-wrap" style="height:280px;">
          <canvas id="chartReceitaMes" role="img" aria-label="Gr&aacute;fico de linha da receita mensal ao longo do per&iacute;odo analisado"></canvas>
        </div>
      </div>
      <div class="mini-card-row">
        <div style="margin-bottom: -4px;"><span class="kpi-label">Receita por Canal</span></div>
        {canal_cards}
      </div>
    </div>
  </section>

  <section id="produtos">
    <div class="section-head">
      <h2>Produtos</h2>
      <p>Ranking de receita, volume e composi&ccedil;&atilde;o do portf&oacute;lio.</p>
    </div>

    <div class="grid-equal" style="margin-bottom: var(--space-md);">
      <div class="card chart-card">
        <h3>Receita por categoria</h3>
        <div class="chart-wrap" style="height:320px;">
          <canvas id="chartCategoria" role="img" aria-label="Gr&aacute;fico de barras horizontais da receita total por categoria de produto"></canvas>
        </div>
      </div>
      <div class="card chart-card">
        <h3>Receita por marca (top 10)</h3>
        <div class="chart-wrap" style="height:320px;">
          <canvas id="chartMarca" role="img" aria-label="Gr&aacute;fico de barras horizontais das 10 marcas com maior receita"></canvas>
        </div>
      </div>
    </div>

    <div class="grid-equal">
      <div class="card table-card">
        <h3>Top 10 produtos por receita</h3>
        <div class="table-scroll">
          <table>
            <thead><tr><th>#</th><th>Produto</th><th class="text-right">Receita</th></tr></thead>
            <tbody>{top_receita_rows}</tbody>
          </table>
        </div>
      </div>
      <div class="card table-card">
        <h3>Top 10 produtos por quantidade</h3>
        <div class="table-scroll">
          <table>
            <thead><tr><th>#</th><th>Produto</th><th class="text-right">Unidades</th></tr></thead>
            <tbody>{top_quantidade_rows}</tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <section id="clientes">
    <div class="section-head">
      <h2>Clientes</h2>
      <p>Distribui&ccedil;&atilde;o geogr&aacute;fica, aquisi&ccedil;&atilde;o e maiores contas.</p>
    </div>

    <div class="grid-2" style="margin-bottom: var(--space-md);">
      <div class="card chart-card">
        <h3>Receita por estado</h3>
        <div class="chart-wrap" style="height:460px;">
          <canvas id="chartEstado" role="img" aria-label="Gr&aacute;fico de barras horizontais da receita total por estado do cliente"></canvas>
        </div>
      </div>
      <div class="card table-card">
        <h3>Clientes cadastrados por estado</h3>
        <div class="table-scroll" style="max-height:460px;">
          <table>
            <thead><tr><th>Estado</th><th class="text-right">Clientes</th></tr></thead>
            <tbody>{clientes_estado_rows}</tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card chart-card">
        <h3>Novos cadastros por m&ecirc;s</h3>
        <div class="chart-wrap" style="height:280px;">
          <canvas id="chartNovosClientes" role="img" aria-label="Gr&aacute;fico de linha de novos clientes cadastrados por m&ecirc;s"></canvas>
        </div>
      </div>
      <div class="card table-card">
        <h3>Top 10 clientes por receita</h3>
        <div class="table-scroll" style="max-height:280px;">
          <table>
            <thead><tr><th>#</th><th>Cliente</th><th class="text-right">Receita</th></tr></thead>
            <tbody>{top_clientes_rows}</tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <section id="competitividade">
    <div class="section-head">
      <h2>Competitividade de Pre&ccedil;o</h2>
      <p>Compara&ccedil;&atilde;o do pre&ccedil;o atual contra a m&eacute;dia coletada dos concorrentes.</p>
    </div>

    <div class="kpi-grid" style="margin-bottom: var(--space-md);">
      <div class="card kpi-card">
        <span class="kpi-label">Produtos Analisados</span>
        <span class="kpi-value">{fmt_num(comp['produtos_analisados'])}</span>
        <span class="kpi-sub">com cota&ccedil;&atilde;o de concorrente</span>
      </div>
      <div class="card kpi-card">
        <span class="kpi-label">Mais Caros que o Mercado</span>
        <span class="kpi-value" style="color:#FCA5A5;">{fmt_num(comp['produtos_mais_caros_que_mercado'])}</span>
        <span class="kpi-sub">produtos acima da m&eacute;dia dos concorrentes</span>
      </div>
      <div class="card kpi-card">
        <span class="kpi-label">Mais Baratos que o Mercado</span>
        <span class="kpi-value" style="color:#86EFAC;">{fmt_num(comp['produtos_mais_baratos_que_mercado'])}</span>
        <span class="kpi-sub">produtos abaixo da m&eacute;dia dos concorrentes</span>
      </div>
      <div class="card kpi-card">
        <span class="kpi-label">No Pre&ccedil;o de Mercado</span>
        <span class="kpi-value">{fmt_num(comp['produtos_no_preco_de_mercado'])}</span>
        <span class="kpi-sub">diferen&ccedil;a igual a zero</span>
      </div>
    </div>

    <div class="card chart-card" style="margin-bottom: var(--space-md);">
      <h3>Diferen&ccedil;a m&eacute;dia de pre&ccedil;o por concorrente</h3>
      <p class="legend-note" style="margin-top:-6px; margin-bottom: var(--space-sm);">Positivo (vermelho) = nosso pre&ccedil;o acima do concorrente &middot; Negativo (verde) = nosso pre&ccedil;o abaixo</p>
      <div class="chart-wrap" style="height:220px;">
        <canvas id="chartConcorrente" role="img" aria-label="Gr&aacute;fico de barras horizontais da diferen&ccedil;a m&eacute;dia percentual de pre&ccedil;o por concorrente"></canvas>
      </div>
    </div>

    <div class="grid-equal">
      <div class="card table-card">
        <h3>Top 10 mais caros que o mercado</h3>
        <div class="table-scroll">
          <table>
            <thead><tr><th>Produto</th><th class="text-right">Nosso Pre&ccedil;o</th><th class="text-right">M&eacute;dia Concorrentes</th><th class="text-right">Diferen&ccedil;a</th></tr></thead>
            <tbody>{caros_rows}</tbody>
          </table>
        </div>
      </div>
      <div class="card table-card">
        <h3>Top 10 mais baratos que o mercado</h3>
        <div class="table-scroll">
          <table>
            <thead><tr><th>Produto</th><th class="text-right">Nosso Pre&ccedil;o</th><th class="text-right">M&eacute;dia Concorrentes</th><th class="text-right">Diferen&ccedil;a</th></tr></thead>
            <tbody>{baratos_rows}</tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

</main>

<footer>
  Gerado a partir dos KPIs agregados via SQL no Supabase (<code>v2_supabase/scripts/compute_kpis.py</code>) &middot;
  Dashboard renderizado localmente por <code>build_presentation.py</code>, sem chamadas ao banco nesta etapa.
</footer>

<script>
const DATA = {data_payload};

Chart.defaults.color = "#94A3B8";
Chart.defaults.font.family = "'Fira Sans', sans-serif";
Chart.defaults.borderColor = "rgba(148, 163, 184, 0.12)";

const fmtBRL = (v) => "R$ " + v.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});

const gridOpt = {{ color: "rgba(148, 163, 184, 0.10)" }};
const baseTooltip = {{
  backgroundColor: "{COLOR_SECONDARY}",
  borderColor: "{COLOR_BORDER}",
  borderWidth: 1,
  titleColor: "{COLOR_FG}",
  bodyColor: "{COLOR_FG}",
  padding: 10,
  cornerRadius: 8,
  displayColors: false,
}};

// Receita por mes (linha)
new Chart(document.getElementById('chartReceitaMes'), {{
  type: 'line',
  data: {{
    labels: DATA.vendas.receita_por_mes.map(d => d.mes),
    datasets: [{{
      label: 'Receita',
      data: DATA.vendas.receita_por_mes.map(d => d.receita),
      borderColor: '{COLOR_ACCENT}',
      backgroundColor: 'rgba(34, 197, 94, 0.15)',
      fill: true,
      tension: 0.35,
      pointRadius: 4,
      pointBackgroundColor: '{COLOR_ACCENT}',
      pointBorderColor: '{COLOR_BG}',
      pointBorderWidth: 2,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }}, tooltip: {{ ...baseTooltip, callbacks: {{ label: (ctx) => fmtBRL(ctx.parsed.y) }} }} }},
    scales: {{
      x: {{ grid: {{ display: false }} }},
      y: {{ grid: gridOpt, ticks: {{ callback: (v) => fmtBRL(v) }} }}
    }}
  }}
}});

// Novos clientes por mes (linha)
new Chart(document.getElementById('chartNovosClientes'), {{
  type: 'line',
  data: {{
    labels: DATA.clientes.novos_cadastros_por_mes.map(d => d.mes),
    datasets: [{{
      label: 'Novos clientes',
      data: DATA.clientes.novos_cadastros_por_mes.map(d => d.novos_clientes),
      borderColor: '{COLOR_INFO}',
      backgroundColor: 'rgba(56, 189, 248, 0.15)',
      fill: true, tension: 0.35, pointRadius: 3,
      pointBackgroundColor: '{COLOR_INFO}', pointBorderColor: '{COLOR_BG}', pointBorderWidth: 2,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }}, tooltip: baseTooltip }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 60, minRotation: 60, autoSkip: true, maxTicksLimit: 14 }} }},
      y: {{ grid: gridOpt, ticks: {{ precision: 0 }} }}
    }}
  }}
}});

function horizontalBar(canvasId, labels, values, color, currency) {{
  new Chart(document.getElementById(canvasId), {{
    type: 'bar',
    data: {{ labels, datasets: [{{ data: values, backgroundColor: color, borderRadius: 4, maxBarThickness: 22 }}] }},
    options: {{
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }}, tooltip: {{ ...baseTooltip, callbacks: {{ label: (ctx) => currency ? fmtBRL(ctx.parsed.x) : ctx.parsed.x.toLocaleString('pt-BR') }} }} }},
      scales: {{
        x: {{ grid: gridOpt, ticks: {{ callback: (v) => currency ? fmtBRL(v) : v }} }},
        y: {{ grid: {{ display: false }} }}
      }}
    }}
  }});
}}

horizontalBar('chartCategoria',
  DATA.produtos.receita_por_categoria.map(d => d.categoria),
  DATA.produtos.receita_por_categoria.map(d => d.receita),
  '{COLOR_ACCENT}', true);

horizontalBar('chartMarca',
  DATA.produtos.receita_por_marca.map(d => d.marca),
  DATA.produtos.receita_por_marca.map(d => d.receita),
  '{COLOR_VIOLET}', true);

horizontalBar('chartEstado',
  DATA.clientes.receita_por_estado.map(d => d.estado),
  DATA.clientes.receita_por_estado.map(d => d.receita),
  '{COLOR_AMBER}', true);

// Diferenca por concorrente: cor condicional (vermelho = mais caro, verde = mais barato)
const concorrentes = DATA.competitividade.breakdown_por_concorrente;
new Chart(document.getElementById('chartConcorrente'), {{
  type: 'bar',
  data: {{
    labels: concorrentes.map(d => d.concorrente),
    datasets: [{{
      data: concorrentes.map(d => d.diff_pct_medio),
      backgroundColor: concorrentes.map(d => d.diff_pct_medio >= 0 ? '{COLOR_DESTRUCTIVE}' : '{COLOR_ACCENT}'),
      borderRadius: 4, maxBarThickness: 26,
    }}]
  }},
  options: {{
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }}, tooltip: {{ ...baseTooltip, callbacks: {{ label: (ctx) => (ctx.parsed.x >= 0 ? '+' : '') + ctx.parsed.x.toFixed(1) + '%' }} }} }},
    scales: {{
      x: {{ grid: gridOpt, ticks: {{ callback: (v) => v + '%' }} }},
      y: {{ grid: {{ display: false }} }}
    }}
  }}
}});

// Realca a aba visivel na navegacao conforme o scroll
const sections = document.querySelectorAll('main section[id]');
const tabs = document.querySelectorAll('nav.tabs a');
const setActive = (id) => tabs.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + id));
if ('IntersectionObserver' in window) {{
  const obs = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{ if (entry.isIntersecting) setActive(entry.target.id); }});
  }}, {{ rootMargin: '-40% 0px -55% 0px' }});
  sections.forEach(s => obs.observe(s));
}}
</script>
</body>
</html>
"""


def main():
    kpis = load_kpis()
    html = build_html(kpis)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"gravado {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
