"""
Serviço de Estoque — Movimentações Automáticas
Toda entrada/saída de estoque passa por este serviço para garantir rastreabilidade.
"""
from extensions import db
from models.materia_prima import MateriaPrima
from models.produto import ProdutoFinal
from models.estoque import MovimentacaoEstoque
from datetime import datetime


def entrada_mp(materia_prima_id, quantidade_sacos, motivo='compra',
               referencia_id=None, referencia_tipo=None, usuario_id=None, obs=None):
    """Registra entrada de matéria-prima no estoque"""
    mp = MateriaPrima.query.get(materia_prima_id)
    if not mp:
        raise ValueError(f"Matéria-prima #{materia_prima_id} não encontrada")

    saldo_antes = mp.estoque_atual
    mp.estoque_atual += quantidade_sacos
    saldo_depois = mp.estoque_atual

    mov = MovimentacaoEstoque(
        data=datetime.utcnow(),
        tipo='entrada',
        materia_prima_id=materia_prima_id,
        quantidade=quantidade_sacos,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        motivo=motivo,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        usuario_id=usuario_id,
        observacoes=obs
    )
    db.session.add(mov)
    return mov


def saida_mp(materia_prima_id, quantidade, motivo='producao',
             referencia_id=None, referencia_tipo=None, usuario_id=None, obs=None):
    """Registra saída de matéria-prima do estoque"""
    mp = MateriaPrima.query.get(materia_prima_id)
    if not mp:
        raise ValueError(f"Matéria-prima #{materia_prima_id} não encontrada")

    saldo_antes = mp.estoque_atual
    mp.estoque_atual -= quantidade
    saldo_depois = mp.estoque_atual

    mov = MovimentacaoEstoque(
        data=datetime.utcnow(),
        tipo='saida',
        materia_prima_id=materia_prima_id,
        quantidade=quantidade,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        motivo=motivo,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        usuario_id=usuario_id,
        observacoes=obs
    )
    db.session.add(mov)
    return mov


def entrada_produto(quantidade_sacos, motivo='producao',
                    referencia_id=None, referencia_tipo=None, usuario_id=None, obs=None):
    """Registra entrada de produto acabado"""
    produto = ProdutoFinal.query.first()
    if not produto:
        raise ValueError("Produto final não cadastrado")

    saldo_antes = produto.estoque_atual
    produto.estoque_atual += quantidade_sacos
    saldo_depois = produto.estoque_atual

    mov = MovimentacaoEstoque(
        data=datetime.utcnow(),
        tipo='entrada',
        produto_id=produto.id,
        quantidade=quantidade_sacos,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        motivo=motivo,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        usuario_id=usuario_id,
        observacoes=obs
    )
    db.session.add(mov)
    return mov


def saida_produto(quantidade_sacos, motivo='venda',
                  referencia_id=None, referencia_tipo=None, usuario_id=None, obs=None):
    """Registra saída de produto acabado (venda)"""
    produto = ProdutoFinal.query.first()
    if not produto:
        raise ValueError("Produto final não cadastrado")

    saldo_antes = produto.estoque_atual
    produto.estoque_atual -= quantidade_sacos
    saldo_depois = produto.estoque_atual

    mov = MovimentacaoEstoque(
        data=datetime.utcnow(),
        tipo='saida',
        produto_id=produto.id,
        quantidade=quantidade_sacos,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        motivo=motivo,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        usuario_id=usuario_id,
        observacoes=obs
    )
    db.session.add(mov)
    return mov


def atualizar_custo_medio(mp, quantidade_nova, custo_novo_por_saco):
    """Atualiza custo médio ponderado da MP após uma compra"""
    # estoque antes da compra (mp.estoque_atual ainda não foi incrementado)
    estoque_atual = mp.estoque_atual
    if estoque_atual < 0:
        estoque_atual = 0

    custo_atual = mp.custo_medio if mp.custo_medio else (mp.preco_saco + mp.frete_saco)
    total_sacos = estoque_atual + quantidade_nova

    if total_sacos > 0:
        mp.custo_medio = round(
            (estoque_atual * custo_atual + quantidade_nova * custo_novo_por_saco) / total_sacos, 4
        )


def get_alertas_estoque():
    """Retorna lista de MPs e produto com estoque abaixo do mínimo"""
    alertas = []
    mps = MateriaPrima.query.filter(
        MateriaPrima.estoque_atual < MateriaPrima.estoque_minimo
    ).all()
    for mp in mps:
        alertas.append({
            'tipo': 'mp',
            'nome': mp.nome,
            'atual': mp.estoque_atual,
            'minimo': mp.estoque_minimo,
            'unidade': 'sacos'
        })

    produto = ProdutoFinal.query.first()
    if produto and produto.abaixo_minimo:
        alertas.append({
            'tipo': 'produto',
            'nome': produto.nome,
            'atual': produto.estoque_atual,
            'minimo': produto.estoque_minimo,
            'unidade': 'sacos'
        })

    return alertas
