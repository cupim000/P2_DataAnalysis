# Análise de Dados de E-commerce — Supabase (v2)

Mesmos dados de `../data/` que a v1, modelados como tabelas relacionais em um projeto Supabase (Postgres). Os KPIs são calculados como agregações SQL direto no Postgres (não em pandas), e o dashboard final é renderizado a partir desses KPIs já pequenos — mesma filosofia de contexto enxuto da v1, com o cálculo empurrado para o banco em vez do pandas.

Projeto Supabase: **AnaliseDadosClaude** (ref `vkgefrcdztxhifzzmtzn`).

## Estrutura do projeto

* `.env`: URL/keys do projeto e string de conexão com o banco (não versionado — ver `.gitignore`).
* `requirements.txt`: dependências Python (`pandas`, `psycopg2-binary`, `python-dotenv`).
* `scripts/load_data.py`: lê os 4 CSVs de `../data/`, limpa os dados, apaga (`TRUNCATE`) e recarrega as 4 tabelas do zero. Idempotente — pode ser rodado quantas vezes for preciso.
* `scripts/compute_kpis.py`: conecta no Postgres (`DATABASE_URL`) e roda os KPIs como `GROUP BY`/joins em SQL — só o resultado agregado volta para Python. Grava JSONs pequenos em `output/kpis/*.json` (mesmo formato usado pela v1).
* `scripts/build_presentation.py`: lê **apenas** esses JSONs (nunca reabre a conexão com o banco) e renderiza `output/apresentacao.html`, um dashboard dark mode com Chart.js (CDN), seguindo o design system gerado pela skill `ui-ux-pro-max` e persistido em `design-system/analise-ecommerce-v2/`.
* `run_pipeline.py`: roda as duas etapas acima em sequência.

## Dashboard

```bash
pip install -r requirements.txt
python run_pipeline.py
```

Abre `output/apresentacao.html` — 4 seções (Visão Geral, Produtos, Clientes, Competitividade), KPIs em cards, gráficos de linha (tendência) e barra horizontal (rankings/comparações). Doughnut/pizza foi evitado de propósito: a base de regras da skill `ui-ux-pro-max` classifica esse tipo de gráfico com nota de acessibilidade C (depende só de cor para distinguir fatias); barra horizontal e linha têm nota AA/AAA.

### Nota sobre `numero_pedidos`

O dashboard v2 mostra **3000 pedidos** (a v1 mostra 3020) porque `vendas.id_produto` tem FK para `produtos` no Postgres — as 20 linhas com `id_produto` inexistente (dado sujo na fonte) são descartadas no load em vez de virarem `NaN` como no `merge(how="left")` da v1. Ver seção abaixo.

## Schema

Quatro tabelas no schema `public`, com RLS habilitado e **sem policies** (só a conexão direta ao Postgres — via `DATABASE_URL`/service role — lê e escreve; `anon`/`authenticated` não têm acesso via API):

* **`clientes`** (`id_cliente` PK) — `nome_cliente, estado, pais, data_cadastro`
* **`produtos`** (`id_produto` PK) — `nome_produto, categoria, marca, preco_atual, data_criacao`
* **`vendas`** (`id_venda` PK) — `data_venda, id_cliente → clientes, id_produto → produtos, canal_venda, quantidade, preco_unitario`
* **`competidores`** (`id` PK serial) — `id_produto → produtos, nome_concorrente, preco_concorrente, data_coleta`

## Quirk de dados: vendas órfãs

20 linhas de `Dadosdoecommerce_vendas.csv` referenciam um `id_produto` que não existe em `Dadosdoecommerce_produtos.csv` (dado sujo na fonte). A v1 não detecta isso porque usa `merge(how="left")` (o produto vira `NaN`); aqui, como `vendas.id_produto` tem FK para `produtos`, essas linhas são descartadas e reportadas no console antes do insert — `vendas` fica com 3000 linhas em vez de 3020.

## Como rodar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Preencha `DATABASE_URL` em `.env` com a **connection string do pooler** (Session ou Transaction pooler — o host direto `db.<ref>.supabase.co` é IPv6-only e não resolve na maioria das redes). Copie em [Database Settings → Connection string](https://supabase.com/dashboard/project/vkgefrcdztxhifzzmtzn/settings/database).
3. Rode o script (a partir de `v2_supabase/`):
   ```bash
   python scripts/load_data.py
   ```

O script trunca as 4 tabelas (respeitando a ordem das FKs) e reinsere tudo a partir dos CSVs atuais em `../data/`.
