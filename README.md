📈 Analisador de Portfólio de Investimentos

Este é um sistema em Python para análise de portfólio de investimentos, construído com uma arquitetura modular e focado em fornecer insights práticos para o rebalanceamento de carteira com base na estratégia de **Paridade de Risco (Risk Parity)**.

O sistema permite ao usuário importar suas transações, buscar dados históricos de mercado e gerar relatórios detalhados sobre a alocação atual e sugestões de rebalanceamento.

## ✨ Funcionalidades Principais

* **Gerenciamento de Transações:** Importação de transações de compra e venda a partir de um arquivo CSV, com detecção inteligente para evitar duplicatas.
* **Coleta de Dados Históricos:** Busca automática de cotações dos últimos 2 anos para todos os ativos da carteira e para índices de referência (Ibovespa, IFIX), utilizando a API do Yahoo Finance. A coleta é inteligente e baixa apenas os dados novos em execuções subsequentes.
* **Análise de Posição Atual:** Cálculo do valor de mercado atual de cada ativo, preço médio, custo total e percentual de alocação na carteira e por classe de ativo.
* **Motor de Risk Parity:** Cálculo da volatilidade anualizada de cada ativo e geração de uma alocação sugerida onde cada ativo contribui igualmente para o risco da sua classe.
* **Plano de Rebalanceamento:** Geração de um relatório com recomendações de **Compra**, **Venda** ou **Neutro** para cada ativo, com valores monetários e quantidade de cotas/ações para atingir as faixas de tolerância do modelo.
* **Plano de Aporte:** Ferramenta interativa para simular a alocação de um novo aporte em dinheiro, sugerindo as compras mais eficientes para corrigir os desequilíbrios da carteira.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11+
* **Banco de Dados:** SQLite
* **Acesso a Dados:** SQLAlchemy (para o ORM) e `db-nexus` (nossa biblioteca core modular).
* **Análise e Coleta de Dados:** Pandas e yfinance.

## 📂 Estrutura do Projeto

```
portfolio_analyzer/
├── app/                  # Contém o código fonte da aplicação (a "biblioteca")
│   ├── __init__.py
│   ├── models.py         # Definições das tabelas do banco e Enums
│   ├── repositories.py   # Camada de acesso direto aos dados
│   ├── services.py       # Camada de lógica de negócio e análises
│   └── view.py           # Funções de exibição de relatórios
├── data/                 # Contém os dados gerados
│   ├── portfolio.db      # O arquivo do banco de dados SQLite
│   └── transacoes.csv    # O arquivo com o histórico de transações
├── .venv/                # Pasta do ambiente virtual Python
├── main.py               # Script principal para visualizar a carteira
├── importar_csv.py       # Ferramenta para importar transações do CSV
├── coletar_historico.py  # Ferramenta para buscar cotações online
├── recomendar_aporte.py  # Ferramenta para planejar novos aportes
├── recomendar_rebalanceamento.py  # Ferramenta para gerar o plano de rebalanceamento
└── README.md             # Este arquivo
```

## ⚙️ Instalação e Configuração

**1. Crie o Ambiente Virtual:**
   Se ainda não o fez, crie e ative um ambiente virtual para isolar as dependências do projeto.
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

**2. Crie o Arquivo `requirements.txt`:**
   Este arquivo lista todas as dependências do projeto. Para gerá-lo automaticamente a partir do que já instalamos, rode:
   ```bash
   pip freeze > requirements.txt
   ```

**3. Instale as Dependências:**
   Se você fosse clonar este projeto em uma nova máquina, o comando para instalar tudo de uma vez seria:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Uso (Fluxo de Trabalho)

O uso da ferramenta é dividido em tarefas de manutenção de dados e tarefas de análise.

### 1. Alimentar e Atualizar os Dados

**a. Registre suas Transações:**
   Abra o arquivo `data/transacoes.csv` e adicione todas as suas operações de compra e venda, seguindo o formato das colunas: `ticker,nome,tipo,data,operacao,quantidade,preco`.
   Use `#` no início de uma linha para comentá-la ou desativá-la temporariamente.

**b. Importe as Transações para o Banco:**
   Este comando lê o arquivo CSV e salva as novas transações no banco de dados. Ele é seguro para ser executado várias vezes, pois ignora transações que já foram importadas.
   ```bash
   python3 importar_csv.py
   ```

**c. Colete as Cotações Históricas:**
   Este comando busca no Yahoo Finance as cotações mais recentes para todos os seus ativos. É rápido, pois só baixa os dados que estão faltando.
   ```bash
   python3 coletar_historico.py
   ```

### 2. Analisar e Planejar

Após seus dados estarem atualizados, você pode usar os scripts de análise:

**a. Para um novo aporte em dinheiro:**
   Use esta ferramenta para saber onde alocar seu novo capital da forma mais eficiente.
   ```bash
   python3 recomendar_aporte.py
   ```
   O programa irá perguntar o valor do aporte.

**b. Para um rebalanceamento completo:**
   Use esta ferramenta para obter o plano de ação completo, com sugestões de compra e venda para alinhar sua carteira à estratégia de Paridade de Risco.
   ```bash
   python3 recomendar_rebalanceamento.py
   ```

**c. Para uma visão geral da sua carteira:**
   Use o `main.py` para uma visualização rápida e limpa da sua posição atual.
   ```bash
   python3 main.py
   ```

## 🔮 Próximos Passos Possíveis

* Criar uma interface web com **Flask** ou **FastAPI** para visualizar os relatórios no navegador.
* Adicionar gráficos e visualizações de dados com bibliotecas como **Matplotlib** ou **Plotly**.
* Implementar outros modelos de alocação de carteira (ex: Markowitz, Black-Litterman).
* Automatizar a coleta de dados para rodar periodicamente.

---