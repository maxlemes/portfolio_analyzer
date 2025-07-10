# analisar_distribuicao.py (Versão com Tabelas Separadas e Dupla Alocação)

from collections import defaultdict
from db_nexus import DatabaseSessionManager
from app.services import PortfolioService

def exibir_analise_completa(service: PortfolioService):
    """
    Busca os dados de mercado e exibe a análise completa com:
    1. Tabela de resumo por classe.
    2. Tabelas de detalhamento separadas para cada classe.
    """
    print("\n--- Análise de Distribuição por Valor de Mercado Atual ---")

    # 1. Busca os dados e faz os cálculos iniciais
    portfolio = service.get_market_value_portfolio()

    if not portfolio:
        print("Não foi possível calcular a distribuição. A carteira está vazia ou sem cotações.")
        return

    # Dicionários para pré-calcular os valores totais
    subtotais_por_classe = defaultdict(float)
    posicoes_agrupadas = defaultdict(list)
    valor_total_mercado = 0

    for ativo in portfolio:
        subtotais_por_classe[ativo['tipo_ativo'].value] += ativo['valor_mercado']
        posicoes_agrupadas[ativo['tipo_ativo'].value].append(ativo)
        valor_total_mercado += ativo['valor_mercado']
    
    if valor_total_mercado == 0:
        print("Não foi possível calcular a alocação, pois o valor de mercado total é zero.")
        return

    # 2. Exibe a Tabela de Resumo Inicial (como solicitado)
    print("\n+--------------------------+------------------+------------+")
    print(f"| {'CLASSE DE ATIVO':<24} | {'VALOR DE MERCADO':>16} | {'ALOCAÇÃO':>10} |")
    print("+--------------------------+------------------+------------+")

    # Ordena as classes por valor para exibir a mais relevante primeiro
    sorted_classes = sorted(subtotais_por_classe.items(), key=lambda item: item[1], reverse=True)

    for classe, valor in sorted_classes:
        percentual = (valor / valor_total_mercado) * 100
        print(f"| {classe:<24} | R$ {valor:>14.2f} | {percentual:>9.2f}% |")

    print("+--------------------------+------------------+------------+")
    print(f"| {'TOTAL':<24} | R$ {valor_total_mercado:>14.2f} | {'100.00%':>10} |")
    print("+--------------------------+------------------+------------+")

    # 3. Exibe as Tabelas de Detalhamento Separadas
    for classe, subtotal_classe in sorted_classes:
        
        # Cabeçalho para a tabela de detalhe da classe
        print(f"\n--- DETALHAMENTO: {classe.upper()} ---")
        print(f"{'TICKER':<10} | {'QTD.':>8} | {'PREÇO ATUAL':>12} | {'VALOR MERCADO':>15} | {'% CARTEIRA':>12} | {'% CLASSE':>10}")
        print("-" * 90)

        # Pega a lista de ativos para esta classe
        lista_posicoes = posicoes_agrupadas[classe]
        # Ordena os ativos dentro da classe por valor
        lista_posicoes.sort(key=lambda p: p['valor_mercado'], reverse=True)

        for ativo in lista_posicoes:
            # Calcula os dois percentuais
            percentual_carteira = (ativo['valor_mercado'] / valor_total_mercado) * 100
            percentual_classe = (ativo['valor_mercado'] / subtotal_classe) * 100
            
            print(
                f"{ativo['ticker']:<10} | "
                f"{int(ativo['quantidade']):>8} | "
                f"R$ {ativo['preco_atual']:>10.2f} | "
                f"R$ {ativo['valor_mercado']:>13.2f} | "
                f"{percentual_carteira:>11.2f}% | "
                f"{percentual_classe:>9.2f}%"
            )
        print("-" * 90)

if __name__ == "__main__":
    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    exibir_analise_completa(service)