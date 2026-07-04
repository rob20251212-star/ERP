
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from extensions import db
from models.fornecedor import Fornecedor

fornecedores_bp = Blueprint('fornecedores', __name__)


@fornecedores_bp.route('/')
@login_required
def index():
    busca = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    query = Fornecedor.query.filter_by(ativo=True)
    if busca:
        query = query.filter(Fornecedor.nome.ilike(f'%{busca}%'))
    fornecedores = query.order_by(Fornecedor.nome).paginate(page=page, per_page=20)
    return render_template('fornecedores/index.html', fornecedores=fornecedores, busca=busca)


@fornecedores_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        f = Fornecedor(
            nome=request.form['nome'].strip().upper(),
            cnpj=request.form.get('cnpj', '').strip(),
            telefone=request.form.get('telefone', '').strip(),
            email=request.form.get('email', '').strip(),
            cidade=request.form.get('cidade', '').strip(),
            estado=request.form.get('estado', '').strip().upper(),
            tipo=request.form.get('tipo', 'outro'),
            observacoes=request.form.get('observacoes', '').strip(),
        )
        db.session.add(f)
        db.session.commit()
        flash(f'Fornecedor {f.nome} cadastrado!', 'success')
        return redirect(url_for('fornecedores.index'))
    return render_template('fornecedores/form.html', fornecedor=None, titulo='Novo Fornecedor')


@fornecedores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    f = Fornecedor.query.get_or_404(id)
    if request.method == 'POST':
        f.nome = request.form['nome'].strip().upper()
        f.cnpj = request.form.get('cnpj', '').strip()
        f.telefone = request.form.get('telefone', '').strip()
        f.email = request.form.get('email', '').strip()
        f.cidade = request.form.get('cidade', '').strip()
        f.estado = request.form.get('estado', '').strip().upper()
        f.tipo = request.form.get('tipo', 'outro')
        f.observacoes = request.form.get('observacoes', '').strip()
        db.session.commit()
        flash(f'Fornecedor {f.nome} atualizado!', 'success')
        return redirect(url_for('fornecedores.index'))
    return render_template('fornecedores/form.html', fornecedor=f, titulo='Editar Fornecedor')


@fornecedores_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    f = Fornecedor.query.get_or_404(id)
    f.ativo = False
    db.session.commit()
    flash(f'Fornecedor {f.nome} removido.', 'warning')
    return redirect(url_for('fornecedores.index'))


@fornecedores_bp.route('/api/buscar')
@login_required
def api_buscar():
    q = request.args.get('q', '')
    fornecedores = Fornecedor.query.filter(
        Fornecedor.nome.ilike(f'%{q}%'), Fornecedor.ativo == True
    ).limit(10).all()
    return jsonify([{'id': f.id, 'nome': f.nome, 'tipo': f.tipo} for f in fornecedores])
