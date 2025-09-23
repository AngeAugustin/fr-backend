from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.reports'
    
    def ready(self):
        """
        Méthode appelée quand l'application Django est prête
        Importe les signaux pour activer le traitement automatique
        """
        import api.reports.signals
