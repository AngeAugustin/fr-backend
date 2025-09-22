from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BalanceUpload(models.Model):
    file = models.FileField(upload_to='balances/')
    start_date = models.DateField()
    end_date = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(blank=True, null=True)
    tft_json = models.JSONField(blank=True, null=True)
    feuilles_maitresses_json = models.JSONField(blank=True, null=True)
    coherence_json = models.JSONField(blank=True, null=True)

class GeneratedFile(models.Model):
    balance_upload = models.ForeignKey(BalanceUpload, related_name='generated_files', on_delete=models.CASCADE)
    file_type = models.CharField(max_length=30)  # 'TFT' ou 'feuille_maitresse'
    group_name = models.CharField(max_length=50, blank=True)  # ex: 'clients', 'fournisseurs', etc.
    file_content = models.BinaryField(blank=True, null=True)  # Stockage exclusif en base
    comment = models.TextField(blank=True, null=True, help_text="Commentaire pour cette feuille maîtresse")
    created_at = models.DateTimeField(auto_now_add=True)
