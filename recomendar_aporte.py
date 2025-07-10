# recomendar_aporte.py (novo arquivo na raiz do projeto)

import math
from db_nexus import DatabaseSessionManager
from app.services import PortfolioService
from app.models import TipoAtivo

# --- Cores ---
VERDE = '\033[92m'
RESET = '\033[0m'

def gerar_relatorio_de_aporte(service: PortfolioService, valor_aporte: float):
    """
    Chama o serviço de aporte e exibe o plano de compras sugerido.
    """
    print(f"\n--- Plano de Aporte Sugerido para R$ {valor_aporte:,.2f} ---")

    # 1. Chama o novo método de serviço com o valor do aporte
    plano = service.gerar_plano_de_aporte(valor_aporte)

    if not plano or not plano['ordens_de_compra']:
        print("\nNenhuma oportunidade de compra encontrada para o aporte.")
        print(f"Sugestão: Aporte o valor total de R$ {valor_aporte:,.2f} no seu ativo de caixa.")
        return

    # 2. Exibe a tabela com as ordens de compra
    print(f"\n{'TICKER':<10} | {'CLASSE':<20} | {'VALOR (R$) A COMPRAR':>20} | {'QTD. APROX.'}")
    print("-" * 75)

    for ativo in plano['ordens_de_compra']:
        valor = ativo['valor_a_movimentar']
        qtd_a_movimentar = math.floor(valor / ativo['preco_atual']) if ativo['preco_atual'] > 0 else 0
        unidade_label = "ações" if ativo['tipo_ativo'] == TipoAtivo.ACAO else "cotas"
        qtd_str = f"{qtd_a_movimentar} {unidade_label}" if qtd_a_movimentar > 0 else "-"

        linha_formatada = (
            f"{ativo['ticker']:<10} | "
            f"{ativo['tipo']:<20} | "
            f"R$ {valor:>18.2f} | "
            f"{qtd_str}"
        )
        print(f"{VERDE}{linha_formatada}{RESET}")
    
    print("-" * 75)

    # 3. Exibe o resumo final
    total_compras = sum(a['valor_a_movimentar'] for a in plano['ordens_de_compra'])
    caixa_restante = plano['caixa_restante']

    print("\n" + "="*40)
    print(" RESUMO DO PLANO DE APORTE")
    print("="*40)
    print(f"  Valor do Aporte:      R$ {valor_aporte:,.2f}")
    print(f"  Total Alocado:        {VERDE}R$ {total_compras:,.2f}{RESET}")
    print("-" * 40)
    print(f"  Caixa Restante:       R$ {caixa_restante:,.2f}")
    print("="*40)


if __name__ == "__main__":
    try:
        aporte_str = input("Qual o valor do seu aporte em R$? ")
        valor_do_aporte = float(aporte_str)
    except ValueError:
        print("Valor inválido. Por favor, digite um número.")
        exit()

    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    gerar_relatorio_de_aporte(service, valor_do_aporte)