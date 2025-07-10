# recomendar_rebalanceamento.py (Versão com Preço Atual na Tabela)

import math
from db_nexus import DatabaseSessionManager
from app.services import PortfolioService
from app.models import TipoAtivo

# --- Cores ---
VERDE = '\033[92m'
VERMELHO = '\033[91m'
AMARELO = '\033[93m'
RESET = '\033[0m'

def gerar_plano_de_rebalanceamento(service: PortfolioService):
    """
    Gera o relatório final com sugestões de rebalanceamento, incluindo o
    preço atual de cada ativo na tabela de detalhamento.
    """
    print("\n--- Relatório de Rebalanceamento Sugerido (Movimentos Suaves) ---")

    plano = service.gerar_plano_rebalanceamento_capital_neutro()

    if not plano:
        print("Não foi possível gerar o plano de rebalanceamento.")
        return

    total_geral_compras = 0
    total_geral_vendas = 0

    sorted_plano = sorted(plano.items(), key=lambda item: sum(a['valor_mercado'] for a in item[1]), reverse=True)

    for classe, ativos in sorted_plano:
        print(f"\n--- CLASSE: {classe.upper()} ---")
        # --- CABEÇALHO ATUALIZADO ---
        print(f"{'TICKER':<10} | {'PREÇO ATUAL':>12} | {'ALOC. ATUAL':>12} | {'FAIXA RP':>18} | {'RECOMENDAÇÃO':<22} | {'VALOR (R$)':>15} | {'QTD. APROX.'}")
        print("-" * 120)
        
        linhas_para_imprimir = []

        for ativo in ativos:
            recomendacao = ativo['recomendacao']
            valor = ativo['valor_a_movimentar']
            cor = AMARELO
            
            if recomendacao == "Vender":
                cor = VERMELHO
                total_geral_vendas += valor
            elif recomendacao == "Comprar":
                cor = VERDE
                total_geral_compras += valor
            
            aloc_atual_pct = ativo['alocacao_atual_na_classe'] * 100
            aloc_sugerida_pct = ativo['alocacao_sugerida'] * 100
            faixa_min_pct = aloc_sugerida_pct * 0.80
            faixa_max_pct = aloc_sugerida_pct * 1.20
            faixa_str = f"{faixa_min_pct:.2f}% a {faixa_max_pct:.2f}%"
            
            qtd_a_movimentar = math.floor(valor / ativo['preco_atual']) if ativo['preco_atual'] > 0 else 0
            unidade_label = "ações" if ativo['tipo_ativo'] == TipoAtivo.ACAO else "cotas"
            qtd_str = f"{qtd_a_movimentar} {unidade_label}" if qtd_a_movimentar > 0 else "-"
            
            # --- LINHA FORMATADA ATUALIZADA ---
            linha_formatada = (
                f"{ativo['ticker']:<10} | "
                f"R$ {ativo['preco_atual']:>10.2f} | " # <-- NOVA COLUNA ADICIONADA AQUI
                f"{aloc_atual_pct:>11.2f}% | "
                f"{faixa_str:>18} | "
                f"{recomendacao:<22} | "
                f"R$ {valor:>12.2f} | "
                f"{qtd_str}"
            )
            
            ordem_prioridade = {'Vender': 0, 'Comprar': 1}.get(recomendacao, 2)

            linhas_para_imprimir.append({
                'prioridade': ordem_prioridade,
                'linha_texto': f"{cor}{linha_formatada}{RESET}"
            })
        
        linhas_para_imprimir.sort(key=lambda item: item['prioridade'])
        
        for item in linhas_para_imprimir:
            print(item['linha_texto'])

        print("-" * 120)

    # --- Resumo Final do Plano ---
    balanco_liquido = total_geral_vendas - total_geral_compras
    
    print("\n" + "="*45)
    print(" RESUMO DO PLANO DE REBALANCEAMENTO")
    print("="*45)
    print(f"  Total de Vendas Sugerido: {VERMELHO}R$ {total_geral_vendas:,.2f}{RESET}")
    print(f"  Total de Compras Viáveis: {VERDE}R$ {total_geral_compras:,.2f}{RESET}")
    print("-" * 45)
    
    if balanco_liquido > 0:
        cor_balanco = VERDE
        texto_balanco = f"  Saldo em Caixa Previsto:  {cor_balanco}R$ {balanco_liquido:,.2f}{RESET}"
    else:
        cor_balanco = AMARELO
        texto_balanco = f"  Aporte Adicional Necessário: {cor_balanco}R$ {-balanco_liquido:,.2f}{RESET}"
    
    print(texto_balanco)
    print("="*45)
    print("(Diferença ocorre por compras não viáveis)")


if __name__ == "__main__":
    DB_URL = "sqlite:///data/portfolio.db"
    session_manager = DatabaseSessionManager(DB_URL)
    service = PortfolioService(session_manager)
    
    gerar_plano_de_rebalanceamento(service)