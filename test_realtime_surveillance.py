#!/usr/bin/env python
"""
Script de test pour le système de surveillance en temps réel
"""

import os
import sys
import django
from datetime import datetime, date
import random
import string

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData, BalanceUpload

def generate_test_data(financial_report_id, num_accounts=15):
    """Génère des données de test pour tester le système de surveillance"""
    
    print(f"🔄 Génération de {num_accounts} comptes de test pour financial_report_id: {financial_report_id}")
    
    # Comptes SYSCOHADA de test
    test_accounts = [
        ('521', 'Banque - Compte courant'),
        ('411', 'Clients - Ventes'),
        ('401', 'Fournisseurs - Achats'),
        ('601', 'Achats de marchandises'),
        ('701', 'Ventes de marchandises'),
        ('421', 'Personnel - Salaires'),
        ('441', 'État - TVA'),
        ('201', 'Immobilisations incorporelles'),
        ('211', 'Immobilisations corporelles'),
        ('101', 'Capital social'),
        ('103', 'Réserves'),
        ('108', 'Compte de l\'exploitant'),
        ('311', 'Stocks - Marchandises'),
        ('251', 'Immobilisations financières'),
        ('675', 'Charges exceptionnelles'),
    ]
    
    created_accounts = []
    
    for i in range(num_accounts):
        if i < len(test_accounts):
            account_number, account_label = test_accounts[i]
        else:
            # Générer des comptes aléatoires
            account_number = f"{random.randint(100, 999)}"
            account_label = f"Compte test {i+1}"
        
        # Créer l'AccountData
        account_data = AccountData.objects.create(
            financial_report_id=financial_report_id,
            account_number=account_number,
            account_label=account_label,
            balance=random.uniform(-100000, 100000),
            total_debit=random.uniform(0, 50000),
            total_credit=random.uniform(0, 50000),
            created_at=datetime.now()
        )
        
        created_accounts.append(account_data)
        print(f"   ✅ Créé: {account_number} - {account_label}")
    
    return created_accounts

def test_realtime_processing():
    """Test du système de traitement en temps réel"""
    
    print("🧪 TEST DU SYSTÈME DE SURVEILLANCE EN TEMPS RÉEL")
    print("=" * 60)
    
    # 1. Générer un financial_report_id de test
    test_financial_report_id = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📊 Financial Report ID de test: {test_financial_report_id}")
    
    # 2. Vérifier l'état initial
    initial_count = AccountData.objects.filter(financial_report_id=test_financial_report_id).count()
    print(f"📈 Comptes initiaux: {initial_count}")
    
    # 3. Générer des données de test (seuil minimum)
    print(f"\n🔄 Génération de données de test...")
    created_accounts = generate_test_data(test_financial_report_id, 15)
    
    # 4. Attendre un peu pour laisser le temps au signal de se déclencher
    print(f"\n⏳ Attente de 5 secondes pour le traitement automatique...")
    import time
    time.sleep(5)
    
    # 5. Vérifier si un traitement a été créé
    balance_uploads = BalanceUpload.objects.filter(financial_report_id=test_financial_report_id)
    
    if balance_uploads.exists():
        upload = balance_uploads.first()
        print(f"✅ Traitement automatique détecté!")
        print(f"   ID: {upload.id}")
        print(f"   Statut: {upload.status}")
        print(f"   Dates: {upload.start_date} à {upload.end_date}")
        print(f"   Commentaire: {upload.comment}")
        
        # Vérifier les fichiers générés
        generated_files = upload.generated_files.all()
        print(f"   Fichiers générés: {generated_files.count()}")
        
        for file in generated_files:
            print(f"     - {file.file_type}: {file.group_name or 'N/A'}")
        
        return True
    else:
        print(f"⚠️  Aucun traitement automatique détecté")
        print(f"   Vérifiez les logs dans logs/auto_processing.log")
        return False

def test_monitoring_command():
    """Test de la commande de surveillance"""
    
    print(f"\n🧪 TEST DE LA COMMANDE DE SURVEILLANCE")
    print("=" * 50)
    
    # Générer des données de test
    test_financial_report_id = f"MONITOR_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    generate_test_data(test_financial_report_id, 12)
    
    print(f"📊 Données de test créées pour: {test_financial_report_id}")
    print(f"💡 Exécutez maintenant: python manage.py monitor_data --once")
    print(f"   Ou: python monitor_realtime_data.py --once")

def cleanup_test_data():
    """Nettoie les données de test"""
    
    print(f"\n🧹 NETTOYAGE DES DONNÉES DE TEST")
    print("=" * 40)
    
    # Supprimer les données de test
    test_uploads = BalanceUpload.objects.filter(
        financial_report_id__startswith='TEST_'
    )
    
    test_accounts = AccountData.objects.filter(
        financial_report_id__startswith='TEST_'
    )
    
    upload_count = test_uploads.count()
    account_count = test_accounts.count()
    
    test_uploads.delete()
    test_accounts.delete()
    
    print(f"✅ Supprimé {upload_count} BalanceUpload(s) de test")
    print(f"✅ Supprimé {account_count} AccountData(s) de test")

def main():
    """Fonction principale de test"""
    
    print("🧪 TESTS DU SYSTÈME DE SURVEILLANCE EN TEMPS RÉEL")
    print("=" * 70)
    
    try:
        # Test 1: Traitement automatique par signal
        success = test_realtime_processing()
        
        # Test 2: Commande de surveillance
        test_monitoring_command()
        
        # Résumé
        print(f"\n📊 RÉSUMÉ DES TESTS:")
        print(f"   Traitement automatique: {'✅ Réussi' if success else '❌ Échec'}")
        print(f"   Commande de surveillance: 💡 À tester manuellement")
        
        # Nettoyage
        cleanup_test_data()
        
        print(f"\n🎯 PROCHAINES ÉTAPES:")
        print(f"   1. Vérifiez les logs: logs/auto_processing.log")
        print(f"   2. Testez la commande: python manage.py monitor_data --once")
        print(f"   3. Testez le script: python monitor_realtime_data.py --status")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
