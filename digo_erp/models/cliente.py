from extensions import db
from datetime import datetime


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf_cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    endereco = db.Column(db.String(255))
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    vendas = db.relationship('Venda', backref='cliente', lazy='dynamic')
    contas_receber = db.relationship('ContaReceber', backref='cliente', lazy='dynamic')

    @property
    def total_comprado(self):
        return sum(v.valor_liquido for v in self.vendas if v.valor_liquido)

    @property
    def ultima_compra(self):
        from models.venda import Venda
        ultima = self.vendas.order_by(Venda.data.desc()).first()
        return ultima.data if ultima else None

    @property
    def quantidade_sacos_comprados(self):
        return sum(v.quantidade_sacos for v in self.vendas)

    @property
    def saldo_devendo(self):
        return sum(c.valor for c in self.contas_receber.filter_by(status='pendente'))

    def __repr__(self):
        return f'<Cliente {self.nome}>'
