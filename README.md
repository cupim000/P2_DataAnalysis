# Análise de Dados de E-commerce — Pipeline & Dashboard

Pipeline automatizado em Python para análise de dados de e-commerce (vendas, produtos, clientes e competitividade de preço), gerando um dashboard executivo interativo em HTML/Chart.js.

---

## 🚀 Como Atualizar a Apresentação com Novos Dados

O projeto é 100% dinâmico. Sempre que você atualizar as bases de dados na pasta `data/`, siga os passos abaixo para recarregar o dashboard:

1. **Substitua os arquivos CSV** na pasta `data/`:
   * `Dadosdoecommerce_vendas.csv`
   * `Dadosdoecommerce_produtos.csv`
   * `Dadosdoecommerce_clientes.csv`
   * `Dadosdoecommercepreco_competidores.csv`

2. **Execute o pipeline de atualização**:
   ```bash
   python run_pipeline.py
   ```

3. **Visualizar o resultado**:
   Abra o arquivo `output/apresentacao.html` em qualquer navegador. Todos os KPIs, gráficos e tabelas estarão 100% atualizados.

---

## 🛠️ Estrutura do Projeto

* `data/`: Arquivos CSV com os dados brutos de entrada.
* `scripts/compute_kpis.py`: Etapa 1 — Processa, limpa os dados e salva os resumos em `output/kpis/*.json`.
* `scripts/build_presentation.py`: Etapa 2 — Constrói o dashboard HTML em `output/apresentacao.html`.
* `run_pipeline.py`: Script principal que executa as Etapas 1 e 2 em sequência.
* `output/apresentacao.html`: Dashboard interativo final em Dark Mode.

---

## ⚙️ Pré-requisitos e Instalação

* Python 3.10+
* Bibliotecas necessárias:
  ```bash
  pip install -r requirements.txt
  ```
