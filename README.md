# Análise de Dados de E-commerce

Análise dos dados de e-commerce em `data/` (vendas, produtos, clientes e competitividade de preço), com duas implementações independentes do mesmo projeto:

* **`v1_local/`** — pipeline 100% local em Python/pandas: lê os CSVs, calcula os KPIs e gera um dashboard HTML estático (Chart.js), sem depender de nenhum serviço externo. Ver [`v1_local/README.md`](v1_local/README.md).
* **`v2_supabase/`** — mesmos dados, modelados como tabelas relacionais (`clientes`, `produtos`, `vendas`, `competidores`) em um projeto Supabase (Postgres). Um script carrega/recarrega as tabelas, os KPIs são calculados como agregações SQL direto no Postgres (em vez de pandas), e o mesmo tipo de dashboard HTML/Chart.js é renderizado a partir desses KPIs — com um design system dark mode gerado pela skill `ui-ux-pro-max`. Ver [`v2_supabase/README.md`](v2_supabase/README.md).

## Estrutura do projeto

* `data/`: arquivos CSV com os dados brutos de entrada, compartilhados pelas duas versões — nunca duplicar ou mover.
* `v1_local/`: pipeline local (Python + Chart.js).
* `v2_supabase/`: tabelas no Supabase, KPIs via SQL e dashboard Chart.js.

Cada versão é autocontida: scripts de uma não leem nem escrevem na pasta da outra.

## Próximos passos (planejados, não iniciados)

* Um terceiro componente — bot de Telegram com Claude (tool use SQL) sobre o mesmo banco Supabase — está descrito em `.llm/prd_bot.md`, mas ainda não foi implementado (depende de uma API paga do Claude).
