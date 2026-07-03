from extensions import db
from datetime import datetime


class Compra(db.Model):
    __tablename__ = 'compras'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    materia_prima_id = db.Column(db.Integer, db.ForeignKey('materias_primas.id'), nullable=False)
    quantidade_sacos = db.Column(db.Float, nullable=False)  # quantidade de sacos comprados
    preco_unitario = db.Column(db.Float, default=0.0)        # preço por saco
    frete_total = db.Column(db.Float, default=0.0)           # frete total da compra
    frete_por_saco = db.Column(db.Float, default=0.0)        # frete rateado por saco
    total = db.Column(db.Float, default=0.0)                  # total (sem frete)
    total_com_frete = db.Column(db.Float, default=0.0)        # total com frete
    numero_nf = db.Column(db.String(50))
    prazo_pagamento = db.Column(db.Integer, default=0)        # dias
    data_vencimento = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    materia_prima = db.relationship('MateriaPrima', backref='compras')
    conta_pagar = db.relationship('ContaPagar', backref='compra', uselist=False)

    def __repr__(self):
        return f'<Compra #{self.id} - {self.data}>'
