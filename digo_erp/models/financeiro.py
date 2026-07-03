from extensions import db
from datetime import datetime


class Financeiro(db.Model):
    __tablename__ = 'financeiro'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # receita | despesa
    categoria = db.Column(db.String(60))  # venda|compra|frete|salario|embalagem|outro
    descricao = db.Column(db.String(255))
    valor = db.Column(db.Float, nullable=False)
    referencia_id = db.Column(db.Integer)
    referencia_tipo = db.Column(db.String(20))  # venda|compra|manual
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Financeiro {self.tipo} R${self.valor:.2f} {self.data}>'
