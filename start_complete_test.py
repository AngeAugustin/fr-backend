#!/usr/bin/env python
"""
Script de démarrage complet pour charger et tester le système
"""

import os
import sys
import subprocess
import time

def run_command(command, description, check=True):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Succès")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - Échec")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            if check:
                return False
            return True
    except Exception as e:
        print(f"❌ {description} - Erreur: {str(e)}")
        if check:
            return False
        return True

def main():
    print("🚀 DÉMARRAGE COMPLET DU SYSTÈME")
    print("=" * 50)
    print("Ce script va charger le CSV et tester le système complet")
    print("=" * 50)
    
    # Configuration
    venv_activate = "& C:/Users/HP/OneDrive/Documents/GitHub/fr_backend/.venv/Scripts/Activate.ps1"
    csv_file = "api_financialreportaccountdetail_with_previous_year.csv"
    
    # 1. Vérifier que le fichier CSV existe
    if not os.path.exists(csv_file):
        print(f"❌ Fichier CSV {csv_file} non trouvé")
        print("Assurez-vous que le fichier est dans le répertoire courant")
        return
    
    # 2. Activer l'environnement virtuel
    print("\n1️⃣ Activation de l'environnement virtuel...")
    
    # 3. Vérifier Django
    django_check = run_command(
        f"{venv_activate}; python -c \"import django; print(f'Django version: {{django.get_version()}}')\"",
        "Vérification de Django"
    )
    
    if not django_check:
        print("\n❌ Django n'est pas installé. Installation en cours...")
        install_django = run_command(
            f"{venv_activate}; pip install django",
            "Installation de Django"
        )
        if not install_django:
            print("❌ Impossible d'installer Django. Arrêt du test.")
            return
    
    # 4. Appliquer les migrations
    run_command(
        f"{venv_activate}; python manage.py migrate",
        "Application des migrations"
    )
    
    # 5. Charger les données CSV
    print(f"\n2️⃣ Chargement du fichier CSV: {csv_file}")
    load_success = run_command(
        f"{venv_activate}; python load_csv_to_postgresql.py {csv_file}",
        "Chargement des données CSV"
    )
    
    if not load_success:
        print("❌ Échec du chargement des données. Arrêt du test.")
        return
    
    # 6. Démarrer le serveur en arrière-plan
    print("\n3️⃣ Démarrage du serveur Django...")
    print("Le serveur va démarrer en arrière-plan.")
    print("Appuyez sur Ctrl+C pour arrêter le serveur et continuer les tests.")
    
    try:
        # Démarrer le serveur
        server_process = subprocess.Popen(
            f"{venv_activate}; python manage.py runserver",
            shell=True
        )
        
        # Attendre que le serveur démarre
        print("⏳ Attente du démarrage du serveur (10 secondes)...")
        time.sleep(10)
        
        # 7. Exécuter les tests
        print("\n4️⃣ Exécution des tests du système...")
        test_success = run_command(
            f"{venv_activate}; python test_postgresql_system.py",
            "Tests du système PostgreSQL",
            check=False
        )
        
        if test_success:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
            print("Le système fonctionne parfaitement.")
        else:
            print("\n⚠️  Certains tests ont échoué.")
            print("Consultez les détails ci-dessus.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du serveur...")
    finally:
        # Arrêter le serveur
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            server_process.kill()
    
    print("\n✅ Processus terminé!")
    print("\n📋 Prochaines étapes:")
    print("1. Consultez les résultats des tests ci-dessus")
    print("2. Si des tests ont échoué, consultez GUIDE_CHARGEMENT_CSV.md")
    print("3. Pour des tests manuels, utilisez les APIs directement")
    print("4. Pour redémarrer le serveur: python manage.py runserver")

if __name__ == "__main__":
    main()
