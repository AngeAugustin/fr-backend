#!/usr/bin/env python
"""
Script de test pour vérifier le système avec les données PostgreSQL
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData, BalanceUpload, GeneratedFile
from api.reports.tft_generator import generate_tft_and_sheets_from_database

class PostgreSQLSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """Enregistre le résultat d'un test"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now()
        })
    
    def test_database_connection(self):
        """Test 1: Vérifier la connexion PostgreSQL"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if result:
                self.log_test("Connexion PostgreSQL", True, "Base de données accessible")
                return True
            else:
                self.log_test("Connexion PostgreSQL", False, "Aucun résultat de la base")
                return False
        except Exception as e:
            self.log_test("Connexion PostgreSQL", False, str(e))
            return False
    
    def test_account_data_loaded(self):
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
                
                self.log_test("Données chargées", True, 
                    f"{account_count} enregistrements, {len(financial_report_ids)} financial_report_ids, "
                    f"Exercices: {sorted(years)}")
                
                return financial_report_ids
            else:
                self.log_test("Données chargées", False, "Aucune donnée trouvée")
                return []
        except Exception as e:
            self.log_test("Données chargées", False, str(e))
            return []
    
    def test_tft_generation(self, financial_report_id):
        """Test 3: Tester la génération TFT"""
        try:
            # Déterminer les dates
            account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
            if not account_data.exists():
                self.log_test("Génération TFT", False, f"Aucune donnée pour {financial_report_id}")
                return False
            
            dates = account_data.values_list('created_at', flat=True)
            start_date = min(dates).date()
            end_date = max(dates).date()
            
            # Générer le TFT
            tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
                financial_report_id, start_date, end_date
            )
            
            # Vérifier les résultats
            tft_size = len(tft_content) if tft_content else 0
            sheets_count = len(sheets_contents) if sheets_contents else 0
            
            self.log_test("Génération TFT", True, 
                f"TFT généré ({tft_size} bytes), {sheets_count} feuilles maîtresses")
            
            return True
        except Exception as e:
            self.log_test("Génération TFT", False, str(e))
            return False
    
    def test_server_connection(self):
        """Test 4: Vérifier la connexion au serveur"""
        try:
            response = requests.get(f"{self.base_url}/api/reports/process-account-data/", timeout=5)
            if response.status_code == 200:
                self.log_test("Connexion serveur", True, "Serveur accessible")
                return True
            else:
                self.log_test("Connexion serveur", False, f"Status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_test("Connexion serveur", False, "Serveur non démarré")
            return False
        except Exception as e:
            self.log_test("Connexion serveur", False, str(e))
            return False
    
    def test_api_processing(self, financial_report_id):
        """Test 5: Tester l'API de traitement"""
        try:
            # Déterminer les dates
            account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
            dates = account_data.values_list('created_at', flat=True)
            start_date = min(dates).date()
            end_date = max(dates).date()
            
            # Tester l'API
            payload = {
                "financial_report_id": financial_report_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            response = requests.post(f"{self.base_url}/api/reports/process-account-data/", 
                                  json=payload, timeout=30)
            
            if response.status_code in [200, 201]:
                data = response.json()
                if 'balance_upload_id' in data:
                    self.log_test("API Traitement", True, 
                        f"Traitement réussi, ID: {data['balance_upload_id']}")
                    return data['balance_upload_id']
                else:
                    self.log_test("API Traitement", False, "Réponse API invalide")
                    return None
            else:
                self.log_test("API Traitement", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("API Traitement", False, str(e))
            return None
    
    def test_generated_files(self):
        """Test 6: Vérifier les fichiers générés"""
        try:
            tft_files = GeneratedFile.objects.filter(file_type='TFT').count()
            sheet_files = GeneratedFile.objects.filter(file_type='feuille_maitresse').count()
            
            if tft_files > 0 and sheet_files > 0:
                self.log_test("Fichiers générés", True, 
                    f"{tft_files} fichiers TFT, {sheet_files} feuilles maîtresses")
                return True
            else:
                self.log_test("Fichiers générés", False, 
                    f"TFT: {tft_files}, Feuilles: {sheet_files}")
                return False
        except Exception as e:
            self.log_test("Fichiers générés", False, str(e))
            return False
    
    def test_download_functionality(self):
        """Test 7: Tester le téléchargement"""
        try:
            generated_file = GeneratedFile.objects.first()
            if generated_file:
                response = requests.get(f"{self.base_url}/api/reports/download-generated/{generated_file.id}/")
                if response.status_code == 200:
                    file_size = len(response.content)
                    self.log_test("Téléchargement", True, 
                        f"Fichier téléchargeable ({file_size} bytes)")
                    return True
                else:
                    self.log_test("Téléchargement", False, f"Status: {response.status_code}")
                    return False
            else:
                self.log_test("Téléchargement", False, "Aucun fichier généré")
                return False
        except Exception as e:
            self.log_test("Téléchargement", False, str(e))
            return False
    
    def test_history_api(self):
        """Test 8: Tester l'API d'historique"""
        try:
            response = requests.get(f"{self.base_url}/api/reports/balance-history/")
            if response.status_code == 200:
                data = response.json()
                history = data.get('history', [])
                
                self.log_test("API Historique", True, f"{len(history)} entrées dans l'historique")
                return True
            else:
                self.log_test("API Historique", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Historique", False, str(e))
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🧪 TEST DU SYSTÈME POSTGRESQL")
        print("=" * 50)
        
        # Test 1: Connexion base
        if not self.test_database_connection():
            print("\n❌ Impossible de continuer sans connexion PostgreSQL")
            return False
        
        # Test 2: Données chargées
        financial_report_ids = self.test_account_data_loaded()
        if not financial_report_ids:
            print("\n❌ Aucune donnée AccountData trouvée")
            print("Chargez d'abord vos données avec: python load_csv_to_postgresql.py your_file.csv")
            return False
        
        # Test 3: Génération TFT (test direct)
        if financial_report_ids:
            self.test_tft_generation(financial_report_ids[0])
        
        # Test 4: Connexion serveur
        if not self.test_server_connection():
            print("\n⚠️  Serveur non accessible. Démarrez-le avec: python manage.py runserver")
            return False
        
        # Test 5: API de traitement
        if financial_report_ids:
            self.test_api_processing(financial_report_ids[0])
        
        # Test 6: Fichiers générés
        self.test_generated_files()
        
        # Test 7: Téléchargement
        self.test_download_functionality()
        
        # Test 8: Historique
        self.test_history_api()
        
        # Résumé
        print("\n" + "=" * 50)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests réussis: {passed}/{total}")
        print(f"Taux de réussite: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
            print("Le système PostgreSQL fonctionne parfaitement.")
        else:
            print(f"\n⚠️  {total-passed} test(s) ont échoué.")
            print("Consultez les détails ci-dessus pour le dépannage.")
        
        return passed == total

def main():
    """Fonction principale"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python test_postgresql_system.py")
        print("Ce script teste le système avec les données PostgreSQL chargées.")
        print("\nPrérequis:")
        print("- Données chargées avec: python load_csv_to_postgresql.py your_file.csv")
        print("- Serveur démarré: python manage.py runserver")
        return
    
    tester = PostgreSQLSystemTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n🔧 ACTIONS RECOMMANDÉES:")
        print("1. Chargez les données: python load_csv_to_postgresql.py your_file.csv")
        print("2. Démarrez le serveur: python manage.py runserver")
        print("3. Vérifiez la configuration PostgreSQL")
        sys.exit(1)

if __name__ == "__main__":
    main()
