from extensions import db
from datetime import datetime


class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(10), nullable=False)  # entrada | saida | ajuste
    materia_prima_id = db.Column(db.Integer, db.ForeignKey('materias_primas.id'), nullable=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto_final.id'), nullable=True)
    quantidade = db.Column(db.Float, nullable=False)
    saldo_antes = db.Column(db.Float, default=0.0)
    saldo_depois = db.Column(db.Float, default=0.0)
    motivo = db.Column(db.String(100))  # compra | producao | venda | ajuste | perda
    referencia_id = db.Column(db.Integer)   # id do compra/producao/venda
    referencia_tipo = db.Column(db.String(20))  # compra | producao | venda
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    observacoes = db.Column(db.Text)

    produto = db.relationship('ProdutoFinal', backref='movimentacoes')

    def __repr__(self):
        return f'<Movimentacao {self.tipo} {self.quantidade}>'
