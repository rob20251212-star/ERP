from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.estoque import MovimentacaoEstoque
from models.materia_prima import MateriaPrima
from models.produto import ProdutoFinal
from services.estoque_service import get_alertas_estoque

estoque_bp = Blueprint('estoque', __name__)


@estoque_bp.route('/')
@login_required
def index():
    mps = MateriaPrima.query.order_by(MateriaPrima.id).all()
    produto = ProdutoFinal.query.first()
    alertas = get_alertas_estoque()
    return render_template('estoque/index.html', mps=mps, produto=produto, alertas=alertas)


@estoque_bp.route('/historico')
@login_required
def historico():
    page = request.args.get('page', 1, type=int)
    tipo_filtro = request.args.get('tipo', '')
    mp_id = request.args.get('mp_id', '')

    query = MovimentacaoEstoque.query.order_by(
        MovimentacaoEstoque.data.desc(), MovimentacaoEstoque.id.desc()
    )
    if tipo_filtro:
        query = query.filter_by(tipo=tipo_filtro)
    if mp_id:
        query = query.filter_by(materia_prima_id=int(mp_id))

    movs = query.paginate(page=page, per_page=30)
    mps = MateriaPrima.query.order_by(MateriaPrima.nome).all()
    return render_template('estoque/historico.html', movs=movs, mps=mps,
                           tipo_filtro=tipo_filtro, mp_id=mp_id)


@estoque_bp.route('/ajuste', methods=['GET', 'POST'])
@login_required
def ajuste():
    """Ajuste manual de estoque (inventário)"""
    mps = MateriaPrima.query.order_by(MateriaPrima.nome).all()
    produto = ProdutoFinal.query.first()

    if request.method == 'POST':
        tipo_item = request.form.get('tipo_item')  # mp | produto
        mp_id = request.form.get('mp_id')
        novo_saldo = float(request.form.get('novo_saldo', 0) or 0)
        motivo = request.form.get('motivo', 'ajuste inventário')

        if tipo_item == 'mp' and mp_id:
            mp = MateriaPrima.query.get(int(mp_id))
            diferenca = novo_saldo - mp.estoque_atual
            tipo = 'entrada' if diferenca >= 0 else 'saida'

            mov = MovimentacaoEstoque(
                tipo=tipo,
                materia_prima_id=mp.id,
                quantidade=abs(diferenca),
                saldo_antes=mp.estoque_atual,
                saldo_depois=novo_saldo,
                motivo='ajuste',
                usuario_id=current_user.id,
                observacoes=motivo
            )
            mp.estoque_atual = novo_saldo
            db.session.add(mov)

        elif tipo_item == 'produto' and produto:
            diferenca = novo_saldo - produto.estoque_atual
            tipo = 'entrada' if diferenca >= 0 else 'saida'

            mov = MovimentacaoEstoque(
                tipo=tipo,
                produto_id=produto.id,
                quantidade=abs(diferenca),
                saldo_antes=produto.estoque_atual,
                saldo_depois=novo_saldo,
                motivo='ajuste',
                usuario_id=current_user.id,
                observacoes=motivo
            )
            produto.estoque_atual = novo_saldo
            db.session.add(mov)

        db.session.commit()
        flash('Ajuste de estoque realizado!', 'success')
        return redirect(url_for('estoque.index'))

    return render_template('estoque/ajuste.html', mps=mps, produto=produto)
