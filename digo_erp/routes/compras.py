from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, datetime, timedelta
from extensions import db
from models.compra import Compra
from models.materia_prima import MateriaPrima
from models.fornecedor import Fornecedor
from services.estoque_service import entrada_mp, saida_mp, atualizar_custo_medio
from services.financeiro_service import gerar_conta_pagar
from services.custo_service import recalcular_custo_produto

compras_bp = Blueprint('compras', __name__)


@compras_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    busca = request.args.get('q', '')
    query = Compra.query.order_by(Compra.data.desc(), Compra.id.desc())
    if busca:
        query = query.join(MateriaPrima).filter(MateriaPrima.nome.ilike(f'%{busca}%'))
    compras = query.paginate(page=page, per_page=20)
    return render_template('compras/index.html', compras=compras, busca=busca)


@compras_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    mps = MateriaPrima.query.order_by(MateriaPrima.nome).all()
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()

    if request.method == 'POST':
        mp_id = int(request.form['materia_prima_id'])
        qtd_sacos = float(request.form['quantidade_sacos'])
        preco_unit = float(request.form.get('preco_unitario', 0) or 0)
        frete_total = float(request.form.get('frete_total', 0) or 0)
        frete_saco = round(frete_total / qtd_sacos, 4) if qtd_sacos else 0
        total = round(qtd_sacos * preco_unit, 2)
        total_com_frete = round(total + frete_total, 2)
        prazo = int(request.form.get('prazo_pagamento', 0) or 0)
        data_compra = datetime.strptime(request.form['data'], '%Y-%m-%d').date()

        fornecedor_id = request.form.get('fornecedor_id') or None
        fornecedor_nome = request.form.get('fornecedor_nome', '').strip()
        if not fornecedor_id and fornecedor_nome:
            fornecedor = Fornecedor.query.filter(
                Fornecedor.ativo == True,
                func.lower(Fornecedor.nome) == fornecedor_nome.lower()
            ).first()
            if not fornecedor:
                fornecedor = Fornecedor.query.filter(
                    Fornecedor.ativo == True,
                    Fornecedor.nome.ilike(f'%{fornecedor_nome}%')
                ).first()
            if not fornecedor:
                fornecedor = Fornecedor(
                    nome=fornecedor_nome.upper(),
                    tipo='outro',
                    ativo=True
                )
                db.session.add(fornecedor)
                db.session.flush()
            fornecedor_id = fornecedor.id

        if not fornecedor_id:
            flash('Fornecedor não informado. Digite o nome do fornecedor.', 'danger')
            return render_template('compras/form.html', mps=mps, fornecedores=fornecedores,
                                   compra=None, titulo='Nova Compra', hoje=date.today().isoformat())

        compra = Compra(
            data=data_compra,
            fornecedor_id=fornecedor_id,
            materia_prima_id=mp_id,
            quantidade_sacos=qtd_sacos,
            preco_unitario=preco_unit,
            frete_total=frete_total,
            frete_por_saco=frete_saco,
            total=total,
            total_com_frete=total_com_frete,
            numero_nf=request.form.get('numero_nf', '').strip(),
            prazo_pagamento=prazo,
            observacoes=request.form.get('observacoes', '').strip(),
            criado_por=current_user.id
        )
        db.session.add(compra)
        db.session.flush()  # get compra.id

        # 1. Atualizar custo médio da MP
        mp = MateriaPrima.query.get(mp_id)
        custo_novo_saco = preco_unit + frete_saco
        atualizar_custo_medio(mp, qtd_sacos, custo_novo_saco)

        # 2. Não sobrescrever o frete da matéria-prima no cadastro mestre
        #    O frete deve ser mantido no registro de compra, não no valor exibido em Matérias-Primas.

        # 3. Entrada no estoque
        entrada_mp(mp_id, qtd_sacos, motivo='compra',
                   referencia_id=compra.id, referencia_tipo='compra',
                   usuario_id=current_user.id)

        # 4. Gerar conta a pagar
        gerar_conta_pagar(
            compra_id=compra.id,
            fornecedor_id=compra.fornecedor_id,
            valor=total_com_frete,
            prazo_dias=prazo,
            descricao=f'Compra {mp.nome} - NF {compra.numero_nf or "s/n"}',
            categoria='materia_prima',
            data_base=data_compra
        )

        # 5. Recalcular custo do produto
        recalcular_custo_produto()

        db.session.commit()
        flash(f'Compra registrada! Estoque de {mp.nome} atualizado automaticamente.', 'success')
        return redirect(url_for('compras.index'))

    return render_template('compras/form.html', mps=mps, fornecedores=fornecedores,
                           compra=None, titulo='Nova Compra', hoje=date.today().isoformat())


@compras_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    compra = Compra.query.get_or_404(id)
    mps = MateriaPrima.query.order_by(MateriaPrima.nome).all()
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()

    if request.method == 'POST':
        mp_id = int(request.form['materia_prima_id'])
        qtd_sacos = float(request.form['quantidade_sacos'])
        preco_unit = float(request.form.get('preco_unitario', 0) or 0)
        frete_total = float(request.form.get('frete_total', 0) or 0)
        frete_saco = round(frete_total / qtd_sacos, 4) if qtd_sacos else 0
        total = round(qtd_sacos * preco_unit, 2)
        total_com_frete = round(total + frete_total, 2)
        prazo = int(request.form.get('prazo_pagamento', 0) or 0)
        data_compra = datetime.strptime(request.form['data'], '%Y-%m-%d').date()

        fornecedor_id = request.form.get('fornecedor_id') or None
        fornecedor_nome = request.form.get('fornecedor_nome', '').strip()
        if not fornecedor_id and fornecedor_nome:
            fornecedor = Fornecedor.query.filter(
                Fornecedor.ativo == True,
                func.lower(Fornecedor.nome) == fornecedor_nome.lower()
            ).first()
            if not fornecedor:
                fornecedor = Fornecedor.query.filter(
                    Fornecedor.ativo == True,
                    Fornecedor.nome.ilike(f'%{fornecedor_nome}%')
                ).first()
            if not fornecedor:
                fornecedor = Fornecedor(
                    nome=fornecedor_nome.upper(),
                    tipo='outro',
                    ativo=True
                )
                db.session.add(fornecedor)
                db.session.flush()
            fornecedor_id = fornecedor.id

        if not fornecedor_id:
            flash('Fornecedor não informado. Digite o nome do fornecedor.', 'danger')
            return render_template('compras/form.html', mps=mps, fornecedores=fornecedores,
                                   compra=compra, titulo='Editar Compra', hoje=date.today().isoformat())

        # Ajusta estoque conforme diferença de quantidade ou mudança de matéria-prima
        atualizar_custo = 0.0
        if compra.materia_prima_id != mp_id:
            if compra.quantidade_sacos:
                saida_mp(compra.materia_prima_id, compra.quantidade_sacos, motivo='compra_ajuste',
                         referencia_id=compra.id, referencia_tipo='compra', usuario_id=current_user.id,
                         obs=f'Reversão de compra #{compra.id}')
            if qtd_sacos:
                entrada_mp(mp_id, qtd_sacos, motivo='compra', referencia_id=compra.id,
                           referencia_tipo='compra', usuario_id=current_user.id,
                           obs=f'Ajuste de compra #{compra.id}')
                atualizar_custo = qtd_sacos
        else:
            dif = qtd_sacos - compra.quantidade_sacos
            if dif > 0:
                entrada_mp(mp_id, dif, motivo='compra_ajuste', referencia_id=compra.id,
                           referencia_tipo='compra', usuario_id=current_user.id,
                           obs=f'Ajuste de compra #{compra.id}')
                atualizar_custo = dif
            elif dif < 0:
                saida_mp(mp_id, abs(dif), motivo='compra_ajuste', referencia_id=compra.id,
                         referencia_tipo='compra', usuario_id=current_user.id,
                         obs=f'Ajuste de compra #{compra.id}')

        compra.data = data_compra
        compra.fornecedor_id = fornecedor_id
        compra.materia_prima_id = mp_id
        compra.quantidade_sacos = qtd_sacos
        compra.preco_unitario = preco_unit
        compra.frete_total = frete_total
        compra.frete_por_saco = frete_saco
        compra.total = total
        compra.total_com_frete = total_com_frete
        compra.numero_nf = request.form.get('numero_nf', '').strip()
        compra.prazo_pagamento = prazo
        compra.observacoes = request.form.get('observacoes', '').strip()

        mp = MateriaPrima.query.get(mp_id)
        if mp:
            if atualizar_custo > 0:
                atualizar_custo_medio(mp, atualizar_custo, preco_unit + frete_saco)

        if compra.conta_pagar:
            conta = compra.conta_pagar
            conta.valor = total_com_frete
            conta.descricao = f'Compra {mp.nome} - NF {compra.numero_nf or "s/n"}'
            conta.vencimento = data_compra + timedelta(days=prazo)
            conta.status = 'pago' if prazo == 0 else 'pendente'
            if prazo == 0:
                conta.data_pagamento = data_compra
                conta.valor_pago = total_com_frete
            elif conta.status != 'pago':
                conta.data_pagamento = None
                conta.valor_pago = 0.0
        else:
            gerar_conta_pagar(
                compra_id=compra.id,
                fornecedor_id=compra.fornecedor_id,
                valor=total_com_frete,
                prazo_dias=prazo,
                descricao=f'Compra {mp.nome} - NF {compra.numero_nf or "s/n"}',
                categoria='materia_prima',
                data_base=data_compra
            )

        recalcular_custo_produto()
        db.session.commit()
        flash('Compra atualizada com sucesso!', 'success')
        return redirect(url_for('compras.index'))

    return render_template('compras/form.html', mps=mps, fornecedores=fornecedores,
                           compra=compra, titulo='Editar Compra', hoje=compra.data.isoformat())


@compras_bp.route('/<int:id>/excluir', methods=['POST'])
@login_required
def excluir(id):
    compra = Compra.query.get_or_404(id)
    if compra.conta_pagar:
        db.session.delete(compra.conta_pagar)
    if compra.quantidade_sacos and compra.materia_prima_id:
        saida_mp(compra.materia_prima_id, compra.quantidade_sacos, motivo='compra_cancelada',
                 referencia_id=compra.id, referencia_tipo='compra', usuario_id=current_user.id,
                 obs=f'Compra cancelada #{compra.id}')
    db.session.delete(compra)
    db.session.commit()
    flash('Compra excluída com sucesso.', 'warning')
    return redirect(url_for('compras.index'))


@compras_bp.route('/<int:id>/detalhe')
@login_required
def detalhe(id):
    compra = Compra.query.get_or_404(id)
    return render_template('compras/detalhe.html', compra=compra)
