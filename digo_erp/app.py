from flask import Flask
from config import Config
from extensions import db, login_manager
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Criar pasta instance se não existir
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'instance', 'backups'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.clientes import clientes_bp
    from routes.fornecedores import fornecedores_bp
    from routes.vendedores import vendedores_bp
    from routes.materias_primas import materias_primas_bp
    from routes.producao import producao_bp
    from routes.compras import compras_bp
    from routes.estoque import estoque_bp
    from routes.vendas import vendas_bp
    from routes.financeiro import financeiro_bp
    from routes.relatorios import relatorios_bp
    from routes.configuracoes import configuracoes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(fornecedores_bp, url_prefix='/fornecedores')
    app.register_blueprint(vendedores_bp, url_prefix='/vendedores')
    app.register_blueprint(materias_primas_bp, url_prefix='/materias-primas')
    app.register_blueprint(producao_bp, url_prefix='/producao')
    app.register_blueprint(compras_bp, url_prefix='/compras')
    app.register_blueprint(estoque_bp, url_prefix='/estoque')
    app.register_blueprint(vendas_bp, url_prefix='/vendas')
    app.register_blueprint(financeiro_bp, url_prefix='/financeiro')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(configuracoes_bp, url_prefix='/configuracoes')

    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    from models.usuario import Usuario
    from models.materia_prima import MateriaPrima
    from models.produto import ProdutoFinal
    from models.configuracao import Configuracao
    from werkzeug.security import generate_password_hash

    # Admin padrão
    if not Usuario.query.first():
        admin = Usuario(
            nome='Administrador',
            email='admin@digo.com',
            senha_hash=generate_password_hash('admin123'),
            perfil='admin',
            ativo=True
        )
        db.session.add(admin)

    # Matérias-primas padrão
    if not MateriaPrima.query.first():
        mps = [
            MateriaPrima(
                nome='Celulósico',
                tipo='celulosico',
                peso_saco_kg=25.0,
                quantidade_uso_kg=12.5,
                preco_saco=0.0,
                frete_saco=0.0,
                estoque_atual=0.0,
                estoque_minimo=50.0
            ),
            MateriaPrima(
                nome='Celugel',
                tipo='celugel',
                peso_saco_kg=25.0,
                quantidade_uso_kg=7.5,
                preco_saco=0.0,
                frete_saco=0.0,
                estoque_atual=0.0,
                estoque_minimo=50.0
            ),
            MateriaPrima(
                nome='Fibra',
                tipo='fibra',
                peso_saco_kg=20.0,
                quantidade_uso_kg=5.0,
                preco_saco=0.0,
                frete_saco=0.0,
                estoque_atual=0.0,
                estoque_minimo=50.0
            ),
            MateriaPrima(
                nome='Embalagem',
                tipo='embalagem',
                peso_saco_kg=1.0,
                quantidade_uso_kg=1.0,
                preco_saco=0.0,
                frete_saco=0.0,
                estoque_atual=0.0,
                estoque_minimo=100.0
            ),
            MateriaPrima(
                nome='Adesivo',
                tipo='adesivo',
                peso_saco_kg=1.0,
                quantidade_uso_kg=1.0,
                preco_saco=0.0,
                frete_saco=0.0,
                estoque_atual=0.0,
                estoque_minimo=100.0
            ),
        ]
        for mp in mps:
            db.session.add(mp)

    # Produto final padrão
    if not ProdutoFinal.query.first():
        produto = ProdutoFinal(
            nome='Argamassa 25kg',
            peso_kg=25.0,
            estoque_atual=0.0,
            estoque_minimo=50.0,
            custo_calculado=0.0,
            preco_venda_padrao=0.0,
            margem_lucro_pct=15.0
        )
        db.session.add(produto)

    # Configurações padrão
    configs = [
        ('empresa_nome', 'DIGO', 'Nome da empresa'),
        ('empresa_cnpj', '', 'CNPJ da empresa'),
        ('empresa_telefone', '', 'Telefone da empresa'),
        ('margem_lucro_padrao', '15', 'Margem de lucro padrão (%)'),
        ('estoque_alerta_dias', '7', 'Dias para alertar estoque'),
    ]
    for chave, valor, desc in configs:
        if not Configuracao.query.filter_by(chave=chave).first():
            db.session.add(Configuracao(chave=chave, valor=valor, descricao=desc))

    db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
