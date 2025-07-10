# main.py (Versão Refatorada)

# Importa a função de setup diretamente do models.py
from app.models import setup_inicial_se_necessario
from db_nexus import DatabaseSessionManager
from app.services import PortfolioService
from app.view import exibir_portfolio

def rodar_dashboard():
    """
    Função principal que inicializa os serviços e exibe o portfólio.
    """
    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    exibir_portfolio(service)

if __name__ == "__main__":
    # 1. Chama a função de setup centralizada
    banco_ja_existia = setup_inicial_se_necessario()
    
    # 2. Roda o dashboard apenas se o banco já existia
    if banco_ja_existia:
        rodar_dashboard()
    else:
        # Se o banco acabou de ser criado, avisa o usuário para importar os dados
        print("\n➡️  Agora, execute o script de importação para popular os dados:")
        print("   python3 importar_csv.py")