"""
Serviço de Cálculo de Custos — Coração do ERP DIGO
Recalcula automaticamente o custo do produto quando qualquer MP é alterada.
"""
from extensions import db
from models.materia_prima import MateriaPrima
from models.produto import ProdutoFinal


def recalcular_custo_produto():
    """
    Recalcula o custo do saco de argamassa baseado nos preços atuais das MPs.
    Chamado automaticamente quando qualquer preço de MP é alterado.

    Fórmula:
      custo_celulosico = (preco_saco + frete) / peso_saco * 12.5
      custo_celugel    = (preco_saco + frete) / peso_saco * 7.5
      custo_fibra      = (preco_saco + frete) / peso_saco * 5.0
      custo_embalagem  = preco_saco + frete
      custo_adesivo    = preco_saco
      custo_total      = soma de todos
    """
    produto = ProdutoFinal.query.first()
    if not produto:
        return 0.0

    custo_total = 0.0
    detalhes = {}

    mps = MateriaPrima.query.all()
    for mp in mps:
        custo = mp.custo_proporcional
        custo_total += custo
        detalhes[mp.tipo] = {
            'nome': mp.nome,
            'custo_proporcional': round(custo, 4),
            'custo_por_kg': round(mp.custo_por_kg, 4),
            'quantidade_uso': mp.quantidade_uso_kg,
        }

    produto.custo_calculado = round(custo_total, 4)

    # Atualizar preço de venda sugerido com base na margem
    if produto.margem_lucro_pct and produto.margem_lucro_pct > 0:
        # preco = custo / (1 - margem%)
        margem_decimal = produto.margem_lucro_pct / 100
        if margem_decimal < 1:
            produto.preco_venda_padrao = round(custo_total / (1 - margem_decimal), 2)

    db.session.commit()
    return custo_total, detalhes


def get_breakdown_custo():
    """Retorna breakdown detalhado do custo para exibição na tela"""
    mps = MateriaPrima.query.all()
    produto = ProdutoFinal.query.first()

    breakdown = []
    total = 0.0

    for mp in mps:
        custo = mp.custo_proporcional
        total += custo
        breakdown.append({
            'nome': mp.nome,
            'tipo': mp.tipo,
            'peso_saco': mp.peso_saco_kg,
            'qtd_uso': mp.quantidade_uso_kg,
            'preco_saco': mp.preco_saco,
            'frete_saco': mp.frete_saco,
            'custo_por_kg': round(mp.custo_por_kg, 4),
            'custo_proporcional': round(custo, 4),
        })

    return {
        'breakdown': breakdown,
        'custo_total': round(total, 4),
        'custo_por_kg': round(total / 25, 4) if total else 0,
        'preco_venda': produto.preco_venda_padrao if produto else 0,
        'margem_pct': produto.margem_lucro_pct if produto else 0,
        'lucro_por_saco': round(produto.lucro_por_saco, 4) if produto else 0,
    }
