# PRD - Agente de Dados com Bot Telegram


## Contexto


Sistema completo de inteligência de dados para e-commerce via Telegram com 3 capacidades:


1. **Chat livre** — responde qualquer pergunta sobre o e-commerce consultando o banco em tempo real via tool use (Claude executa SQL dinamicamente).
2. **Relatório executivo** — gera relatório para 3 diretores (Comercial, CS, Pricing) com insights acionáveis a partir dos Data Marts gold.
3. **Envio automático** — quando é digitado /relatorio


**Banco:** PostgreSQL (Supabase)
**LLM:** Claude (Anthropic API) com tool use para execução de SQL
**Bot:** python-telegram-bot v20+ (https://github.com/python-telegram-bot/python-telegram-bot)
**Referência técnica:** Ler o arquivo `PROJETO_REFERENCIA` para schemas completos, colunas, tipos e regras de negócio.


Crie um comando pré pronto, /relatorio para responder 3 kpis indicados no documento PROJETO_REFERENCIA.md


Utilize o  PROJETO_REFERENCIA.md para desenvolver esse projeto.


Ele será todo em python, e deve rodar com somente um arquivo, app.py


Atualize no .env as variaveis que preciso passar ex: Claude e tb telegrambot
