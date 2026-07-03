from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from extensions import db
from models.vendedor import Vendedor
from sqlalchemy import func

vendedores_bp = Blueprint('vendedores', __name__)


@vendedores_bp.route('/')
@login_required
def index():
    vendedores = Vendedor.query.filter_by(ativo=True).order_by(Vendedor.nome).all()
    return render_template('vendedores/index.html', vendedores=vendedores)


@vendedores_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        v = Vendedor(
            nome=request.form['nome'].strip().upper(),
            telefone=request.form.get('telefone', '').strip(),
            email=request.form.get('email', '').strip(),
            cidade=request.form.get('cidade', '').strip(),
            estado=request.form.get('estado', '').strip().upper(),
            comissao_pct=float(request.form.get('comissao_pct', 0) or 0),
        )
        db.session.add(v)
        db.session.commit()
        flash(f'Vendedor {v.nome} cadastrado!', 'success')
        return redirect(url_for('vendedores.index'))
    return render_template('vendedores/form.html', vendedor=None, titulo='Novo Vendedor')


@vendedores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    v = Vendedor.query.get_or_404(id)
    if request.method == 'POST':
        v.nome = request.form['nome'].strip().upper()
        v.telefone = request.form.get('telefone', '').strip()
        v.email = request.form.get('email', '').strip()
        v.cidade = request.form.get('cidade', '').strip()
        v.estado = request.form.get('estado', '').strip().upper()
        v.comissao_pct = float(request.form.get('comissao_pct', 0) or 0)
        db.session.commit()
        flash(f'Vendedor {v.nome} atualizado!', 'success')
        return redirect(url_for('vendedores.index'))
    return render_template('vendedores/form.html', vendedor=v, titulo='Editar Vendedor')


@vendedores_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    v = Vendedor.query.get_or_404(id)
    v.ativo = False
    db.session.commit()
    flash(f'Vendedor {v.nome} removido.', 'warning')
    return redirect(url_for('vendedores.index'))


@vendedores_bp.route('/<int:id>/detalhe')
@login_required
def detalhe(id):
    v = Vendedor.query.get_or_404(id)
    from models.venda import Venda
    vendas = Venda.query.filter_by(vendedor_id=id).order_by(Venda.data.desc()).limit(50).all()
    return render_template('vendedores/detalhe.html', vendedor=v, vendas=vendas)
