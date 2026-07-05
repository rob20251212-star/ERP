from app import create_app
from extensions import db
from models.venda import Venda
from models.compra import Compra
from models.financeiro import Financeiro
from models.materia_prima import MateriaPrima
from models.produto import ProdutoFinal
from sqlalchemy import func

def run_diagnostics():
    app = create_app()
    with app.app_context():
        print("=== DIAGNÓSTICOS DO SISTEMA ===")
        
        # 1. Verificação de Vendas
        vendas = Venda.query.all()
        print(f"Total de vendas cadastradas: {len(vendas)}")
        
        wrong_gross = 0
        wrong_liquid = 0
        wrong_profit = 0
        for v in vendas:
            # bruto = quantidade * preco_unitario
            expected_gross = round(v.quantidade_sacos * v.preco_unitario, 2)
            if abs(v.valor_bruto - expected_gross) > 0.02:
                wrong_gross += 1
                
            # lucro = valor_liquido - custo_total
            expected_profit = round(v.valor_liquido - v.custo_total, 2)
            if abs(v.lucro - expected_profit) > 0.02:
                wrong_profit += 1
                
        print(f"Vendas com discrepância de Valor Bruto: {wrong_gross}")
        print(f"Vendas com discrepância de Lucro: {wrong_profit}")
        
        # 2. Verificação de Compras
        compras = Compra.query.all()
        print(f"\nTotal de compras cadastradas: {len(compras)}")
        
        wrong_compra_total = 0
        for c in compras:
            expected_total = round(c.quantidade_sacos * c.preco_unitario, 2)
            if abs(c.total - expected_total) > 0.02:
                wrong_compra_total += 1
        print(f"Compras com discrepância de Total: {wrong_compra_total}")
        
        # 3. Verificação de Finanças (Fluxo de Caixa)
        financas = Financeiro.query.all()
        print(f"\nTotal de lançamentos financeiros: {len(financas)}")
        
        receitas = sum(f.valor for f in financas if f.tipo == 'receita')
        despesas = sum(f.valor for f in financas if f.tipo == 'despesa')
        print(f"  Receitas Totais: R$ {receitas:,.2f}")
        print(f"  Despesas Totais: R$ {despesas:,.2f}")
        print(f"  Saldo de Caixa: R$ {(receitas - despesas):,.2f}")

        # 4. Verificação de Matérias Primas
        mps = MateriaPrima.query.all()
        print("\n=== Matérias-Primas ===")
        for mp in mps:
            print(f"  {mp.nome} ({mp.tipo}):")
            print(f"    Estoque Atual: {mp.estoque_atual:.2f} sacos")
            print(f"    Custo Unitário Saco: R$ {mp.preco_saco:.2f}")
            print(f"    Frete Unitário Saco: R$ {mp.frete_saco:.2f}")
            print(f"    Custo Médio: R$ {mp.custo_medio:.2f}")

        # 5. Custo do Produto Final
        produto = ProdutoFinal.query.first()
        if produto:
            print(f"\n=== Produto Acabado: {produto.nome} ===")
            print(f"  Estoque Atual: {produto.estoque_atual:.2f} sacos")
            print(f"  Custo Calculado: R$ {produto.custo_calculado:.2f}")
            print(f"  Preço Venda Padrão: R$ {produto.preco_venda_padrao:.2f}")
            print(f"  Margem de Lucro: {produto.margem_lucro_pct:.1f}%")

if __name__ == '__main__':
    run_diagnostics()
