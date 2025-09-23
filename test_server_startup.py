#!/usr/bin/env python
"""
Script pour tester le démarrage du serveur Django
"""

import os
import sys
import django
from pathlib import Path

def test_server_startup():
    """Test du démarrage du serveur Django"""
    
    print("🚀 TEST DU DÉMARRAGE DU SERVEUR DJANGO")
    print("=" * 50)
    
    try:
        # Configuration Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
        
        # Vérifier que le dossier logs existe
        logs_dir = Path('logs')
        if not logs_dir.exists():
            print("📁 Création du dossier logs...")
            logs_dir.mkdir(exist_ok=True)
            print("   ✅ Dossier logs créé")
        else:
            print("   ✅ Dossier logs existe déjà")
        
        # Vérifier que le fichier de log peut être créé
        log_file = logs_dir / 'auto_processing.log'
        if not log_file.exists():
            print("📄 Création du fichier de log...")
            log_file.touch()
            print("   ✅ Fichier de log créé")
        else:
            print("   ✅ Fichier de log existe déjà")
        
        # Initialiser Django
        print("🔧 Initialisation de Django...")
        django.setup()
        print("   ✅ Django initialisé avec succès")
        
        # Tester l'import des modules
        print("📦 Test des imports...")
        from api.reports.models import AccountData, BalanceUpload, GeneratedFile
        from api.reports.views import AutoProcessView, ProcessAccountDataView
        from api.reports.tft_generator import generate_tft_and_sheets_from_database
        print("   ✅ Tous les modules importés avec succès")
        
        # Tester la configuration de logging
        print("📝 Test de la configuration de logging...")
        import logging
        logger = logging.getLogger('api.reports.signals')
        logger.info("Test de logging - serveur prêt")
        print("   ✅ Configuration de logging fonctionnelle")
        
        # Vérifier la base de données
        print("🗄️ Test de la base de données...")
        account_count = AccountData.objects.count()
        upload_count = BalanceUpload.objects.count()
        file_count = GeneratedFile.objects.count()
        print(f"   📊 AccountData: {account_count} enregistrements")
        print(f"   📊 BalanceUpload: {upload_count} enregistrements")
        print(f"   📊 GeneratedFile: {file_count} enregistrements")
        print("   ✅ Base de données accessible")
        
        print(f"\n🎉 SUCCÈS ! Le serveur Django est prêt à démarrer")
        print("=" * 50)
        print("💡 Commandes pour démarrer le serveur :")
        print("   python manage.py runserver")
        print("   ou")
        print("   py -3.10 manage.py runserver")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du test : {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🔧 DIAGNOSTIC COMPLET DU SERVEUR DJANGO")
    print("=" * 60)
    
    success = test_server_startup()
    
    if success:
        print(f"\n✅ DIAGNOSTIC RÉUSSI !")
        print("Votre serveur Django est prêt à démarrer sans erreurs.")
    else:
        print(f"\n❌ DIAGNOSTIC ÉCHOUÉ !")
        print("Des corrections sont nécessaires avant de démarrer le serveur.")

if __name__ == "__main__":
    main()
