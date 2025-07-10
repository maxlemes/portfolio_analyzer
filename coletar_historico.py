# coletar_historico.py

import datetime
import yfinance as yf
from db_nexus import DatabaseSessionManager
from app.services import PortfolioService

def coletar_e_salvar_historico(service: PortfolioService):
    """
    Busca os tickers no banco, coleta o histórico de 2 anos para cada um
    e salva no banco de dados.
    """
    print("Iniciando coleta de dados históricos...")

    # 1. Calcula o intervalo de datas: de hoje até 2 anos atrás
    data_final = datetime.date.today()
    data_inicial = data_final - datetime.timedelta(days=2*365)
    
    # Formata as datas para o formato que a API yfinance espera (AAAA-MM-DD)
    data_inicial_str = data_inicial.strftime('%Y-%m-%d')
    data_final_str = data_final.strftime('%Y-%m-%d')

    print(f"Buscando dados no intervalo de {data_inicial_str} a {data_final_str}.")

    # 2. Busca todos os tickers do nosso banco de dados
    tickers = service.get_all_asset_tickers()
    # Vamos também adicionar os índices que queremos acompanhar
    tickers_para_buscar = tickers + ['^BVSP', 'XFIX11.SA']
    
    print(f"Ativos e Índices a serem atualizados: {tickers_para_buscar}")

    dados_para_importar = []

    # 3. Para cada ticker, busca os dados na API
    for ticker in tickers_para_buscar:
        # Para ativos brasileiros na B3, o Yahoo Finance geralmente requer o sufixo ".SA"
        # O ticker do Ibovespa é uma exceção: '^BVSP'
        ticker_api = ticker
        if not ticker.endswith(".SA") and ticker != '^BVSP':
            ticker_api = f"{ticker}.SA"

        try:
            print(f"  - Coletando dados para {ticker} (usando {ticker_api})...")
            
            # Baixa os dados usando yfinance
            dados = yf.download(ticker_api, start=data_inicial_str, end=data_final_str, progress=False)
            
            if dados.empty:
                print(f"    ⚠️ Nenhum dado retornado para {ticker_api}.")
                continue

            # 4. Formata os dados para o nosso serviço de importação
            for data_cotacao, linha in dados.iterrows():
                dados_para_importar.append({
                    'ticker': ticker, # Salva o ticker original (ex: 'CXSE3')
                    'data': data_cotacao.strftime('%Y-%m-%d'),
                    'preco_fechamento': linha['Close']
                })
        
        except Exception as e:
            print(f"    ❌ Erro ao coletar dados para {ticker_api}: {e}")

    # 5. Salva todos os dados coletados no banco de uma só vez
    if dados_para_importar:
        print(f"\nTotal de {len(dados_para_importar)} registros de cotações para salvar...")
        # Reutilizamos o mesmo método de importação que criamos para o CSV!
        service.importar_dados_historicos(dados_para_importar)
    else:
        print("\nNenhum dado novo para importar.")


if __name__ == "__main__":
    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    coletar_e_salvar_historico(service)