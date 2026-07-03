from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func, extract
from extensions import db
from models.venda import Venda, ContaReceber, ContaPagar
from models.producao import Producao
from models.produto import ProdutoFinal
from models.materia_prima import MateriaPrima
from models.financeiro import Financeiro
from models.cliente import Cliente
from models.vendedor import Vendedor
from services.estoque_service import get_alertas_estoque
from services.financeiro_service import get_contas_vencidas, get_resumo_financeiro
from datetime import date, datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # KPIs de Produção
    prod_hoje = db.session.query(func.sum(Producao.quantidade_sacos)).filter(
        Producao.data == hoje
    ).scalar() or 0

    prod_mes = db.session.query(func.sum(Producao.quantidade_sacos)).filter(
        extract('month', Producao.data) == mes_atual,
        extract('year', Producao.data) == ano_atual
    ).scalar() or 0

    prod_ano = db.session.query(func.sum(Producao.quantidade_sacos)).filter(
        extract('year', Producao.data) == ano_atual
    ).scalar() or 0

    # KPIs de Vendas
    vendas_mes = db.session.query(func.sum(Venda.valor_liquido)).filter(
        extract('month', Venda.data) == mes_atual,
        extract('year', Venda.data) == ano_atual
    ).scalar() or 0

    vendas_ano = db.session.query(func.sum(Venda.valor_liquido)).filter(
        extract('year', Venda.data) == ano_atual
    ).scalar() or 0

    qtd_vendas_mes = db.session.query(func.sum(Venda.quantidade_sacos)).filter(
        extract('month', Venda.data) == mes_atual,
        extract('year', Venda.data) == ano_atual
    ).scalar() or 0

    # Lucro
    lucro_mes = db.session.query(func.sum(Venda.lucro)).filter(
        extract('month', Venda.data) == mes_atual,
        extract('year', Venda.data) == ano_atual
    ).scalar() or 0

    lucro_ano = db.session.query(func.sum(Venda.lucro)).filter(
        extract('year', Venda.data) == ano_atual
    ).scalar() or 0

    # Financeiro do mês
    resumo_fin = get_resumo_financeiro(mes=mes_atual, ano=ano_atual)

    # Estoque
    produto = ProdutoFinal.query.first()
    mps = MateriaPrima.query.all()
    valor_estoque_mp = sum(mp.valor_em_estoque for mp in mps)
    valor_estoque_produto = produto.valor_em_estoque if produto else 0

    # Contagens
    total_clientes = Cliente.query.filter_by(ativo=True).count()
    total_vendedores = Vendedor.query.filter_by(ativo=True).count()

    # Últimas vendas
    ultimas_vendas = Venda.query.order_by(Venda.data.desc(), Venda.id.desc()).limit(10).all()

    # Últimas produções
    ultimas_producoes = Producao.query.order_by(Producao.data.desc(), Producao.id.desc()).limit(5).all()

    # Alertas
    alertas_estoque = get_alertas_estoque()
    alertas_contas = get_contas_vencidas()

    # Dados para gráfico de vendas mensais (ano atual)
    vendas_por_mes = []
    for m in range(1, 13):
        val = db.session.query(func.sum(Venda.valor_liquido)).filter(
            extract('month', Venda.data) == m,
            extract('year', Venda.data) == ano_atual
        ).scalar() or 0
        vendas_por_mes.append(round(float(val), 2))

    # Dados para gráfico de produção mensais
    producao_por_mes = []
    for m in range(1, 13):
        val = db.session.query(func.sum(Producao.quantidade_sacos)).filter(
            extract('month', Producao.data) == m,
            extract('year', Producao.data) == ano_atual
        ).scalar() or 0
        producao_por_mes.append(int(val))

    return render_template('dashboard/index.html',
        # KPIs Produção
        prod_hoje=prod_hoje,
        prod_mes=prod_mes,
        prod_ano=prod_ano,
        # KPIs Vendas
        vendas_mes=vendas_mes,
        vendas_ano=vendas_ano,
        qtd_vendas_mes=qtd_vendas_mes,
        lucro_mes=lucro_mes,
        lucro_ano=lucro_ano,
        # Financeiro
        resumo_fin=resumo_fin,
        # Estoque
        produto=produto,
        mps=mps,
        valor_estoque_mp=valor_estoque_mp,
        valor_estoque_produto=valor_estoque_produto,
        # Contagens
        total_clientes=total_clientes,
        total_vendedores=total_vendedores,
        # Listas
        ultimas_vendas=ultimas_vendas,
        ultimas_producoes=ultimas_producoes,
        # Alertas
        alertas_estoque=alertas_estoque,
        alertas_contas=alertas_contas,
        total_alertas=len(alertas_estoque) + len(alertas_contas),
        # Gráficos
        vendas_por_mes=vendas_por_mes,
        producao_por_mes=producao_por_mes,
        mes_atual=mes_atual,
        ano_atual=ano_atual,
    )
