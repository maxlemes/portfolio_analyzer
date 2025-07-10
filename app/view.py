# app/view.py (novo arquivo)

from .services import PortfolioService, PosicaoAtivo

def exibir_portfolio(portfolio_service: PortfolioService):
    """
    Calcula e exibe a posição atual da carteira de forma formatada.
    """
    print("\n--- Posição Atual do Portfólio ---")
    
    posicoes = portfolio_service.calcular_portfolio_atual()
    
    if not posicoes:
        print("Sua carteira está vazia.")
        return

    print(f"{'TICKER':<10} | {'TIPO':<18} | {'QTD.':>10} | {'P. MÉDIO':>12} | {'CUSTO TOTAL':>15} | {'ALOCAÇÃO':>10}")
    print("-" * 90)

    custo_total_carteira = sum(p.custo_total for p in posicoes)

    for posicao in posicoes:
        alocacao_percentual = (posicao.custo_total / custo_total_carteira) * 100 if custo_total_carteira > 0 else 0
        
        print(
            f"{posicao.ticker:<10} | "
            f"{posicao.tipo_ativo.value:<18} | "
            f"{posicao.quantidade_total:>10.2f} | "
            f"R$ {posicao.preco_medio:>10.2f} | "
            f"R$ {posicao.custo_total:>13.2f} | "
            f"{alocacao_percentual:>9.2f}%"
        )
    
    print("-" * 90)
    print(f"{'CUSTO TOTAL DA CARTEIRA:':<68} R$ {custo_total_carteira:>15.2f}")