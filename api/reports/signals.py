"""
Signals Django pour le traitement automatique des données AccountData
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
import logging
from .models import AccountData, BalanceUpload, GeneratedFile
from .tft_generator import generate_tft_and_sheets_from_database
from datetime import date
import math
import pandas as pd
import numpy as np

# Configuration du logger
logger = logging.getLogger(__name__)

@receiver(post_save, sender=AccountData)
def auto_process_new_account_data(sender, instance, created, **kwargs):
    """
    Signal déclenché à chaque création/modification d'AccountData
    Traite automatiquement les nouvelles données si nécessaire
    """
    if created:
        logger.info(f"Nouvelle donnée AccountData créée: {instance.account_number} - {instance.account_label}")
        
        # Traitement différé pour éviter les conflits
        transaction.on_commit(lambda: process_financial_report_async(instance.financial_report_id))
    else:
        logger.info(f"Donnée AccountData modifiée: {instance.account_number}")

def process_financial_report_async(financial_report_id):
    """
    Traite de manière asynchrone un financial_report_id
    """
    if not financial_report_id:
        return
    
    try:
        # Vérifier si le traitement existe déjà
        existing_upload = BalanceUpload.objects.filter(
            financial_report_id=financial_report_id
        ).first()
        
        if existing_upload:
            logger.info(f"Traitement déjà existant pour financial_report_id: {financial_report_id}")
            return
        
        # Vérifier si on a suffisamment de données pour traiter
        account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
        if account_data.count() < 10:  # Seuil minimum de données
            logger.info(f"Données insuffisantes pour financial_report_id: {financial_report_id} ({account_data.count()} comptes)")
            return
        
        logger.info(f"Début du traitement automatique pour financial_report_id: {financial_report_id}")
        
        # Déterminer les dates automatiquement
        exercices = set()
        for data in account_data:
            exercices.add(data.created_at.year)
        
        exercices = sorted(exercices)
        
        if len(exercices) >= 2:
            n_1 = exercices[-2]
            n = exercices[-1]
            start_date = date(n_1, 1, 1)
            end_date = date(n, 12, 31)
        elif len(exercices) == 1:
            n = exercices[0]
            start_date = date(n, 1, 1)
            end_date = date(n, 12, 31)
        else:
            logger.warning(f"Aucun exercice détecté pour financial_report_id: {financial_report_id}")
            return
        
        # Créer le BalanceUpload
        balance_upload = BalanceUpload.objects.create(
            file=None,
            start_date=start_date,
            end_date=end_date,
            user=None,  # Traitement automatique
            status='processing',
            financial_report_id=financial_report_id,
            comment=f"Traitement automatique - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Générer les rapports
        tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
            financial_report_id, start_date, end_date
        )
        
        # Enregistrer le fichier TFT
        GeneratedFile.objects.create(
            balance_upload=balance_upload,
            file_type='TFT',
            file_content=tft_content
        )
        
        # Enregistrer les feuilles maîtresses
        for group_name, sheet_content in sheets_contents.items():
            GeneratedFile.objects.create(
                balance_upload=balance_upload,
                file_type='feuille_maitresse',
                group_name=group_name,
                file_content=sheet_content
            )
        
        # Fonction de nettoyage des données
        def sanitize(obj):
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(v) for v in obj]
            elif isinstance(obj, (np.integer, np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float32, np.float64)):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return float(obj)
            elif isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return obj
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        # Mettre à jour le BalanceUpload avec les résultats
        balance_upload.status = 'success'
        balance_upload.tft_json = sanitize(tft_data)
        balance_upload.feuilles_maitresses_json = sanitize(sheets_data)
        balance_upload.coherence_json = coherence
        balance_upload.save()
        
        logger.info(f"Traitement automatique réussi pour financial_report_id: {financial_report_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement automatique pour financial_report_id {financial_report_id}: {str(e)}")
        
        # Marquer le traitement comme échoué
        try:
            balance_upload = BalanceUpload.objects.filter(
                financial_report_id=financial_report_id,
                status='processing'
            ).first()
            if balance_upload:
                balance_upload.status = 'error'
                balance_upload.error_message = str(e)
                balance_upload.save()
        except:
            pass

@receiver(post_delete, sender=AccountData)
def handle_account_data_deletion(sender, instance, **kwargs):
    """
    Signal déclenché lors de la suppression d'AccountData
    """
    logger.info(f"Donnée AccountData supprimée: {instance.account_number} - {instance.account_label}")
    
    # Vérifier si il reste des données pour ce financial_report_id
    remaining_data = AccountData.objects.filter(financial_report_id=instance.financial_report_id)
    if remaining_data.count() == 0:
        logger.info(f"Aucune donnée restante pour financial_report_id: {instance.financial_report_id}")
        # Optionnel: marquer les traitements comme obsolètes
        BalanceUpload.objects.filter(
            financial_report_id=instance.financial_report_id
        ).update(status='obsolete')
