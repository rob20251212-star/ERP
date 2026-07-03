"""
Serviço Financeiro — Lançamentos Automáticos
Todo movimento financeiro é registrado aqui, garantindo fluxo de caixa sempre atualizado.
"""
from extensions import db
from models.financeiro import Financeiro
from models.venda import ContaReceber, ContaPagar
from datetime import date, timedelta


def lancar_receita(valor, descricao, categoria='venda',
                   referencia_id=None, referencia_tipo=None,
                   data_lancamento=None, usuario_id=None):
    """Lança uma receita no financeiro"""
    f = Financeiro(
        data=data_lancamento or date.today(),
        tipo='receita',
        categoria=categoria,
        descricao=descricao,
        valor=valor,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        usuario_id=usuario_id
    )
    db.session.add(f)
    return f


def lancar_despesa(valor, descricao, categoria='outro',
                   referencia_id=None, referencia_tipo=None,
                   data_lancamento=None, usuario_id=None):
    """Lança uma despesa no financeiro"""
    f = Financeiro(
        data=data_lancamento or date.today(),
        tipo='despesa',
        categoria=categoria,
        descricao=descricao,
        valor=valor,
        referencia_id=referencia_id,
        referencia_tipo=referencia_tipo,
        usuario_id=usuario_id
    )
    db.session.add(f)
    return f


def gerar_conta_receber(venda_id, cliente_id, valor, prazo_dias=0,
                        descricao=None, data_base=None):
    """Gera conta a receber para uma venda"""
    data_base = data_base or date.today()
    vencimento = data_base + timedelta(days=prazo_dias)

    conta = ContaReceber(
        venda_id=venda_id,
        cliente_id=cliente_id,
        descricao=descricao or f'Venda #{venda_id}',
        valor=valor,
        vencimento=vencimento,
        status='pago' if prazo_dias == 0 else 'pendente'
    )
    if prazo_dias == 0:
        conta.data_pagamento = data_base
        conta.valor_pago = valor

    db.session.add(conta)
    return conta


def gerar_conta_pagar(compra_id, fornecedor_id, valor, prazo_dias=0,
                      descricao=None, categoria='materia_prima', data_base=None):
    """Gera conta a pagar para uma compra"""
    data_base = data_base or date.today()
    vencimento = data_base + timedelta(days=prazo_dias)

    conta = ContaPagar(
        compra_id=compra_id,
        fornecedor_id=fornecedor_id,
        descricao=descricao or f'Compra #{compra_id}',
        valor=valor,
        vencimento=vencimento,
        status='pago' if prazo_dias == 0 else 'pendente',
        categoria=categoria
    )
    if prazo_dias == 0:
        conta.data_pagamento = data_base
        conta.valor_pago = valor

    db.session.add(conta)
    return conta


def get_resumo_financeiro(mes=None, ano=None):
    """Retorna resumo financeiro do período"""
    from sqlalchemy import extract, func

    query = Financeiro.query
    if mes and ano:
        query = query.filter(
            extract('month', Financeiro.data) == mes,
            extract('year', Financeiro.data) == ano
        )
    elif ano:
        query = query.filter(extract('year', Financeiro.data) == ano)

    receitas = query.filter_by(tipo='receita').with_entities(
        func.sum(Financeiro.valor)
    ).scalar() or 0.0

    despesas = query.filter_by(tipo='despesa').with_entities(
        func.sum(Financeiro.valor)
    ).scalar() or 0.0

    return {
        'receitas': round(receitas, 2),
        'despesas': round(despesas, 2),
        'saldo': round(receitas - despesas, 2),
    }


def get_contas_vencidas():
    """Retorna alertas de contas vencidas"""
    hoje = date.today()
    alertas = []

    receber = ContaReceber.query.filter(
        ContaReceber.status == 'pendente',
        ContaReceber.vencimento < hoje
    ).all()
    for c in receber:
        alertas.append({
            'tipo': 'receber',
            'descricao': c.descricao,
            'valor': c.valor,
            'vencimento': c.vencimento,
            'dias_atraso': (hoje - c.vencimento).days
        })

    pagar = ContaPagar.query.filter(
        ContaPagar.status == 'pendente',
        ContaPagar.vencimento < hoje
    ).all()
    for c in pagar:
        alertas.append({
            'tipo': 'pagar',
            'descricao': c.descricao,
            'valor': c.valor,
            'vencimento': c.vencimento,
            'dias_atraso': (hoje - c.vencimento).days
        })

    return alertas
