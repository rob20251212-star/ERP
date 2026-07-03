from extensions import db
from datetime import datetime


class Vendedor(db.Model):
    __tablename__ = 'vendedores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    comissao_pct = db.Column(db.Float, default=0.0)  # % de comissão sobre venda
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    vendas = db.relationship('Venda', backref='vendedor', lazy='dynamic')

    @property
    def total_vendido(self):
        return sum(v.valor_liquido for v in self.vendas if v.valor_liquido)

    @property
    def total_comissao(self):
        return sum(v.comissao for v in self.vendas if v.comissao)

    @property
    def quantidade_sacos(self):
        return sum(v.quantidade_sacos for v in self.vendas)

    @property
    def lucro_gerado(self):
        return sum(v.lucro for v in self.vendas if v.lucro)

    def __repr__(self):
        return f'<Vendedor {self.nome}>'
