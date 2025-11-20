from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = 'Documents'

    def ready(self):
        """Import signal handlers when app is ready"""
        import apps.core.signals  # noqa: F401
