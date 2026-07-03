from extensions import db
from datetime import datetime


class Producao(db.Model):
    __tablename__ = 'producao'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    lote = db.Column(db.String(50))
    quantidade_sacos = db.Column(db.Integer, nullable=False)
    responsavel = db.Column(db.String(100))
    custo_total = db.Column(db.Float, default=0.0)
    custo_por_saco = db.Column(db.Float, default=0.0)
    observacoes = db.Column(db.Text)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Consumo registrado (snapshot dos custos no momento da produção)
    consumo_celulosico_kg = db.Column(db.Float, default=0.0)
    consumo_celugel_kg = db.Column(db.Float, default=0.0)
    consumo_fibra_kg = db.Column(db.Float, default=0.0)
    consumo_embalagem_un = db.Column(db.Integer, default=0)
    consumo_adesivo_un = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Producao Lote:{self.lote} - {self.quantidade_sacos} sacos>'
