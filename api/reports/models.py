from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountData(models.Model):
    """Modèle pour stocker les données de balance générale chargées depuis CSV"""
    id = models.CharField(max_length=36, primary_key=True)  # UUID
    account_number = models.CharField(max_length=20, db_index=True)
    account_label = models.CharField(max_length=200, blank=True)
    account_class = models.CharField(max_length=10, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2)
    entries_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(db_index=True)
    financial_report_id = models.CharField(max_length=36, blank=True)
    account_lookup_key = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'account_data'
        indexes = [
            models.Index(fields=['account_number', 'created_at']),
            models.Index(fields=['financial_report_id']),
        ]
    
    def __str__(self):
        return f"{self.account_number} - {self.account_label}"

class BalanceUpload(models.Model):
    file = models.FileField(upload_to='balances/', null=True, blank=True)  # Rendu optionnel
    start_date = models.DateField()
    end_date = models.DateField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='success')
    error_message = models.TextField(blank=True, null=True)
    tft_json = models.JSONField(blank=True, null=True)
    feuilles_maitresses_json = models.JSONField(blank=True, null=True)
    coherence_json = models.JSONField(blank=True, null=True)
    financial_report_id = models.CharField(max_length=36, blank=True, null=True)  # Pour lier aux données AccountData

class GeneratedFile(models.Model):
    balance_upload = models.ForeignKey(BalanceUpload, related_name='generated_files', on_delete=models.CASCADE)
    file_type = models.CharField(max_length=30)  # 'TFT' ou 'feuille_maitresse'
    group_name = models.CharField(max_length=50, blank=True)  # ex: 'clients', 'fournisseurs', etc.
    file_content = models.BinaryField(blank=True, null=True)  # Stockage exclusif en base
    comment = models.TextField(blank=True, null=True, help_text="Commentaire pour cette feuille maîtresse")
    created_at = models.DateTimeField(auto_now_add=True)
