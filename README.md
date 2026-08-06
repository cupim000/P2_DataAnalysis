# Análise de Dados de E-commerce

Análise dos dados de e-commerce em `data/` (vendas, produtos, clientes e competitividade de preço), com duas implementações independentes do mesmo projeto:

* **`v1_local/`** — pipeline 100% local em Python/pandas: lê os CSVs, calcula os KPIs e gera um dashboard HTML estático (Chart.js), sem depender de nenhum serviço externo. Ver [`v1_local/README.md`](v1_local/README.md).
* **`v2_supabase/`** — mesmos dados, modelados como tabelas relacionais (`clientes`, `produtos`, `vendas`, `competidores`) em um projeto Supabase (Postgres), com um script Python para carregar/recarregar os dados. Ver [`v2_supabase/README.md`](v2_supabase/README.md).

## Estrutura do projeto

* `data/`: arquivos CSV com os dados brutos de entrada, compartilhados pelas duas versões — nunca duplicar ou mover.
* `v1_local/`: pipeline local (Python + Chart.js).
* `v2_supabase/`: tabelas no Supabase + script de carga em Python.

Cada versão é autocontida: scripts de uma não leem nem escrevem na pasta da outra.
