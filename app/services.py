# services.py

import datetime
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict

# Dependências da nossa aplicação
from db_nexus import DatabaseSessionManager
from .models import Ativo, Transacao, DadoHistorico, TipoAtivo, TipoOperacao
from .repositories import AtivoRepository, TransacaoRepository, DadoHistoricoRepository

# --- Estruturas de Dados ---

@dataclass
class PosicaoAtivo:
    """
    Representa a posição consolidada de um ativo na carteira.
    É um objeto de dados, não um modelo do banco.
    """
    ticker: str
    tipo_ativo: TipoAtivo
    quantidade_total: float = 0.0
    custo_total: float = 0.0
    preco_medio: float = field(init=False, default=0.0)

    def __post_init__(self):
        """Calcula o preço médio após a inicialização do objeto."""
        if self.quantidade_total > 0:
            self.preco_medio = self.custo_total / self.quantidade_total
        else:
            self.preco_medio = 0.0

# --- Classe de Serviço ---

class PortfolioService:
    """
    Orquestra as operações relacionadas à análise de portfólio.
    Esta é a camada de lógica de negócio.
    """
    def __init__(self, session_manager: DatabaseSessionManager):
        # Injeção de Dependência: o serviço recebe o gerenciador de sessão.
        self.session_manager = session_manager
        # O serviço instancia os repositórios que ele precisa.
        self.ativo_repo = AtivoRepository()
        self.transacao_repo = TransacaoRepository()
        self.dado_historico_repo = DadoHistoricoRepository()

    def adicionar_transacao_completa(
        self,
        ticker: str,
        nome_ativo: str,
        tipo_ativo: TipoAtivo,
        data: datetime.date,
        tipo_operacao: TipoOperacao,
        quantidade: float,
        preco_unitario: float,
    ) -> Transacao:
        """
        Adiciona uma nova transação, criando o ativo se ele não existir.
        Este método mostra como o serviço coordena dois repositórios.
        """
        with self.session_manager.get_session() as session:
            # 1. Usa o repositório de ativos para buscar ou criar o ativo.
            dados_ativo = {'nome': nome_ativo, 'tipo': tipo_ativo}
            ativo = self.ativo_repo.find_or_create(session, ticker, defaults=dados_ativo)

            # 2. Cria o objeto da transação, ligando ao ID do ativo.
            nova_transacao = Transacao(
                data=data,
                tipo_operacao=tipo_operacao,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
            )

            # 3. A MÁGICA DO SQLALCHEMY: Atribua o objeto pai ao relacionamento.
            # O SQLAlchemy se encarregará de descobrir o ID quando for salvar.
            nova_transacao.ativo = ativo

            # 4. Adiciona a nova transação à sessão.
            session.add(nova_transacao)

            # 5. Força o envio do INSERT para o banco e a obtenção do ID.
            session.flush()
            
            # 6. Agora o refresh pode ser feito, pois o objeto tem um ID e existe no banco.
            # O 'with' garante o commit. O SQLAlchemy atualiza 'nova_transacao' com seu ID.
            return nova_transacao
        
    def importar_transacao_se_nova(self, ticker: str, nome_ativo: str, tipo_ativo: TipoAtivo, data: datetime.date, tipo_operacao: TipoOperacao, quantidade: float, preco_unitario: float) -> dict:
        """
        Importa uma transação apenas se uma idêntica já não existir no banco.
        Retorna um dicionário com o status da operação.
        """
        with self.session_manager.get_session() as session:
            # Primeiro, encontra ou cria o ativo para obter seu ID
            ativo = self.ativo_repo.find_or_create(session, ticker, defaults={'nome': nome_ativo, 'tipo': tipo_ativo})
            session.flush() # Garante que o ativo tenha um ID, mesmo se for novo

            # Agora, verifica se a transação já existe usando o ID do ativo
            if self.transacao_repo.existe_transacao_identica(session, ativo.id, data, tipo_operacao, quantidade, preco_unitario):
                return {'status': 'skipped', 'ticker': ticker}
            
            # Se não existe, cria e adiciona a nova transação
            nova_transacao = Transacao(
                ativo_id=ativo.id,
                data=data,
                tipo_operacao=tipo_operacao,
                quantidade=quantidade,
                preco_unitario=preco_unitario,
            )
            self.transacao_repo.add(session, nova_transacao)
            
            return {'status': 'imported', 'ticker': ticker}

    def calcular_portfolio_atual(self) -> List[PosicaoAtivo]:
        """
        Calcula a posição atual de cada ativo na carteira com base em todas as transações.
        """
        with self.session_manager.get_session() as session:
            todas_as_transacoes = self.transacao_repo.list_all(session, limit=10000) # Limite alto
            
            # Dicionário para agregar os dados por ticker
            posicoes: Dict[str, Dict] = {}

            for transacao in todas_as_transacoes:
                ticker = transacao.ativo.ticker
                
                # Se for a primeira vez que vemos este ticker, inicializa sua posição
                if ticker not in posicoes:
                    posicoes[ticker] = {
                        "tipo_ativo": transacao.ativo.tipo,
                        "quantidade_total": 0.0,
                        "custo_total": 0.0
                    }
                
                # Atualiza a posição com base no tipo de operação
                if transacao.tipo_operacao == TipoOperacao.COMPRA:
                    posicoes[ticker]["quantidade_total"] += transacao.quantidade
                    posicoes[ticker]["custo_total"] += transacao.quantidade * transacao.preco_unitario
                elif transacao.tipo_operacao == TipoOperacao.VENDA:
                    # Simplificação: para vendas, apenas reduzimos a quantidade.
                    # O cálculo de custo em vendas (preço médio, FIFO) pode ser complexo.
                    # Por enquanto, focamos na posição atual.
                    posicoes[ticker]["quantidade_total"] -= transacao.quantidade
            
            # Converte o dicionário de posições em uma lista de objetos PosicaoAtivo
            portfolio_final = []
            for ticker, dados in posicoes.items():
                # Ignora ativos que foram totalmente vendidos
                if dados["quantidade_total"] > 0.0001: 
                    posicao = PosicaoAtivo(
                        ticker=ticker,
                        tipo_ativo=dados["tipo_ativo"],
                        quantidade_total=dados["quantidade_total"],
                        custo_total=dados["custo_total"],
                    )
                    portfolio_final.append(posicao)
            
            return portfolio_final

    def importar_dados_historicos(self, dados: List[Dict]):
        """
        Importa uma lista de dados históricos para o banco.
        'dados' deve ser uma lista de dicionários, ex:
        [{'ticker': 'BOVA11', 'data': '2025-07-10', 'preco_fechamento': 120.50}]
        """
        with self.session_manager.get_session() as session:
            print(f"Importando {len(dados)} registros de dados históricos...")
            for registro in dados:
                # O ideal aqui seria verificar se o registro já não existe para não duplicar
                # mas nossa UniqueConstraint no modelo já nos protege de duplicatas exatas.
                dado_historico = DadoHistorico(
                    ticker=registro['ticker'],
                    data=datetime.date.fromisoformat(registro['data']),
                    preco_fechamento=registro['preco_fechamento']
                )
                self.dado_historico_repo.add(session, dado_historico)
            print("Importação concluída.")
            # Commit é feito automaticamente ao sair do 'with'
    
    def get_all_asset_tickers(self) -> List[str]:
        """Busca e retorna uma lista com os tickers de todos os ativos cadastrados."""
        with self.session_manager.get_session() as session:
            # O resultado é uma lista de tuplas, ex: [('CXSE3',), ('EZTC3',)]
            # então usamos uma list comprehension para extrair o primeiro item de cada tupla.
            resultados = session.query(Ativo.ticker).all()
            return [ticker for (ticker,) in resultados]
        
    def get_market_value_portfolio(self) -> List[Dict]:
        """
        Calcula a posição atual da carteira e enriquece com o valor de mercado atual.
        Retorna uma lista de dicionários com todos os dados.
        """
        posicoes_custo = self.calcular_portfolio_atual()
        portfolio_valor_mercado = []

        with self.session_manager.get_session() as session:
            for posicao in posicoes_custo:
                # Busca o preço mais recente no nosso banco de dados
                dado_recente = self.dado_historico_repo.get_latest_price(session, posicao.ticker)

                preco_atual = dado_recente.preco_fechamento if dado_recente else 0
                valor_mercado = posicao.quantidade_total * preco_atual

                portfolio_valor_mercado.append({
                    "ticker": posicao.ticker,
                    "tipo_ativo": posicao.tipo_ativo,
                    "quantidade": posicao.quantidade_total,
                    "preco_medio_custo": posicao.preco_medio,
                    "custo_total": posicao.custo_total,
                    "preco_atual": preco_atual,
                    "valor_mercado": valor_mercado,
                    "data_ultima_cotacao": dado_recente.data if dado_recente else None
                })

        return portfolio_valor_mercado
    
    def calcular_alocacao_risk_parity_por_classe(self) -> dict:
        """
        Calcula a alocação de paridade de risco (Risk Parity) para cada classe de ativo.
        A análise é baseada na volatilidade dos últimos 2 anos.
        """
        with self.session_manager.get_session() as session:
            # 1. Busca todos os dados necessários do banco
            historico_query = session.query(DadoHistorico).all()
            ativos_query = session.query(Ativo).all()

            if not historico_query or not ativos_query:
                print("⚠️ Dados históricos ou de ativos insuficientes para a análise.")
                return {}

            # 2. Converte os dados para DataFrames do Pandas para facilitar a análise
            df_historico = pd.DataFrame([h.__dict__ for h in historico_query])
            df_ativos = pd.DataFrame([a.__dict__ for a in ativos_query])
            df_ativos['tipo'] = df_ativos['tipo'].apply(lambda x: x.value)

            # 3. Prepara a matriz de preços: tickers nas colunas, datas como índice
            df_precos = df_historico.pivot(index='data', columns='ticker', values='preco_fechamento')

            # 4. Calcula os retornos diários
            df_retornos = df_precos.pct_change().dropna()

            # 5. Calcula a volatilidade anualizada (desvio padrão dos retornos * raiz de 252)
            # 252 é o número aproximado de dias de pregão em um ano.
            volatilidades = df_retornos.std() * np.sqrt(252)

            # 6. Agrupa os tickers pela sua classe (tipo)
            tickers_por_classe = df_ativos.groupby('tipo')['ticker'].apply(list).to_dict()

            resultado_final = {}
            # 7. Calcula o Risk Parity para cada classe de ativo
            for classe, tickers_na_classe in tickers_por_classe.items():
                # Filtra as volatilidades apenas para os ativos desta classe
                vol_classe = volatilidades.reindex(tickers_na_classe).dropna()
                
                if vol_classe.empty:
                    continue

                # Calcula o peso inverso da volatilidade
                inv_vol = 1 / vol_classe
                soma_inv_vol = inv_vol.sum()

                # Normaliza para que a soma dos pesos seja 100%
                pesos_rp = (inv_vol / soma_inv_vol) if soma_inv_vol > 0 else pd.Series(0, index=inv_vol.index)

                # Monta a estrutura de dados do resultado
                resultado_classe = []
                for ticker, peso_sugerido in pesos_rp.items():
                    volatilidade_ativo = vol_classe.get(ticker, 0)
                    resultado_classe.append({
                        "ticker": ticker,
                        "volatilidade_anual": volatilidade_ativo,
                        "alocacao_sugerida": peso_sugerido,
                    })
                
                # Ordena por alocação sugerida
                resultado_classe.sort(key=lambda x: x['alocacao_sugerida'], reverse=True)
                resultado_final[classe] = resultado_classe

            return resultado_final
        
    def gerar_analise_consolidada(self) -> dict:
        """
        Combina a análise de portfólio atual (valor de mercado) com a análise
        de Risk Parity, retornando uma estrutura de dados completa para o relatório.
        """
        # 1. Busca as duas análises que já temos
        portfolio_atual = self.get_market_value_portfolio()
        analise_rp = self.calcular_alocacao_risk_parity_por_classe()

        if not portfolio_atual or not analise_rp:
            return {}

        # 2. Converte para DataFrames do Pandas para facilitar a junção dos dados
        df_atual = pd.DataFrame(portfolio_atual)
        
        # Constrói o DataFrame de Risk Parity a partir do dicionário
        lista_rp = []
        for classe, resultados in analise_rp.items():
            for res in resultados:
                res['tipo'] = classe
                lista_rp.append(res)
        df_rp = pd.DataFrame(lista_rp)

        # 3. Junta as duas tabelas de dados usando o 'ticker' como chave
        if 'tipo_ativo' in df_atual.columns:
            df_atual['tipo'] = df_atual['tipo_ativo'].apply(lambda x: x.value)
        
        df_consolidado = pd.merge(df_atual, df_rp, on=['ticker', 'tipo'], how='left')

        # 4. Organiza o resultado final em um dicionário agrupado por classe
        resultado_final = {}
        for classe in df_consolidado['tipo'].unique():
            df_classe = df_consolidado[df_consolidado['tipo'] == classe].copy()
            
            # Calcula a alocação atual dentro da classe
            subtotal_classe = df_classe['valor_mercado'].sum()
            df_classe['alocacao_atual_na_classe'] = (df_classe['valor_mercado'] / subtotal_classe)
            
            resultado_final[classe] = df_classe.to_dict('records')

        return resultado_final
    
    def gerar_plano_rebalanceamento_capital_neutro(self) -> dict:
        """
        Gera um plano de rebalanceamento com capital neutro, com uma lógica explícita
        de separação entre ativos de Venda, Compra e Neutro.
        """
        analise_bruta = self.gerar_analise_consolidada()
        if not analise_bruta:
            return {}

        ativos_venda = []
        ativos_compra_candidatos = []
        ativos_neutros = []
        
        # --- FASE 1: Classificar explicitamente cada ativo ---
        for classe, ativos in analise_bruta.items():
            subtotal_classe = sum(ativo['valor_mercado'] for ativo in ativos)
            for ativo in ativos:
                aloc_atual_pct = ativo['alocacao_atual_na_classe'] * 100
                aloc_sugerida_pct = ativo['alocacao_sugerida'] * 100
                faixa_max_pct = aloc_sugerida_pct * 1.20
                faixa_min_pct = aloc_sugerida_pct * 0.80

                if aloc_atual_pct > faixa_max_pct:
                    # É uma ordem de venda
                    percentual_excedente = aloc_atual_pct - faixa_max_pct
                    ativo['valor_a_movimentar'] = (percentual_excedente / 100) * subtotal_classe
                    ativo['recomendacao'] = "Vender"
                    ativos_venda.append(ativo)
                elif aloc_atual_pct < faixa_min_pct:
                    # É um candidato à compra
                    ativo['valor_a_movimentar'] = 0 # Valor será calculado depois
                    ativo['recomendacao'] = "Comprar"
                    ativos_compra_candidatos.append(ativo)
                else:
                    # É uma posição neutra
                    ativo['valor_a_movimentar'] = 0
                    ativo['recomendacao'] = "Neutro"
                    ativos_neutros.append(ativo)

        # --- FASE 2: Calcular o caixa total gerado pelas vendas ---
        caixa_gerado_pelas_vendas = sum(ativo['valor_a_movimentar'] for ativo in ativos_venda)

        # --- FASE 3: Distribuir o caixa entre os candidatos à compra ---
        if caixa_gerado_pelas_vendas > 0 and ativos_compra_candidatos:
            # Calcula o "gap" total de compra
            gap_total_compra = 0
            for ativo in ativos_compra_candidatos:
                subtotal_classe_ativo = sum(p['valor_mercado'] for p in analise_bruta[ativo['tipo']])
                aloc_atual_pct = ativo['alocacao_atual_na_classe'] * 100
                aloc_sugerida_pct = ativo['alocacao_sugerida'] * 100
                faixa_min_pct = aloc_sugerida_pct * 0.80
                ativo['gap_compra'] = (faixa_min_pct - aloc_atual_pct) / 100 * subtotal_classe_ativo
                gap_total_compra += ativo['gap_compra']
            
            # Distribui o caixa proporcionalmente
            if gap_total_compra > 0:
                for ativo in ativos_compra_candidatos:
                    proporcao = ativo['gap_compra'] / gap_total_compra
                    valor_compra = caixa_gerado_pelas_vendas * proporcao
                    
                    if valor_compra < ativo['preco_atual']:
                        ativo['recomendacao'] = "Neutro (Valor Insuf.)"
                        ativos_neutros.append(ativo) # Move da lista de compra para neutro
                    else:
                        ativo['valor_a_movimentar'] = valor_compra
            # Remove os ativos que se tornaram neutros da lista de compra
            ativos_compra_candidatos = [a for a in ativos_compra_candidatos if a['recomendacao'] == "Comprar"]

        # --- FASE 4: Reagrupar tudo para o relatório final ---
        plano_final = {}
        todos_os_ativos = ativos_venda + ativos_compra_candidatos + ativos_neutros
        for ativo in todos_os_ativos:
            classe = ativo['tipo']
            if classe not in plano_final:
                plano_final[classe] = []
            plano_final[classe].append(ativo)

        return plano_final
    
    def gerar_plano_de_aporte(self, valor_aporte: float) -> dict:
        """
        Gera um plano de alocação para um novo aporte em dinheiro, priorizando
        as compras dos ativos mais subalocados sem gerar vendas.
        """
        analise_bruta = self.gerar_analise_consolidada()
        if not analise_bruta:
            return {}

        ativos_compra_candidatos = []
        
        # --- FASE 1: Identificar todos os candidatos à compra ---
        for classe, ativos in analise_bruta.items():
            for ativo in ativos:
                aloc_atual_pct = ativo['alocacao_atual_na_classe'] * 100
                aloc_sugerida_pct = ativo['alocacao_sugerida'] * 100
                faixa_min_pct = aloc_sugerida_pct * 0.80

                if aloc_atual_pct < faixa_min_pct:
                    # Calcula o "gap" monetário para atingir o alvo mínimo
                    subtotal_classe = sum(p['valor_mercado'] for p in analise_bruta[classe])
                    gap_percentual = faixa_min_pct - aloc_atual_pct
                    ativo['valor_necessario'] = (gap_percentual / 100) * subtotal_classe
                    ativos_compra_candidatos.append(ativo)
        
        # --- FASE 2: Alocação em Cascata do Aporte ---
        # Ordena os candidatos pelo maior "gap" (mais necessitado primeiro)
        ativos_compra_candidatos.sort(key=lambda x: x['valor_necessario'], reverse=True)

        caixa_disponivel = valor_aporte
        ordens_de_compra = []

        for ativo in ativos_compra_candidatos:
            if caixa_disponivel < 0.01:
                break # Dinheiro do aporte acabou

            # O valor a comprar é o menor entre o caixa que temos e o que o ativo "precisa"
            valor_a_comprar = min(caixa_disponivel, ativo['valor_necessario'])

            if valor_a_comprar >= ativo['preco_atual']:
                # Atualiza o valor final a ser movimentado e o caixa restante
                ativo['valor_a_movimentar'] = valor_a_comprar
                caixa_disponivel -= valor_a_comprar
                ordens_de_compra.append(ativo)
        
        return {
            "ordens_de_compra": ordens_de_compra,
            "caixa_restante": caixa_disponivel
        }
