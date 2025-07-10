# repositories.py

import datetime 
from sqlalchemy.orm import Session
from db_nexus import BaseRepository, RecordNotFoundError  # Importamos nossa classe base
from .models import Ativo, Transacao, DadoHistorico, TipoOperacao  # Importamos nossos modelos

class AtivoRepository(BaseRepository[Ativo]):
    """
    Repositório para operações com o modelo Ativo.
    Herda todos os métodos genéricos (get_by_id, list_all, add, delete)
    de BaseRepository.
    """
    def __init__(self):
        # Passamos o modelo 'Ativo' para o construtor da classe pai.
        super().__init__(Ativo)

    # --- Métodos Específicos para Ativos ---

    def find_by_ticker(self, session: Session, ticker: str) -> Ativo | None:
        """
        Busca um ativo específico pelo seu ticker.
        Retorna o objeto Ativo ou None se não encontrar.
        """
        return session.query(self.model).filter_by(ticker=ticker.upper()).first()

    def find_or_create(self, session: Session, ticker: str, defaults: dict) -> Ativo:
        """
        Busca um ativo pelo ticker. Se não existir, cria um novo com os dados
        fornecidos em 'defaults'.
        Útil para não duplicar ativos ao importar dados.
        """
        ativo = self.find_by_ticker(session, ticker)
        if ativo:
            return ativo
        
        # Se não encontrou, cria um novo
        # O dicionário 'defaults' deve conter 'nome', 'tipo', etc.
        novo_ativo = Ativo(ticker=ticker.upper(), **defaults)
        self.add(session, novo_ativo)
        # O SQLAlchemy atualiza o objeto 'novo_ativo' com o ID após o add
        return novo_ativo

class TransacaoRepository(BaseRepository[Transacao]):
    """
    Repositório para operações com o modelo Transacao.
    """
    def __init__(self):
        super().__init__(Transacao)

    # --- Métodos Específicos para Transações ---
    
    def find_by_ativo_id(self, session: Session, ativo_id: int) -> list[Transacao]:
        """
        Busca todas as transações de um determinado ativo.
        """
        return session.query(self.model).filter_by(ativo_id=ativo_id).order_by(self.model.data.asc()).all()
    
    def existe_transacao_identica(self, session: Session, ativo_id: int, data: datetime.date, tipo_op: TipoOperacao, qtd: float, preco: float) -> bool:
        """
        Verifica se uma transação com exatamente os mesmos parâmetros já existe.
        """
        # SQLAlchemy nos permite construir queries complexas de forma legível
        return session.query(
            session.query(self.model)
            .filter_by(
                ativo_id=ativo_id,
                data=data,
                tipo_operacao=tipo_op,
                quantidade=qtd,
                preco_unitario=preco
            ).exists()
        ).scalar()


class DadoHistoricoRepository(BaseRepository[DadoHistorico]):
    """
    Repositório para operações com o modelo DadoHistorico.
    """
    def __init__(self):
        super().__init__(DadoHistorico)

    # --- Métodos Específicos para Dados Históricos ---

    def find_by_ticker_and_date_range(self, session: Session, ticker: str, start_date: str, end_date: str) -> list[DadoHistorico]:
        """
        Busca os dados históricos para um ticker dentro de um intervalo de datas.
        """
        return session.query(self.model)\
            .filter(self.model.ticker == ticker.upper())\
            .filter(self.model.data.between(start_date, end_date))\
            .order_by(self.model.data.asc())\
            .all()
    
    def get_latest_price(self, session: Session, ticker: str) -> DadoHistorico | None:
        """
        Busca o registro de dado histórico mais recente para um ticker.
        """
        return session.query(self.model)\
            .filter(self.model.ticker == ticker.upper())\
            .order_by(self.model.data.desc())\
            .first()