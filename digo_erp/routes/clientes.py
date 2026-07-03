from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from extensions import db
from models.cliente import Cliente

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/')
@login_required
def index():
    busca = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    query = Cliente.query.filter_by(ativo=True)
    if busca:
        query = query.filter(Cliente.nome.ilike(f'%{busca}%'))
    clientes = query.order_by(Cliente.nome).paginate(page=page, per_page=20)
    return render_template('clientes/index.html', clientes=clientes, busca=busca)


@clientes_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        cliente = Cliente(
            nome=request.form['nome'].strip().upper(),
            cpf_cnpj=request.form.get('cpf_cnpj', '').strip(),
            telefone=request.form.get('telefone', '').strip(),
            email=request.form.get('email', '').strip(),
            cidade=request.form.get('cidade', '').strip(),
            estado=request.form.get('estado', '').strip().upper(),
            endereco=request.form.get('endereco', '').strip(),
            observacoes=request.form.get('observacoes', '').strip(),
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f'Cliente {cliente.nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes.index'))
    return render_template('clientes/form.html', cliente=None, titulo='Novo Cliente')


@clientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nome = request.form['nome'].strip().upper()
        cliente.cpf_cnpj = request.form.get('cpf_cnpj', '').strip()
        cliente.telefone = request.form.get('telefone', '').strip()
        cliente.email = request.form.get('email', '').strip()
        cliente.cidade = request.form.get('cidade', '').strip()
        cliente.estado = request.form.get('estado', '').strip().upper()
        cliente.endereco = request.form.get('endereco', '').strip()
        cliente.observacoes = request.form.get('observacoes', '').strip()
        db.session.commit()
        flash(f'Cliente {cliente.nome} atualizado!', 'success')
        return redirect(url_for('clientes.index'))
    return render_template('clientes/form.html', cliente=cliente, titulo='Editar Cliente')


@clientes_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    cliente = Cliente.query.get_or_404(id)
    cliente.ativo = False
    db.session.commit()
    flash(f'Cliente {cliente.nome} removido.', 'warning')
    return redirect(url_for('clientes.index'))


@clientes_bp.route('/<int:id>/detalhe')
@login_required
def detalhe(id):
    cliente = Cliente.query.get_or_404(id)
    from models.venda import Venda
    vendas = Venda.query.filter_by(cliente_id=id).order_by(Venda.data.desc()).all()
    return render_template('clientes/detalhe.html', cliente=cliente, vendas=vendas)


@clientes_bp.route('/api/buscar')
@login_required
def api_buscar():
    q = request.args.get('q', '')
    clientes = Cliente.query.filter(
        Cliente.nome.ilike(f'%{q}%'), Cliente.ativo == True
    ).limit(10).all()
    return jsonify([{'id': c.id, 'nome': c.nome, 'cidade': c.cidade} for c in clientes])
