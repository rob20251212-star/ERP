from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.venda import Venda, ContaReceber
from models.cliente import Cliente
from models.vendedor import Vendedor
from models.produto import ProdutoFinal
from services.estoque_service import saida_produto
from services.financeiro_service import gerar_conta_receber, lancar_receita
from datetime import date, datetime

vendas_bp = Blueprint('vendas', __name__)


@vendas_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    busca = request.args.get('q', '')
    data_ini = request.args.get('data_ini', '')
    data_fim = request.args.get('data_fim', '')

    query = Venda.query.order_by(Venda.data.desc(), Venda.id.desc())

    if busca:
        query = query.join(Cliente).filter(Cliente.nome.ilike(f'%{busca}%'))
    if data_ini:
        query = query.filter(Venda.data >= datetime.strptime(data_ini, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Venda.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())

    vendas = query.paginate(page=page, per_page=20)
    return render_template('vendas/index.html', vendas=vendas, busca=busca,
                           data_ini=data_ini, data_fim=data_fim)


@vendas_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    vendedores = Vendedor.query.filter_by(ativo=True).order_by(Vendedor.nome).all()
    produto = ProdutoFinal.query.first()

    if request.method == 'POST':
        cliente_id = int(request.form['cliente_id'])
        vendedor_id = request.form.get('vendedor_id') or None
        qtd = int(request.form['quantidade_sacos'])
        preco_unit = float(request.form['preco_unitario'])
        desconto = float(request.form.get('desconto', 0) or 0)
        frete = float(request.form.get('frete', 0) or 0)
        tipo_frete = request.form.get('tipo_frete', 'FOB')
        forma_pagamento = request.form.get('forma_pagamento', 'A VISTA')
        prazo_dias = int(request.form.get('prazo_dias', 0) or 0)
        data_venda = datetime.strptime(request.form['data'], '%Y-%m-%d').date()

        # Verificar estoque
        if produto and produto.estoque_atual < qtd:
            flash(f'Estoque insuficiente! Disponível: {produto.estoque_atual:.0f} sacos', 'danger')
            return render_template('vendas/form.html', clientes=clientes, vendedores=vendedores,
                                   produto=produto, titulo='Nova Venda', hoje=date.today().isoformat())

        # Cálculos automáticos
        valor_bruto = round(qtd * preco_unit, 2)
        # Frete CIF = cobrado do cliente; FOB = custo do cliente mas não entra no total
        valor_liquido = round(valor_bruto - desconto + (frete if tipo_frete == 'CIF' else 0), 2)
        custo_total = round((produto.custo_calculado if produto else 0) * qtd, 2)
        lucro = round(valor_liquido - custo_total, 2)
        margem = round((lucro / valor_liquido * 100) if valor_liquido else 0, 2)

        # Comissão do vendedor
        comissao = 0.0
        if vendedor_id:
            vendedor = Vendedor.query.get(int(vendedor_id))
            if vendedor and vendedor.comissao_pct:
                comissao = round(valor_liquido * vendedor.comissao_pct / 100, 2)

        venda = Venda(
            data=data_venda,
            cliente_id=cliente_id,
            vendedor_id=int(vendedor_id) if vendedor_id else None,
            quantidade_sacos=qtd,
            preco_unitario=preco_unit,
            desconto=desconto,
            frete=frete,
            tipo_frete=tipo_frete,
            forma_pagamento=forma_pagamento,
            prazo_dias=prazo_dias,
            valor_bruto=valor_bruto,
            valor_liquido=valor_liquido,
            custo_total=custo_total,
            lucro=lucro,
            margem=margem,
            comissao=comissao,
            status_pagamento='pago' if prazo_dias == 0 else 'pendente',
            valor_pago=valor_liquido if prazo_dias == 0 else 0,
            observacoes=request.form.get('observacoes', '').strip(),
            criado_por=current_user.id
        )
        db.session.add(venda)
        db.session.flush()

        # 1. Baixar estoque do produto
        saida_produto(qtd, motivo='venda',
                      referencia_id=venda.id, referencia_tipo='venda',
                      usuario_id=current_user.id,
                      obs=f'Venda para {Cliente.query.get(cliente_id).nome}')

        # 2. Gerar conta a receber
        gerar_conta_receber(
            venda_id=venda.id,
            cliente_id=cliente_id,
            valor=valor_liquido,
            prazo_dias=prazo_dias,
            descricao=f'Venda {qtd} sacos - {forma_pagamento}',
            data_base=data_venda
        )

        # 3. Lançar receita (se à vista, lançar imediatamente)
        if prazo_dias == 0:
            lancar_receita(
                valor=valor_liquido,
                descricao=f'Venda {qtd} sacos p/ {Cliente.query.get(cliente_id).nome}',
                categoria='venda',
                referencia_id=venda.id,
                referencia_tipo='venda',
                data_lancamento=data_venda,
                usuario_id=current_user.id
            )

        db.session.commit()
        flash(f'Venda registrada! {qtd} sacos. Valor: R$ {valor_liquido:,.2f} | '
              f'Lucro: R$ {lucro:,.2f} | Margem: {margem:.1f}%', 'success')
        return redirect(url_for('vendas.index'))

    return render_template('vendas/form.html', clientes=clientes, vendedores=vendedores,
                           produto=produto, titulo='Nova Venda', hoje=date.today().isoformat())


@vendas_bp.route('/<int:id>/detalhe')
@login_required
def detalhe(id):
    venda = Venda.query.get_or_404(id)
    return render_template('vendas/detalhe.html', venda=venda)


@vendas_bp.route('/<int:id>/pagar', methods=['POST'])
@login_required
def registrar_pagamento(id):
    """Registra pagamento de uma venda a prazo"""
    venda = Venda.query.get_or_404(id)
    valor_pago = float(request.form.get('valor_pago', 0) or 0)

    venda.valor_pago = (venda.valor_pago or 0) + valor_pago
    if venda.valor_pago >= venda.valor_liquido:
        venda.status_pagamento = 'pago'
        if venda.conta_receber:
            venda.conta_receber.status = 'pago'
            venda.conta_receber.data_pagamento = date.today()
    else:
        venda.status_pagamento = 'parcial'

    # Lançar receita no financeiro
    lancar_receita(
        valor=valor_pago,
        descricao=f'Pagamento venda #{venda.id} - {venda.cliente.nome}',
        categoria='venda',
        referencia_id=venda.id,
        referencia_tipo='venda',
        data_lancamento=date.today(),
        usuario_id=current_user.id
    )

    db.session.commit()
    flash(f'Pagamento de R$ {valor_pago:,.2f} registrado!', 'success')
    return redirect(url_for('vendas.detalhe', id=id))


@vendas_bp.route('/api/preco-custo')
@login_required
def api_preco_custo():
    """Retorna custo atual do produto para cálculo em tempo real no formulário"""
    produto = ProdutoFinal.query.first()
    return jsonify({
        'custo': produto.custo_calculado if produto else 0,
        'estoque': produto.estoque_atual if produto else 0,
        'preco_padrao': produto.preco_venda_padrao if produto else 0,
    })
