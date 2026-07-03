import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_url():
    """
    Railway fornece DATABASE_URL com prefixo 'postgres://' (legado),
    mas o SQLAlchemy 1.4+ exige 'postgresql://'.
    Esta função corrige isso automaticamente.
    """
    url = os.environ.get('DATABASE_URL')
    if url:
        # Corrige o prefixo legado do Heroku/Railway
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    # Fallback para SQLite em desenvolvimento local
    return 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'digo.db')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'digo-erp-secret-key-2024-change-in-production')
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Backup automático
    BACKUP_DIR = os.path.join(BASE_DIR, 'instance', 'backups')

    # Configurações de paginação
    ITEMS_PER_PAGE = 20
