"""
Etapa 2 do pipeline de analise: le apenas os JSONs pequenos gerados por
compute_kpis.py (output/kpis/) e monta a apresentacao final em HTML,
dark mode moderno/futurista, com graficos via Chart.js (CDN).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KPI_DIR = ROOT / "output" / "kpis"
OUT_FILE = ROOT / "output" / "apresentacao.html"


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


def build_html(k: dict) -> str:
    v = k["vendas"]
    p = k["produtos"]
    c = k["clientes"]
    comp = k["competitividade"]

    data_payload = json.dumps(k, ensure_ascii=False)

    top_produtos_rows = "\n".join(
        f'<tr><td>{i + 1}</td><td>{item["produto"]}</td><td class="text-right">{fmt_brl(item["receita"])}</td></tr>'
        for i, item in enumerate(p["top_10_receita"])
    )

    top_clientes_rows = "\n".join(
        f'<tr><td>{i + 1}</td><td>{item["cliente"]}</td><td class="text-right">{fmt_brl(item["receita"])}</td></tr>'
        for i, item in enumerate(c["top_10_clientes"])
    )

    def diff_pill(diff_pct: float) -> str:
        pill_class = "pill-up" if diff_pct >= 0 else "pill-down"
        sign = "+" if diff_pct >= 0 else ""
        return f'<span class="pill {pill_class}">{sign}{diff_pct:.1f}%</span>'

    caros_rows = "\n".join(
        f'<tr><td>{item["produto"]}</td><td class="text-right">{fmt_brl(item["preco_atual"])}</td>'
        f'<td class="text-right">{fmt_brl(item["preco_medio_concorrente"])}</td>'
        f'<td class="text-right">{diff_pill(item["diff_pct"])}</td></tr>'
        for item in comp["top_10_mais_caros_que_mercado"]
    )

    baratos_rows = "\n".join(
        f'<tr><td>{item["produto"]}</td><td class="text-right">{fmt_brl(item["preco_atual"])}</td>'
        f'<td class="text-right">{fmt_brl(item["preco_medio_concorrente"])}</td>'
        f'<td class="text-right">{diff_pill(item["diff_pct"])}</td></tr>'
        for item in comp["top_10_mais_baratos_que_mercado"]
    )

    canal_cards = "\n".join(
        f"""<div class="mini-card">
              <span class="mini-label">{item['canal'].replace('_', ' ').title()}</span>
              <span class="mini-value">{fmt_brl(item['receita'])}</span>
              <span class="mini-sub">{fmt_num(item['pedidos'])} pedidos · ticket médio {fmt_brl(item['ticket_medio'])}</span>
            </div>"""
        for item in v["receita_por_canal"]
    )

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análise de E-commerce — Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #05070f;
    --bg-alt: #0b0f1e;
    --panel: rgba(20, 26, 46, 0.65);
    --border: rgba(120, 150, 255, 0.14);
    --cyan: #24f2d8;
    --purple: #a06bff;
    --pink: #ff5fb8;
    --text: #eef1fb;
    --text-dim: #8b93b8;
    --up: #ff6b81;
    --down: #24f2d8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    background: radial-gradient(circle at 15% 0%, #16204a 0%, var(--bg) 45%),
                radial-gradient(circle at 85% 20%, #2a0f42 0%, transparent 40%),
                var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }}
  h1, h2, h3, .value {{ font-family: 'Space Grotesk', sans-serif; }}
  .glow {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(600px circle at 10% 10%, rgba(36,242,216,0.08), transparent 40%),
      radial-gradient(600px circle at 90% 30%, rgba(160,107,255,0.10), transparent 40%);
    z-index: 0;
  }}
  header.hero {{
    position: relative;
    z-index: 1;
    padding: 6rem 6vw 4rem;
    text-align: center;
  }}
  .eyebrow {{
    display: inline-block;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    font-size: 0.72rem;
    color: var(--cyan);
    border: 1px solid var(--border);
    padding: 0.4rem 1rem;
    border-radius: 999px;
    margin-bottom: 1.5rem;
    background: rgba(36,242,216,0.06);
  }}
  h1 {{
    font-size: clamp(2.2rem, 5vw, 4rem);
    font-weight: 700;
    line-height: 1.1;
    background: linear-gradient(120deg, #f4f6ff 20%, var(--cyan) 55%, var(--purple) 90%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 1rem;
  }}
  .hero p.sub {{
    color: var(--text-dim);
    max-width: 640px;
    margin: 0 auto;
    font-size: 1.05rem;
  }}
  .kpi-strip {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.2rem;
    max-width: 1100px;
    margin: 3rem auto 0;
  }}
  .kpi-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.6rem;
    backdrop-filter: blur(14px);
    text-align: left;
    transition: transform .25s ease, border-color .25s ease;
  }}
  .kpi-card:hover {{ transform: translateY(-4px); border-color: rgba(36,242,216,0.4); }}
  .kpi-card .label {{ color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }}
  .kpi-card .value {{ font-size: 1.9rem; font-weight: 700; margin-top: 0.4rem; color: var(--cyan); }}

  main {{ position: relative; z-index: 1; max-width: 1200px; margin: 0 auto; padding: 2rem 6vw 6rem; }}
  section {{ margin-top: 5rem; }}
  section .section-head {{ margin-bottom: 1.8rem; }}
  section .section-head .tag {{ color: var(--purple); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.2em; }}
  section h2 {{ font-size: 1.9rem; margin-top: 0.3rem; }}

  .grid-2 {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 1.5rem; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; }}
  @media (max-width: 900px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}

  .panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.6rem;
    backdrop-filter: blur(14px);
    display: flex;
    flex-direction: column;
  }}
  .panel h3 {{ font-size: 1rem; color: var(--text-dim); font-weight: 500; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.06em; }}
  .chart-box {{ position: relative; flex: 1; min-height: 280px; width: 100%; }}

  .mini-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }}
  .mini-label {{ color: var(--text-dim); font-size: 0.8rem; text-transform: uppercase; }}
  .mini-value {{ font-size: 1.4rem; font-weight: 700; color: var(--purple); font-family: 'Space Grotesk', sans-serif; }}
  .mini-sub {{ color: var(--text-dim); font-size: 0.8rem; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th, td {{ text-align: left; padding: 0.55rem 0.6rem; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--text-dim); font-weight: 500; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.06em; }}
  .text-right {{ text-align: right; }}
  td:last-child, th:last-child {{ text-align: right; }}

  .pill {{ display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px; font-weight: 600; font-size: 0.82rem; }}
  .pill-up {{ background: rgba(255,107,129,0.14); color: var(--up); }}
  .pill-down {{ background: rgba(36,242,216,0.14); color: var(--down); }}

  footer {{
    position: relative; z-index: 1;
    text-align: center;
    padding: 3rem 1rem 4rem;
    color: var(--text-dim);
    font-size: 0.85rem;
  }}
</style>
</head>
<body>
<div class="glow"></div>

<header class="hero">
  <span class="eyebrow">Relatório de performance</span>
  <h1>Análise Completa de E-commerce</h1>
  <p class="sub">Visão consolidada de vendas, produtos, clientes e competitividade de preço, calculada a partir dos dados brutos de operação.</p>
  <div class="kpi-strip">
    <div class="kpi-card"><div class="label">Receita total</div><div class="value">{fmt_brl(v['receita_total'])}</div></div>
    <div class="kpi-card"><div class="label">Pedidos</div><div class="value">{fmt_num(v['numero_pedidos'])}</div></div>
    <div class="kpi-card"><div class="label">Ticket médio</div><div class="value">{fmt_brl(v['ticket_medio'])}</div></div>
    <div class="kpi-card"><div class="label">Itens vendidos</div><div class="value">{fmt_num(v['quantidade_total_itens'])}</div></div>
  </div>
</header>

<main>

  <section id="vendas">
    <div class="section-head">
      <span class="tag">01 · Vendas gerais</span>
      <h2>Evolução da receita</h2>
    </div>
    <div class="grid-2">
      <div class="panel">
        <h3>Receita por mês</h3>
        <div class="chart-box"><canvas id="chartReceitaMes"></canvas></div>
      </div>
      <div class="panel" style="display:flex; flex-direction:column; gap:1rem; justify-content:center;">
        <h3>Receita por canal</h3>
        {canal_cards}
      </div>
    </div>
  </section>

  <section id="produtos">
    <div class="section-head">
      <span class="tag">02 · Produtos</span>
      <h2>O que mais vende</h2>
    </div>
    <div class="grid-2">
      <div class="panel">
        <h3>Top 10 produtos por receita</h3>
        <table>
          <thead><tr><th>#</th><th>Produto</th><th>Receita</th></tr></thead>
          <tbody>{top_produtos_rows}</tbody>
        </table>
      </div>
      <div class="panel">
        <h3>Receita por categoria</h3>
        <div class="chart-box"><canvas id="chartCategoria"></canvas></div>
      </div>
    </div>
    <div class="grid-2" style="margin-top:1.2rem;">
      <div class="panel">
        <h3>Receita por marca (top 10)</h3>
        <div class="chart-box"><canvas id="chartMarca"></canvas></div>
      </div>
      <div class="panel">
        <h3>Preço médio por categoria</h3>
        <div class="chart-box"><canvas id="chartPrecoCategoria"></canvas></div>
      </div>
    </div>
  </section>

  <section id="clientes">
    <div class="section-head">
      <span class="tag">03 · Clientes</span>
      <h2>Quem compra</h2>
    </div>
    <div class="grid-2">
      <div class="panel">
        <h3>Receita por estado</h3>
        <div class="chart-box"><canvas id="chartEstado"></canvas></div>
      </div>
      <div class="panel">
        <h3>Novos cadastros por mês</h3>
        <div class="chart-box"><canvas id="chartCadastros"></canvas></div>
      </div>
    </div>
    <div class="panel" style="margin-top:1.2rem;">
      <h3>Top 10 clientes por receita &nbsp;·&nbsp; ticket médio por cliente: {fmt_brl(c['ticket_medio_por_cliente'])}</h3>
      <table>
        <thead><tr><th>#</th><th>Cliente</th><th>Receita</th></tr></thead>
        <tbody>{top_clientes_rows}</tbody>
      </table>
    </div>
  </section>

  <section id="competitividade">
    <div class="section-head">
      <span class="tag">04 · Competitividade de preço</span>
      <h2>Nosso preço vs. o mercado</h2>
    </div>
    <div class="grid-3">
      <div class="mini-card"><span class="mini-label">Produtos analisados</span><span class="mini-value">{fmt_num(comp['produtos_analisados'])}</span></div>
      <div class="mini-card"><span class="mini-label">Acima do mercado</span><span class="mini-value" style="color:var(--up)">{fmt_num(comp['produtos_mais_caros_que_mercado'])}</span></div>
      <div class="mini-card"><span class="mini-label">Abaixo do mercado</span><span class="mini-value" style="color:var(--down)">{fmt_num(comp['produtos_mais_baratos_que_mercado'])}</span></div>
    </div>
    <div class="grid-2" style="margin-top:1.2rem;">
      <div class="panel">
        <h3>Diferença média de preço por concorrente</h3>
        <div class="chart-box"><canvas id="chartConcorrentes"></canvas></div>
      </div>
      <div class="panel">
        <h3>Top 10 mais caros que o mercado</h3>
        <table>
          <thead><tr><th>Produto</th><th class="text-right">Nosso preço</th><th class="text-right">Média mercado</th><th class="text-right">Diferença</th></tr></thead>
          <tbody>{caros_rows}</tbody>
        </table>
      </div>
    </div>
    <div class="panel" style="margin-top:1.2rem;">
      <h3>Top 10 mais baratos que o mercado</h3>
      <table>
        <thead><tr><th>Produto</th><th class="text-right">Nosso preço</th><th class="text-right">Média mercado</th><th class="text-right">Diferença</th></tr></thead>
        <tbody>{baratos_rows}</tbody>
      </table>
    </div>
  </section>

</main>

<footer>Gerado automaticamente a partir de data/*.csv via scripts/compute_kpis.py + scripts/build_presentation.py</footer>

<script>
const KPI = {data_payload};

Chart.defaults.color = "#8b93b8";
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.borderColor = "rgba(120,150,255,0.12)";

const gridStyle = {{ color: "rgba(120,150,255,0.08)" }};
const neon = ["#24f2d8", "#a06bff", "#ff5fb8", "#ffd166", "#6ea8ff"];

function gradient(ctx, area, c1, c2) {{
  const g = ctx.createLinearGradient(0, area.top, 0, area.bottom);
  g.addColorStop(0, c1);
  g.addColorStop(1, c2);
  return g;
}}

new Chart(document.getElementById('chartReceitaMes'), {{
  type: 'line',
  data: {{
    labels: KPI.vendas.receita_por_mes.map(d => d.mes),
    datasets: [{{
      label: 'Receita',
      data: KPI.vendas.receita_por_mes.map(d => d.receita),
      borderColor: '#24f2d8',
      backgroundColor: 'rgba(36,242,216,0.15)',
      fill: true, tension: 0.35, pointRadius: 4, pointBackgroundColor: '#24f2d8'
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});

new Chart(document.getElementById('chartCategoria'), {{
  type: 'bar',
  data: {{
    labels: KPI.produtos.receita_por_categoria.map(d => d.categoria),
    datasets: [{{ label: 'Receita', data: KPI.produtos.receita_por_categoria.map(d => d.receita), backgroundColor: '#a06bff', borderRadius: 6 }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});

new Chart(document.getElementById('chartMarca'), {{
  type: 'bar',
  data: {{
    labels: KPI.produtos.receita_por_marca.map(d => d.marca),
    datasets: [{{ label: 'Receita', data: KPI.produtos.receita_por_marca.map(d => d.receita), backgroundColor: '#ff5fb8', borderRadius: 6 }}]
  }},
  options: {{ indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});

new Chart(document.getElementById('chartPrecoCategoria'), {{
  type: 'bar',
  data: {{
    labels: KPI.produtos.preco_medio_por_categoria.map(d => d.categoria),
    datasets: [{{ label: 'Preço médio', data: KPI.produtos.preco_medio_por_categoria.map(d => d.preco_medio), backgroundColor: '#ffd166', borderRadius: 6 }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});

new Chart(document.getElementById('chartEstado'), {{
  type: 'bar',
  data: {{
    labels: KPI.clientes.receita_por_estado.map(d => d.estado),
    datasets: [{{ label: 'Receita', data: KPI.clientes.receita_por_estado.map(d => d.receita), backgroundColor: '#24f2d8', borderRadius: 6 }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});

new Chart(document.getElementById('chartCadastros'), {{
  type: 'line',
  data: {{
    labels: KPI.clientes.novos_cadastros_por_mes.map(d => d.mes),
    datasets: [{{
      label: 'Novos clientes', data: KPI.clientes.novos_cadastros_por_mes.map(d => d.novos_clientes),
      borderColor: '#a06bff', backgroundColor: 'rgba(160,107,255,0.15)', fill: true, tension: 0.35, pointRadius: 3
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});

new Chart(document.getElementById('chartConcorrentes'), {{
  type: 'bar',
  data: {{
    labels: KPI.competitividade.breakdown_por_concorrente.map(d => d.concorrente),
    datasets: [{{
      label: 'Diferença média (%)',
      data: KPI.competitividade.breakdown_por_concorrente.map(d => d.diff_pct_medio),
      backgroundColor: KPI.competitividade.breakdown_por_concorrente.map(d => d.diff_pct_medio >= 0 ? '#ff6b81' : '#24f2d8'),
      borderRadius: 6
    }}]
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: gridStyle }}, y: {{ grid: gridStyle }} }} }}
}});
</script>
</body>
</html>
"""


def main():
    k = load_kpis()
    html = build_html(k)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"gravado {OUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
