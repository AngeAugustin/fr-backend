#!/usr/bin/env python
"""
Script de test pour vérifier les données chargées et la génération TFT
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData, BalanceUpload, GeneratedFile
from api.reports.tft_generator import generate_tft_and_sheets_from_database

def test_database_connection():
    """Test 1: Vérifier la connexion PostgreSQL"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        if result:
            print("✅ Connexion PostgreSQL: Base de données accessible")
            return True
        else:
            print("❌ Connexion PostgreSQL: Aucun résultat de la base")
            return False
    except Exception as e:
        print(f"❌ Connexion PostgreSQL: {str(e)}")
        return False

def test_account_data_loaded():
    """Test 2: Vérifier que les données sont chargées"""
    try:
        account_count = AccountData.objects.count()
        if account_count > 0:
            # Analyser les données
            financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
            financial_report_ids = [fid for fid in financial_report_ids if fid]
            
            # Analyser les exercices
            exercices = AccountData.objects.values_list('created_at', flat=True).distinct()
            years = set([ex.year for ex in exercices if ex])
            
            print(f"✅ Données chargées: {account_count} enregistrements, {len(financial_report_ids)} financial_report_ids, Exercices: {sorted(years)}")
            
            return financial_report_ids
        else:
            print("❌ Données chargées: Aucune donnée trouvée")
            return []
    except Exception as e:
        print(f"❌ Données chargées: {str(e)}")
        return []

def test_tft_generation(financial_report_id):
    """Test 3: Tester la génération TFT"""
    try:
        # Déterminer les dates
        account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
        if not account_data.exists():
            print(f"❌ Génération TFT: Aucune donnée pour {financial_report_id}")
            return False
        
        dates = account_data.values_list('created_at', flat=True)
        start_date = min(dates).date()
        end_date = max(dates).date()
        
        print(f"🔄 Génération TFT pour {financial_report_id}...")
        print(f"   Période: {start_date} à {end_date}")
        
        # Générer le TFT
        tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
            financial_report_id, start_date, end_date
        )
        
        # Vérifier les résultats
        tft_size = len(tft_content) if tft_content else 0
        sheets_count = len(sheets_contents) if sheets_contents else 0
        
        print(f"✅ Génération TFT: TFT généré ({tft_size} bytes), {sheets_count} feuilles maîtresses")
        
        # Afficher les détails des feuilles maîtresses
        if sheets_contents:
            print("   Feuilles maîtresses générées:")
            for group_name in sheets_contents.keys():
                print(f"     - {group_name}")
        
        # Afficher les détails de cohérence
        if coherence:
            print(f"   Cohérence TFT: {coherence.get('is_coherent', 'N/A')}")
            if 'details' in coherence:
                details = coherence['details']
                print(f"     - Flux opérationnels: {details.get('flux_operationnels', 0)}")
                print(f"     - Flux investissement: {details.get('flux_investissement', 0)}")
                print(f"     - Flux financement: {details.get('flux_financement', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Génération TFT: {str(e)}")
        return False

def test_balance_upload_creation(financial_report_id):
    """Test 4: Tester la création d'un BalanceUpload"""
    try:
        # Déterminer les dates
        account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
        dates = account_data.values_list('created_at', flat=True)
        start_date = min(dates).date()
        end_date = max(dates).date()
        
        # Créer un BalanceUpload
        balance_upload = BalanceUpload.objects.create(
            file=None,
            start_date=start_date,
            end_date=end_date,
            user=None,
            status='processing',
            financial_report_id=financial_report_id
        )
        
        print(f"✅ BalanceUpload créé: ID {balance_upload.id}")
        
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
        
        # Fonction de nettoyage des données pour JSON
        def sanitize(obj):
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(v) for v in obj]
            elif hasattr(obj, 'isoformat'):  # Pour les Timestamps
                return obj.isoformat()
            elif hasattr(obj, 'item'):  # Pour les numpy types
                return obj.item()
            else:
                return obj
        
        # Mettre à jour le BalanceUpload
        balance_upload.status = 'success'
        balance_upload.tft_json = sanitize(tft_data)
        balance_upload.feuilles_maitresses_json = sanitize(sheets_data)
        balance_upload.coherence_json = sanitize(coherence)
        balance_upload.save()
        
        print(f"✅ Fichiers générés et stockés pour BalanceUpload {balance_upload.id}")
        
        # Vérifier les fichiers générés
        tft_files = GeneratedFile.objects.filter(balance_upload=balance_upload, file_type='TFT').count()
        sheet_files = GeneratedFile.objects.filter(balance_upload=balance_upload, file_type='feuille_maitresse').count()
        
        print(f"   - {tft_files} fichier(s) TFT")
        print(f"   - {sheet_files} feuille(s) maîtresse(s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Création BalanceUpload: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🧪 TEST DES DONNÉES ET GÉNÉRATION TFT")
    print("=" * 50)
    
    # Test 1: Connexion base
    if not test_database_connection():
        print("\n❌ Impossible de continuer sans connexion PostgreSQL")
        return False
    
    # Test 2: Données chargées
    financial_report_ids = test_account_data_loaded()
    if not financial_report_ids:
        print("\n❌ Aucune donnée AccountData trouvée")
        return False
    
    # Test 3: Génération TFT (test direct)
    print(f"\n🔄 Test de génération TFT...")
    if financial_report_ids:
        tft_success = test_tft_generation(financial_report_ids[0])
        if not tft_success:
            print("❌ Test de génération TFT échoué")
            return False
    
    # Test 4: Création BalanceUpload et stockage
    print(f"\n🔄 Test de création BalanceUpload...")
    if financial_report_ids:
        upload_success = test_balance_upload_creation(financial_report_ids[0])
        if not upload_success:
            print("❌ Test de création BalanceUpload échoué")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 TOUS LES TESTS SONT PASSÉS !")
    print("Le système fonctionne parfaitement avec PostgreSQL.")
    print("\n📋 Prochaines étapes:")
    print("1. Démarrer le serveur: python manage.py runserver")
    print("2. Tester les APIs via navigateur ou Postman")
    print("3. Utiliser les endpoints pour l'intégration")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
