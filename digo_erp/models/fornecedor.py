from extensions import db
from datetime import datetime


class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    tipo = db.Column(db.String(50))  # materia_prima | embalagem | frete | outro
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    compras = db.relationship('Compra', backref='fornecedor', lazy='dynamic')
    contas_pagar = db.relationship('ContaPagar', backref='fornecedor', lazy='dynamic')
    materias_primas = db.relationship('MateriaPrima', backref='fornecedor', lazy='dynamic')

    @property
    def total_comprado(self):
        return sum(c.total for c in self.compras if c.total)

    def __repr__(self):
        return f'<Fornecedor {self.nome}>'
