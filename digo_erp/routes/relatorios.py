from flask import Blueprint, render_template, request, send_file, jsonify
from flask_login import login_required
from extensions import db
from models.venda import Venda
from models.producao import Producao
from models.compra import Compra
from models.cliente import Cliente
from models.vendedor import Vendedor
from models.financeiro import Financeiro
from models.materia_prima import MateriaPrima
from sqlalchemy import func, extract
from datetime import datetime, date
import io, csv

relatorios_bp = Blueprint('relatorios', __name__)


def _parse_filtros():
    data_ini = request.args.get('data_ini', '')
    data_fim = request.args.get('data_fim', '')
    cliente_id = request.args.get('cliente_id', '')
    vendedor_id = request.args.get('vendedor_id', '')
    mes = request.args.get('mes', '')
    ano = request.args.get('ano', str(date.today().year))
    return data_ini, data_fim, cliente_id, vendedor_id, mes, ano


@relatorios_bp.route('/')
@login_required
def index():
    return render_template('relatorios/index.html')


@relatorios_bp.route('/vendas')
@login_required
def vendas():
    data_ini, data_fim, cliente_id, vendedor_id, mes, ano = _parse_filtros()
    query = Venda.query.order_by(Venda.data.desc())

    if data_ini:
        query = query.filter(Venda.data >= datetime.strptime(data_ini, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Venda.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if cliente_id:
        query = query.filter_by(cliente_id=int(cliente_id))
    if vendedor_id:
        query = query.filter_by(vendedor_id=int(vendedor_id))
    if mes:
        query = query.filter(extract('month', Venda.data) == int(mes))
    if ano:
        query = query.filter(extract('year', Venda.data) == int(ano))

    vendas = query.all()
    total_sacos = sum(v.quantidade_sacos for v in vendas)
    total_valor = sum(v.valor_liquido for v in vendas)
    total_lucro = sum(v.lucro for v in vendas)
    total_comissao = sum(v.comissao for v in vendas)

    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    vendedores = Vendedor.query.filter_by(ativo=True).order_by(Vendedor.nome).all()

    return render_template('relatorios/vendas.html',
                           vendas=vendas, total_sacos=total_sacos,
                           total_valor=total_valor, total_lucro=total_lucro,
                           total_comissao=total_comissao,
                           clientes=clientes, vendedores=vendedores,
                           data_ini=data_ini, data_fim=data_fim,
                           cliente_id=cliente_id, vendedor_id=vendedor_id,
                           mes=mes, ano=ano)


@relatorios_bp.route('/producao')
@login_required
def producao():
    data_ini, data_fim, *_ = _parse_filtros()
    ano = request.args.get('ano', str(date.today().year))
    query = Producao.query.order_by(Producao.data.desc())
    if data_ini:
        query = query.filter(Producao.data >= datetime.strptime(data_ini, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Producao.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if ano:
        query = query.filter(extract('year', Producao.data) == int(ano))
    producoes = query.all()
    total_sacos = sum(p.quantidade_sacos for p in producoes)
    total_custo = sum(p.custo_total for p in producoes)
    return render_template('relatorios/producao.html',
                           producoes=producoes, total_sacos=total_sacos,
                           total_custo=total_custo, data_ini=data_ini, data_fim=data_fim, ano=ano)


@relatorios_bp.route('/financeiro')
@login_required
def financeiro():
    data_ini, data_fim, *_ = _parse_filtros()
    mes = request.args.get('mes', '')
    ano = request.args.get('ano', str(date.today().year))
    query = Financeiro.query.order_by(Financeiro.data.desc())
    if data_ini:
        query = query.filter(Financeiro.data >= datetime.strptime(data_ini, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Financeiro.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if mes:
        query = query.filter(extract('month', Financeiro.data) == int(mes))
    if ano:
        query = query.filter(extract('year', Financeiro.data) == int(ano))
    lancamentos = query.all()
    receitas = sum(f.valor for f in lancamentos if f.tipo == 'receita')
    despesas = sum(f.valor for f in lancamentos if f.tipo == 'despesa')
    return render_template('relatorios/financeiro.html',
                           lancamentos=lancamentos, receitas=receitas,
                           despesas=despesas, saldo=receitas - despesas,
                           data_ini=data_ini, data_fim=data_fim, mes=mes, ano=ano)


@relatorios_bp.route('/estoque')
@login_required
def estoque():
    mps = MateriaPrima.query.order_by(MateriaPrima.id).all()
    from models.produto import ProdutoFinal
    produto = ProdutoFinal.query.first()
    return render_template('relatorios/estoque.html', mps=mps, produto=produto)


@relatorios_bp.route('/clientes')
@login_required
def clientes():
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    dados = []
    for c in clientes:
        dados.append({
            'cliente': c,
            'total': c.total_comprado,
            'qtd': c.quantidade_sacos_comprados,
            'ultima': c.ultima_compra,
            'devendo': c.saldo_devendo,
        })
    dados.sort(key=lambda x: x['total'], reverse=True)
    return render_template('relatorios/clientes.html', dados=dados)


@relatorios_bp.route('/vendedores')
@login_required
def vendedores():
    vendedores = Vendedor.query.filter_by(ativo=True).all()
    dados = []
    for v in vendedores:
        dados.append({
            'vendedor': v,
            'total_vendido': v.total_vendido,
            'total_comissao': v.total_comissao,
            'qtd_sacos': v.quantidade_sacos,
            'lucro_gerado': v.lucro_gerado,
        })
    dados.sort(key=lambda x: x['total_vendido'], reverse=True)
    return render_template('relatorios/vendedores.html', dados=dados)


@relatorios_bp.route('/compras')
@login_required
def compras():
    data_ini, data_fim, *_ = _parse_filtros()
    ano = request.args.get('ano', str(date.today().year))
    query = Compra.query.order_by(Compra.data.desc())
    if data_ini:
        query = query.filter(Compra.data >= datetime.strptime(data_ini, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Compra.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if ano:
        query = query.filter(extract('year', Compra.data) == int(ano))
    compras = query.all()
    total = sum(c.total_com_frete for c in compras)
    return render_template('relatorios/compras.html', compras=compras, total=total,
                           data_ini=data_ini, data_fim=data_fim, ano=ano)


@relatorios_bp.route('/exportar/csv/<tipo>')
@login_required
def exportar_csv(tipo):
    """Exportação CSV de qualquer relatório"""
    output = io.StringIO()
    writer = csv.writer(output)

    if tipo == 'vendas':
        writer.writerow(['Data', 'Cliente', 'Vendedor', 'Qtd Sacos', 'Preço Unit',
                         'Desconto', 'Frete', 'Valor Líquido', 'Custo', 'Lucro', 'Margem%', 'Comissão', 'Pagamento'])
        for v in Venda.query.order_by(Venda.data.desc()).all():
            writer.writerow([
                v.data.strftime('%d/%m/%Y'),
                v.cliente.nome if v.cliente else '',
                v.vendedor.nome if v.vendedor else '',
                v.quantidade_sacos, v.preco_unitario, v.desconto,
                v.frete, v.valor_liquido, v.custo_total,
                v.lucro, v.margem, v.comissao, v.forma_pagamento
            ])

    elif tipo == 'compras':
        writer.writerow(['Data', 'Fornecedor', 'Matéria-Prima', 'Qtd Sacos',
                         'Preço Unit', 'Frete Total', 'Total'])
        for c in Compra.query.order_by(Compra.data.desc()).all():
            writer.writerow([
                c.data.strftime('%d/%m/%Y'),
                c.fornecedor.nome if c.fornecedor else '',
                c.materia_prima.nome if c.materia_prima else '',
                c.quantidade_sacos, c.preco_unitario, c.frete_total, c.total_com_frete
            ])

    elif tipo == 'producao':
        writer.writerow(['Data', 'Lote', 'Qtd Sacos', 'Responsável', 'Custo/Saco', 'Custo Total'])
        for p in Producao.query.order_by(Producao.data.desc()).all():
            writer.writerow([
                p.data.strftime('%d/%m/%Y'), p.lote, p.quantidade_sacos,
                p.responsavel, p.custo_por_saco, p.custo_total
            ])

    output.seek(0)
    return send_file(
        io.BytesIO(('\ufeff' + output.getvalue()).encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{tipo}_{date.today().strftime("%Y%m%d")}.csv'
    )
