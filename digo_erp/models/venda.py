from extensions import db
from datetime import datetime


class Venda(db.Model):
    __tablename__ = 'vendas'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('vendedores.id'), nullable=True)
    quantidade_sacos = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0)       # valor do desconto
    frete = db.Column(db.Float, default=0.0)
    tipo_frete = db.Column(db.String(10), default='FOB')  # CIF | FOB
    forma_pagamento = db.Column(db.String(50))         # A VISTA | CHEQUE | PRAZO
    prazo_dias = db.Column(db.Integer, default=0)

    # Valores calculados automaticamente
    valor_bruto = db.Column(db.Float, default=0.0)    # qtd * preco_unitario
    valor_liquido = db.Column(db.Float, default=0.0)  # bruto - desconto + frete(CIF)
    custo_total = db.Column(db.Float, default=0.0)    # custo produto * qtd
    lucro = db.Column(db.Float, default=0.0)           # liquido - custo
    margem = db.Column(db.Float, default=0.0)          # lucro/liquido * 100
    comissao = db.Column(db.Float, default=0.0)        # % do vendedor sobre valor_liquido

    status_pagamento = db.Column(db.String(20), default='pendente')  # pendente|parcial|pago
    valor_pago = db.Column(db.Float, default=0.0)
    observacoes = db.Column(db.Text)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    conta_receber = db.relationship('ContaReceber', backref='venda', uselist=False)

    def __repr__(self):
        return f'<Venda #{self.id} - {self.data}>'


class ContaReceber(db.Model):
    __tablename__ = 'contas_receber'

    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')  # pendente|pago|vencido
    data_pagamento = db.Column(db.Date)
    valor_pago = db.Column(db.Float, default=0.0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContaReceber #{self.id} R${self.valor:.2f}>'


class ContaPagar(db.Model):
    __tablename__ = 'contas_pagar'

    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    vencimento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')  # pendente|pago|vencido
    data_pagamento = db.Column(db.Date)
    valor_pago = db.Column(db.Float, default=0.0)
    categoria = db.Column(db.String(50))  # materia_prima|frete|embalagem|salario|outro
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContaPagar #{self.id} R${self.valor:.2f}>'
