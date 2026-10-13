from django.apps import AppConfig
from django.db.backends.signals import connection_created


def configure_sqlite_concurrency(sender, connection, **kwargs):
    """
    Enables Write-Ahead Logging (WAL) and busy timeout on SQLite connections.
    WAL allows multiple concurrent readers and writers without blocking or 'database is locked' errors.
    """
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA busy_timeout = 30000;')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        connection_created.connect(configure_sqlite_concurrency)
