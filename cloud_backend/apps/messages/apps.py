from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.messages'
    label = 'chat_messages'  # Avoid conflict with django.contrib.messages
    verbose_name = 'Chat Messages'

    def ready(self):
        """Import signals when app is ready"""
        import apps.messages.signals  # noqa: F401
