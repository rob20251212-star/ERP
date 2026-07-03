from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.financeiro import Financeiro
from models.venda import ContaReceber, ContaPagar
from services.financeiro_service import (
    lancar_receita, lancar_despesa,
    get_resumo_financeiro, get_contas_vencidas
)
from sqlalchemy import func, extract
from datetime import date, datetime

financeiro_bp = Blueprint('financeiro', __name__)


@financeiro_bp.route('/')
@login_required
def index():
    hoje = date.today()
    mes = request.args.get('mes', hoje.month, type=int)
    ano = request.args.get('ano', hoje.year, type=int)

    # Fluxo de caixa do mês
    lancamentos = Financeiro.query.filter(
        extract('month', Financeiro.data) == mes,
        extract('year', Financeiro.data) == ano
    ).order_by(Financeiro.data.desc()).all()

    resumo = get_resumo_financeiro(mes=mes, ano=ano)
    resumo_ano = get_resumo_financeiro(ano=ano)

    # Contas a receber pendentes
    contas_receber = ContaReceber.query.filter(
        ContaReceber.status.in_(['pendente', 'parcial'])
    ).order_by(ContaReceber.vencimento).all()

    # Contas a pagar pendentes
    contas_pagar = ContaPagar.query.filter(
        ContaPagar.status.in_(['pendente'])
    ).order_by(ContaPagar.vencimento).all()

    # Alertas de vencimento
    alertas = get_contas_vencidas()

    # Saldo por dia para gráfico
    dias_saldo = []
    for lanc in sorted(lancamentos, key=lambda x: x.data):
        pass

    return render_template('financeiro/index.html',
                           lancamentos=lancamentos,
                           resumo=resumo,
                           resumo_ano=resumo_ano,
                           contas_receber=contas_receber,
                           contas_pagar=contas_pagar,
                           alertas=alertas,
                           mes=mes, ano=ano)


@financeiro_bp.route('/lancamento', methods=['GET', 'POST'])
@login_required
def novo_lancamento():
    """Lançamento manual de receita ou despesa"""
    if request.method == 'POST':
        tipo = request.form['tipo']
        valor = float(request.form['valor'])
        data_lanc = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        categoria = request.form.get('categoria', 'outro')
        descricao = request.form.get('descricao', '').strip()

        if tipo == 'receita':
            lancar_receita(valor, descricao, categoria,
                           data_lancamento=data_lanc, usuario_id=current_user.id)
        else:
            lancar_despesa(valor, descricao, categoria,
                           data_lancamento=data_lanc, usuario_id=current_user.id)

        db.session.commit()
        flash(f'{tipo.capitalize()} de R$ {valor:,.2f} lançada!', 'success')
        return redirect(url_for('financeiro.index'))

    return render_template('financeiro/lancamento.html', hoje=date.today().isoformat())


@financeiro_bp.route('/pagar-conta/<int:id>', methods=['POST'])
@login_required
def pagar_conta(id):
    conta = ContaPagar.query.get_or_404(id)
    valor_pago = float(request.form.get('valor_pago', conta.valor) or conta.valor)
    conta.status = 'pago'
    conta.data_pagamento = date.today()
    conta.valor_pago = valor_pago

    lancar_despesa(
        valor=valor_pago,
        descricao=conta.descricao or f'Conta pagar #{conta.id}',
        categoria=conta.categoria or 'outro',
        referencia_id=conta.id,
        referencia_tipo='conta_pagar',
        data_lancamento=date.today(),
        usuario_id=current_user.id
    )
    db.session.commit()
    flash(f'Pagamento de R$ {valor_pago:,.2f} registrado!', 'success')
    return redirect(url_for('financeiro.index'))


@financeiro_bp.route('/receber-conta/<int:id>', methods=['POST'])
@login_required
def receber_conta(id):
    conta = ContaReceber.query.get_or_404(id)
    valor_pago = float(request.form.get('valor_pago', conta.valor) or conta.valor)
    conta.status = 'pago'
    conta.data_pagamento = date.today()
    conta.valor_pago = valor_pago

    lancar_receita(
        valor=valor_pago,
        descricao=conta.descricao or f'Recebimento #{conta.id}',
        categoria='venda',
        referencia_id=conta.id,
        referencia_tipo='conta_receber',
        data_lancamento=date.today(),
        usuario_id=current_user.id
    )
    db.session.commit()
    flash(f'Recebimento de R$ {valor_pago:,.2f} registrado!', 'success')
    return redirect(url_for('financeiro.index'))
