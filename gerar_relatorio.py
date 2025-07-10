# gerar_relatorio.py

from db_nexus import DatabaseSessionManager
from app.services import PortfolioService

# --- Funções Auxiliares de Cor para o Terminal ---
# Adiciona cores para destacar as recomendações
VERDE = '\033[92m'
VERMELHO = '\033[91m'
AMARELO = '\033[93m'
RESET = '\033[0m'

def gerar_relatorio_completo(service: PortfolioService):
    """
    Gera e exibe o relatório final consolidado com as recomendações de Compra/Venda/Neutro.
    """
    print("\n--- Relatório Consolidado de Análise de Carteira e Risk Parity ---")

    # 1. Chama o novo método de serviço para obter todos os dados de uma vez
    analise_completa = service.gerar_analise_consolidada()

    if not analise_completa:
        print("Não foi possível gerar a análise. Verifique se os dados históricos e de transações existem.")
        return

    # 2. Itera sobre cada classe de ativo para exibir sua tabela
    for classe, ativos in analise_completa.items():
        print(f"\n--- ANÁLISE PARA A CLASSE: {classe.upper()} ---")
        print(f"{'TICKER':<10} | {'ALOC. ATUAL (CLASSE)':>22} | {'ALOC. RP SUGERIDA':>20} | {'RECOMENDAÇÃO'}")
        print("-" * 85)

        # Ordena os ativos pelo ticker para consistência
        ativos.sort(key=lambda x: x['ticker'])

        for ativo in ativos:
            aloc_atual_pct = ativo['alocacao_atual_na_classe'] * 100
            aloc_sugerida_pct = ativo['alocacao_sugerida'] * 100

            # Define a faixa de tolerância de +/- 20%
            faixa_min = aloc_sugerida_pct * 0.80
            faixa_max = aloc_sugerida_pct * 1.20

            # Lógica para a recomendação
            if aloc_atual_pct > faixa_max:
                recomendacao = f"{VERMELHO}Venda{RESET}"
            elif aloc_atual_pct < faixa_min:
                recomendacao = f"{VERDE}Compra{RESET}"
            else:
                recomendacao = f"{AMARELO}Neutro{RESET}"
            
            print(
                f"{ativo['ticker']:<10} | "
                f"{aloc_atual_pct:>21.2f}% | "
                f"{aloc_sugerida_pct:>19.2f}% | "
                f"{recomendacao}"
            )
        
        print("-" * 85)


if __name__ == "__main__":
    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    gerar_relatorio_completo(service)