from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.producao import Producao
from models.materia_prima import MateriaPrima
from models.produto import ProdutoFinal
from services.estoque_service import saida_mp, entrada_produto
from services.financeiro_service import lancar_despesa
from datetime import date, datetime

producao_bp = Blueprint('producao', __name__)

# Consumo padrão por saco de produto (extraído da planilha)
CONSUMO_POR_SACO = {
    'celulosico': 12.5,  # kg
    'celugel':    7.5,   # kg
    'fibra':      5.0,   # kg
    'embalagem':  1.0,   # un
    'adesivo':    1.0,   # un
}


@producao_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    producoes = Producao.query.order_by(
        Producao.data.desc(), Producao.id.desc()
    ).paginate(page=page, per_page=20)
    return render_template('producao/index.html', producoes=producoes)


@producao_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    mps = {mp.tipo: mp for mp in MateriaPrima.query.all()}
    produto = ProdutoFinal.query.first()

    if request.method == 'POST':
        qtd = int(request.form['quantidade_sacos'])
        data_prod = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        lote = request.form.get('lote', '').strip()
        responsavel = request.form.get('responsavel', '').strip()

        # Verificar estoque das MPs
        erros = []
        for tipo, kg_por_saco in CONSUMO_POR_SACO.items():
            mp = mps.get(tipo)
            if not mp:
                erros.append(f'{tipo} não cadastrado')
                continue
            consumo_total = kg_por_saco * qtd if mp.tipo not in ('embalagem', 'adesivo') else qtd
            # Para celulosico/celugel/fibra: consumo em kg, estoque em sacos
            if mp.tipo in ('celulosico', 'celugel', 'fibra'):
                consumo_sacos = consumo_total / mp.peso_saco_kg
                if mp.estoque_atual < consumo_sacos:
                    erros.append(f'Estoque insuficiente de {mp.nome}: '
                                 f'necessário {consumo_sacos:.1f} sacos, disponível {mp.estoque_atual:.1f}')
            else:
                if mp.estoque_atual < consumo_total:
                    erros.append(f'Estoque insuficiente de {mp.nome}: '
                                 f'necessário {consumo_total} un, disponível {mp.estoque_atual:.0f}')

        if erros:
            for erro in erros:
                flash(erro, 'danger')
            return render_template('producao/form.html', mps=mps, produto=produto,
                                   titulo='Nova Produção', hoje=date.today().isoformat(),
                                   consumo=CONSUMO_POR_SACO)

        # Calcular custo da produção
        custo_por_saco = produto.custo_calculado if produto else 0
        custo_total = round(custo_por_saco * qtd, 2)

        # Criar registro de produção
        producao = Producao(
            data=data_prod,
            lote=lote or f'LOTE-{data_prod.strftime("%Y%m%d")}-{qtd}',
            quantidade_sacos=qtd,
            responsavel=responsavel,
            custo_total=custo_total,
            custo_por_saco=custo_por_saco,
            observacoes=request.form.get('observacoes', '').strip(),
            criado_por=current_user.id,
            consumo_celulosico_kg=CONSUMO_POR_SACO['celulosico'] * qtd,
            consumo_celugel_kg=CONSUMO_POR_SACO['celugel'] * qtd,
            consumo_fibra_kg=CONSUMO_POR_SACO['fibra'] * qtd,
            consumo_embalagem_un=qtd,
            consumo_adesivo_un=qtd,
        )
        db.session.add(producao)
        db.session.flush()

        # Baixar MPs automaticamente
        for tipo, kg_por_saco in CONSUMO_POR_SACO.items():
            mp = mps.get(tipo)
            if not mp:
                continue
            if mp.tipo in ('celulosico', 'celugel', 'fibra'):
                consumo_sacos = (kg_por_saco * qtd) / mp.peso_saco_kg
                saida_mp(mp.id, consumo_sacos, motivo='producao',
                         referencia_id=producao.id, referencia_tipo='producao',
                         usuario_id=current_user.id,
                         obs=f'Produção lote {producao.lote}')
            else:
                saida_mp(mp.id, qtd, motivo='producao',
                         referencia_id=producao.id, referencia_tipo='producao',
                         usuario_id=current_user.id,
                         obs=f'Produção lote {producao.lote}')

        # Adicionar produto acabado ao estoque
        entrada_produto(qtd, motivo='producao',
                        referencia_id=producao.id, referencia_tipo='producao',
                        usuario_id=current_user.id,
                        obs=f'Produção lote {producao.lote}')

        # Lançar custo no financeiro
        lancar_despesa(
            valor=custo_total,
            descricao=f'Custo produção lote {producao.lote} - {qtd} sacos',
            categoria='producao',
            referencia_id=producao.id,
            referencia_tipo='producao',
            data_lancamento=data_prod,
            usuario_id=current_user.id
        )

        db.session.commit()
        flash(f'Produção registrada! {qtd} sacos adicionados ao estoque. '
              f'MPs baixadas automaticamente. Custo: R$ {custo_total:,.2f}', 'success')
        return redirect(url_for('producao.index'))

    return render_template('producao/form.html', mps=mps, produto=produto,
                           titulo='Nova Produção', hoje=date.today().isoformat(),
                           consumo=CONSUMO_POR_SACO)


@producao_bp.route('/<int:id>/detalhe')
@login_required
def detalhe(id):
    producao = Producao.query.get_or_404(id)
    return render_template('producao/detalhe.html', producao=producao,
                           consumo=CONSUMO_POR_SACO)
