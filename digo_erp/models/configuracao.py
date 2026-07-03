from extensions import db
from datetime import datetime


class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(50))  # criar|editar|excluir|login|logout
    tabela = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    dados_antes = db.Column(db.Text)
    dados_depois = db.Column(db.Text)
    ip = db.Column(db.String(45))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Log {self.acao} {self.tabela}#{self.registro_id}>'


class Configuracao(db.Model):
    __tablename__ = 'configuracoes'

    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text)
    descricao = db.Column(db.String(255))
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Configuracao {self.chave}={self.valor}>'
