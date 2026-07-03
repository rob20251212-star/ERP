from extensions import db
from datetime import datetime


class ProdutoFinal(db.Model):
    __tablename__ = 'produto_final'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), default='Argamassa 25kg')
    peso_kg = db.Column(db.Float, default=25.0)
    estoque_atual = db.Column(db.Float, default=0.0)  # em sacos
    estoque_minimo = db.Column(db.Float, default=0.0)
    custo_calculado = db.Column(db.Float, default=0.0)   # custo total por saco
    preco_venda_padrao = db.Column(db.Float, default=0.0)
    margem_lucro_pct = db.Column(db.Float, default=15.0)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def custo_por_kg(self):
        if self.peso_kg and self.peso_kg > 0:
            return self.custo_calculado / self.peso_kg
        return 0.0

    @property
    def valor_em_estoque(self):
        return self.estoque_atual * self.custo_calculado

    @property
    def abaixo_minimo(self):
        return self.estoque_atual < self.estoque_minimo

    @property
    def lucro_por_saco(self):
        return self.preco_venda_padrao - self.custo_calculado

    @property
    def margem_real(self):
        if self.preco_venda_padrao and self.preco_venda_padrao > 0:
            return ((self.preco_venda_padrao - self.custo_calculado) / self.preco_venda_padrao) * 100
        return 0.0

    def __repr__(self):
        return f'<ProdutoFinal {self.nome}>'
