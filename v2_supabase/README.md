# Análise de Dados de E-commerce — Supabase (v2)

Mesmos dados de `../data/` que a v1, modelados como tabelas relacionais em um projeto Supabase (Postgres), no lugar do pipeline local em pandas.

Projeto Supabase: **AnaliseDadosClaude** (ref `vkgefrcdztxhifzzmtzn`).

## Estrutura do projeto

* `.env`: URL/keys do projeto e string de conexão com o banco (não versionado — ver `.gitignore`).
* `requirements.txt`: dependências Python (`pandas`, `psycopg2-binary`, `python-dotenv`).
* `scripts/load_data.py`: lê os 4 CSVs de `../data/`, limpa os dados, apaga (`TRUNCATE`) e recarrega as 4 tabelas do zero. Idempotente — pode ser rodado quantas vezes for preciso.

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
