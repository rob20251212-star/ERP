
import os
import threading
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from extensions import db
from models.configuracao import Configuracao
from models.usuario import Usuario
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from services.excel_import_service import import_excel_planilha

configuracoes_bp = Blueprint('configuracoes', __name__)


def _processar_upload_planilha(app, caminho_arquivo, nome_arquivo):
    with app.app_context():
        try:
            resumo = import_excel_planilha(caminho_arquivo)
            app.logger.info(
                'Importação de planilha concluída para %s: vendas=%s compras=%s',
                nome_arquivo,
                resumo.get('vendas', 0),
                resumo.get('compras', 0),
            )
        except Exception as exc:
            app.logger.exception('Falha ao importar planilha %s: %s', nome_arquivo, exc)
        finally:
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)


@configuracoes_bp.route('/')
@login_required
def index():
    configs = {c.chave: c.valor for c in Configuracao.query.all()}
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('configuracoes/index.html', configs=configs, usuarios=usuarios)


@configuracoes_bp.route('/salvar', methods=['POST'])
@login_required
def salvar():
    for chave, valor in request.form.items():
        if chave.startswith('_'):
            continue
        config = Configuracao.query.filter_by(chave=chave).first()
        if config:
            config.valor = valor
        else:
            db.session.add(Configuracao(chave=chave, valor=valor))
    db.session.commit()
    flash('Configurações salvas!', 'success')
    return redirect(url_for('configuracoes.index'))


@configuracoes_bp.route('/upload-planilha', methods=['POST'])
@login_required
def upload_planilha():
    arquivo = request.files.get('planilha_excel')
    if not arquivo or arquivo.filename == '':
        flash('Selecione um arquivo XLS ou XLSX antes de enviar.', 'danger')
        return redirect(url_for('configuracoes.index'))

    nome_arquivo = secure_filename(arquivo.filename)
    pasta_upload = os.path.join(current_app.root_path, 'instance', 'uploads')
    os.makedirs(pasta_upload, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_upload, f"{uuid.uuid4().hex}_{nome_arquivo}")
    arquivo.save(caminho_arquivo)

    thread = threading.Thread(
        target=_processar_upload_planilha,
        args=(current_app._get_current_object(), caminho_arquivo, nome_arquivo),
        daemon=True,
    )
    thread.start()

    flash('Arquivo recebido. A importação foi iniciada em segundo plano e pode levar alguns minutos.', 'info')
    return redirect(url_for('configuracoes.index'))


@configuracoes_bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if request.method == 'POST':
        u = Usuario(
            nome=request.form['nome'].strip(),
            email=request.form['email'].strip(),
            senha_hash=generate_password_hash(request.form['senha']),
            perfil=request.form.get('perfil', 'funcionario'),
            ativo=True
        )
        db.session.add(u)
        db.session.commit()
        flash(f'Usuário {u.nome} criado!', 'success')
        return redirect(url_for('configuracoes.index'))
    return render_template('configuracoes/usuario_form.html', usuario=None)


@configuracoes_bp.route('/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    u = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        u.nome = request.form['nome'].strip()
        u.email = request.form['email'].strip()
        u.perfil = request.form.get('perfil', 'funcionario')
        u.ativo = request.form.get('ativo') == 'on'
        if request.form.get('nova_senha'):
            u.senha_hash = generate_password_hash(request.form['nova_senha'])
        db.session.commit()
        flash(f'Usuário {u.nome} atualizado!', 'success')
        return redirect(url_for('configuracoes.index'))
    return render_template('configuracoes/usuario_form.html', usuario=u)
