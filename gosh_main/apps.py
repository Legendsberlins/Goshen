from django.apps import AppConfig


class GoshMainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gosh_main'
    
    def ready(self):
        """Import signals when app is ready"""
        import gosh_main.signals