# analisar_risk_parity.py

from db_nexus import DatabaseSessionManager
from app.services import PortfolioService

def exibir_tabelas_risk_parity(service: PortfolioService):
    """
    Chama o serviço de análise de Risk Parity e exibe os resultados em tabelas.
    """
    print("\n--- Análise de Alocação por Paridade de Risco (Risk Parity) ---")

    # 1. Chama o novo método do serviço para obter os cálculos
    analise_rp = service.calcular_alocacao_risk_parity_por_classe()

    if not analise_rp:
        print("Não foi possível gerar a análise de Risk Parity.")
        return

    # 2. Itera sobre cada classe de ativo e imprime sua tabela de análise
    for classe, resultados in analise_rp.items():
        print(f"\n--- SUGESTÃO DE ALOCAÇÃO PARA A CLASSE: {classe.upper()} ---")
        print(f"{'TICKER':<10} | {'VOL. ANUALIZADA':>16} | {'ALOCAÇÃO RP SUGERIDA':>22} | {'FAIXA DE ALOCAÇÃO (+/- 20%)':>28}")
        print("-" * 85)

        for ativo in resultados:
            sugerido_pct = ativo['alocacao_sugerida'] * 100
            
            # Calcula a faixa de +/- 20%
            faixa_min = sugerido_pct * 0.80
            faixa_max = sugerido_pct * 1.20
            faixa_str = f"{faixa_min:.2f}% a {faixa_max:.2f}%"

            print(
                f"{ativo['ticker']:<10} | "
                f"{ativo['volatilidade_anual']:>15.2%} | "
                f"{sugerido_pct:>21.2f}% | "
                f"{faixa_str:>28}"
            )
        print("-" * 85)

if __name__ == "__main__":
    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    exibir_tabelas_risk_parity(service)