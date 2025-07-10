# importar_csv.py (Versão com Suporte a Comentários)

import csv
import datetime
import os
from sqlalchemy import create_engine
from app.models import Base, setup_inicial_se_necessario, TipoAtivo, TipoOperacao
from db_nexus import DatabaseSessionManager
from app.services import PortfolioService
from app.view import exibir_portfolio

def find_enum_by_value(enum_class, value_to_find: str):
    value_to_find_clean = value_to_find.strip().lower()
    for member in enum_class:
        if member.value.lower() == value_to_find_clean:
            return member
    return None

def importar_de_csv(service: PortfolioService, caminho_arquivo: str):
    print(f"\nIniciando importação do arquivo '{caminho_arquivo}'...")
    try:
        with open(caminho_arquivo, mode='r', encoding='utf-8') as arquivo_csv:
            
            # --- A MUDANÇA ESTÁ AQUI ---
            # Criamos um "filtro" que lê o arquivo e ignora linhas que começam
            # com '#' ou que estão completamente em branco.
            linhas_filtradas = (linha for linha in arquivo_csv if not linha.strip().startswith('#'))
            
            # O DictReader agora lê a partir das linhas já filtradas, em vez do arquivo direto
            leitor = csv.DictReader(linhas_filtradas)
            
            importadas = 0
            puladas = 0
            
            for linha in leitor:
                try:
                    # O resto do código continua igual...
                    ticker = linha['ticker'].upper()
                    nome = linha['nome']
                    tipo_ativo = find_enum_by_value(TipoAtivo, linha['tipo'])
                    data = datetime.date.fromisoformat(linha['data'])
                    tipo_operacao = find_enum_by_value(TipoOperacao, linha['operacao'])
                    quantidade = float(linha['quantidade'])
                    preco = float(linha['preco'])

                    resultado = service.importar_transacao_se_nova(
                        ticker, nome, tipo_ativo, data, tipo_operacao, quantidade, preco
                    )
                    
                    if resultado['status'] == 'imported':
                        importadas += 1
                    elif resultado['status'] == 'skipped':
                        puladas += 1

                except Exception as e:
                    print(f"⚠️ Erro ao processar a linha: {linha}. Erro: {e}")
            
            print("\n--- Resumo da Importação ---")
            print(f"✅ {importadas} novas transações importadas.")
            print(f"⏩ {puladas} transações existentes foram puladas.")

    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{caminho_arquivo}' não encontrado.")
    except Exception as e:
        print(f"❌ Ocorreu um erro durante a importação: {e}")

if __name__ == "__main__":
    setup_inicial_se_necessario()

    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    ARQUIVO_CSV = "data/transacoes.csv"
    importar_de_csv(service, ARQUIVO_CSV)
    
    print("\n--- Carteira após a operação ---")
    exibir_portfolio(service)