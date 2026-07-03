from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from extensions import db
from models.materia_prima import MateriaPrima
from models.fornecedor import Fornecedor
from services.custo_service import recalcular_custo_produto, get_breakdown_custo

materias_primas_bp = Blueprint('materias_primas', __name__)


@materias_primas_bp.route('/')
@login_required
def index():
    mps = MateriaPrima.query.order_by(MateriaPrima.id).all()
    breakdown = get_breakdown_custo()
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()
    return render_template('materias_primas/index.html',
                           mps=mps, breakdown=breakdown, fornecedores=fornecedores)


@materias_primas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    mp = MateriaPrima.query.get_or_404(id)
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()

    if request.method == 'POST':
        mp.preco_saco = float(request.form.get('preco_saco', 0) or 0)
        mp.frete_saco = float(request.form.get('frete_saco', 0) or 0)
        mp.estoque_minimo = float(request.form.get('estoque_minimo', 0) or 0)
        mp.fornecedor_id = request.form.get('fornecedor_id') or None
        mp.observacoes = request.form.get('observacoes', '').strip()

        # Se embalagem/adesivo, atualizar quantidade de uso
        if mp.tipo in ('embalagem', 'adesivo'):
            mp.quantidade_uso_kg = 1.0

        db.session.commit()

        # Recalcular custo do produto automaticamente
        recalcular_custo_produto()

        flash(f'Preços de {mp.nome} atualizados! Custo do produto recalculado.', 'success')
        return redirect(url_for('materias_primas.index'))

    return render_template('materias_primas/form.html', mp=mp,
                           fornecedores=fornecedores, titulo=f'Editar {mp.nome}')


@materias_primas_bp.route('/api/custo')
@login_required
def api_custo():
    """API para retornar o custo atual calculado em tempo real"""
    breakdown = get_breakdown_custo()
    return jsonify(breakdown)


@materias_primas_bp.route('/produto-final', methods=['GET', 'POST'])
@login_required
def produto_final():
    from models.produto import ProdutoFinal
    produto = ProdutoFinal.query.first()
    breakdown = get_breakdown_custo()

    if request.method == 'POST':
        produto.margem_lucro_pct = float(request.form.get('margem_lucro_pct', 15) or 15)
        produto.estoque_minimo = float(request.form.get('estoque_minimo', 0) or 0)
        db.session.commit()
        recalcular_custo_produto()
        flash('Configurações do produto atualizadas e custo recalculado!', 'success')
        return redirect(url_for('materias_primas.produto_final'))

    return render_template('materias_primas/produto_final.html',
                           produto=produto, breakdown=breakdown)
