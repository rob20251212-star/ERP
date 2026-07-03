from extensions import db
from datetime import datetime


class MateriaPrima(db.Model):
    __tablename__ = 'materias_primas'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)  # celulosico|celugel|fibra|embalagem|adesivo
    peso_saco_kg = db.Column(db.Float, default=25.0)      # peso do saco comprado
    quantidade_uso_kg = db.Column(db.Float, default=0.0)  # kg consumidos por saco de produto
    preco_saco = db.Column(db.Float, default=0.0)          # preço por saco comprado
    frete_saco = db.Column(db.Float, default=0.0)          # frete rateado por saco
    custo_medio = db.Column(db.Float, default=0.0)         # custo médio calculado
    estoque_atual = db.Column(db.Float, default=0.0)       # em unidades (sacos ou pcs)
    estoque_minimo = db.Column(db.Float, default=0.0)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    observacoes = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimentacoes = db.relationship('MovimentacaoEstoque', backref='materia_prima',
                                    lazy='dynamic',
                                    foreign_keys='MovimentacaoEstoque.materia_prima_id')

    @property
    def custo_por_kg(self):
        """Custo por kg incluindo frete"""
        total_saco = self.preco_saco + self.frete_saco
        if self.peso_saco_kg and self.peso_saco_kg > 0:
            return total_saco / self.peso_saco_kg
        return 0.0

    @property
    def custo_proporcional(self):
        """Custo proporcional ao consumo no produto (por saco de produto)"""
        return self.custo_por_kg * self.quantidade_uso_kg

    @property
    def valor_em_estoque(self):
        """Valor monetário do estoque atual"""
        custo = self.custo_medio if self.custo_medio else (self.preco_saco + self.frete_saco)
        return self.estoque_atual * custo

    @property
    def abaixo_minimo(self):
        return self.estoque_atual < self.estoque_minimo

    def __repr__(self):
        return f'<MateriaPrima {self.nome}>'
