#!/usr/bin/env python
"""
Script de test avec SQLite pour contourner le problème PostgreSQL
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Configuration Django avec SQLite temporaire
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')

# Modifier temporairement la configuration de base de données
import django.conf
django.conf.settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_database.db',
    }
}

django.setup()

from api.reports.models import AccountData

def load_csv_to_sqlite(csv_file_path):
    """Charge le fichier CSV dans SQLite pour test"""
    
    print(f"🔄 Chargement du fichier: {csv_file_path}")
    
    # Vérifier que le fichier existe
    if not os.path.exists(csv_file_path):
        print(f"❌ ERREUR: Le fichier {csv_file_path} n'existe pas")
        return False
    
    try:
        # Lire le CSV
        print("📖 Lecture du fichier CSV...")
        df = pd.read_csv(csv_file_path)
        print(f"✅ {len(df)} lignes lues")
        
        # Afficher les colonnes
        print(f"📋 Colonnes disponibles: {list(df.columns)}")
        
        # Vérifier les colonnes requises
        required_columns = ['id', 'account_number', 'balance', 'total_debit', 'total_credit', 'created_at']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ ERREUR: Colonnes manquantes: {missing_columns}")
            return False
        
        # Nettoyer les données existantes
        print("🧹 Nettoyage des données existantes...")
        AccountData.objects.all().delete()
        
        # Préparer les données pour l'insertion
        print("🔄 Préparation des données...")
        account_data_list = []
        errors = 0
        
        for index, row in df.iterrows():
            try:
                # Convertir created_at en datetime
                created_at = pd.to_datetime(row['created_at']).to_pydatetime()
                
                # Créer l'objet AccountData
                account_data = AccountData(
                    id=str(row['id']),
                    account_number=str(row['account_number']),
                    account_label=str(row.get('account_label', '')),
                    account_class=str(row.get('account_class', '')),
                    balance=float(row['balance']),
                    total_debit=float(row['total_debit']),
                    total_credit=float(row['total_credit']),
                    entries_count=int(row.get('entries_count', 0)),
                    created_at=created_at,
                    financial_report_id=str(row.get('financial_report_id', '')),
                    account_lookup_key=str(row.get('account_lookup_key', '')) if pd.notna(row.get('account_lookup_key')) else None
                )
                account_data_list.append(account_data)
                
                # Afficher le progrès
                if (index + 1) % 500 == 0:
                    print(f"   Traité {index + 1}/{len(df)} lignes...")
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Afficher seulement les 5 premières erreurs
                    print(f"⚠️  Erreur à la ligne {index + 1}: {e}")
                continue
        
        if errors > 0:
            print(f"⚠️  {errors} erreurs rencontrées sur {len(df)} lignes")
        
        # Insérer en lot
        print(f"💾 Insertion de {len(account_data_list)} enregistrements dans SQLite...")
        AccountData.objects.bulk_create(account_data_list, batch_size=1000)
        
        print(f"✅ {len(account_data_list)} enregistrements chargés avec succès!")
        
        # Afficher les statistiques
        total_count = AccountData.objects.count()
        financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        financial_report_ids = [fid for fid in financial_report_ids if fid]  # Filtrer les valeurs vides
        
        print(f"\n📊 Statistiques:")
        print(f"   - Total enregistrements dans la base: {total_count}")
        print(f"   - Financial Report IDs: {len(financial_report_ids)}")
        
        if financial_report_ids:
            for fid in financial_report_ids:
                count = AccountData.objects.filter(financial_report_id=fid).count()
                print(f"     * {fid}: {count} enregistrements")
        
        # Analyser les exercices
        exercices = AccountData.objects.values_list('created_at', flat=True).distinct()
        years = set([ex.year for ex in exercices if ex])
        print(f"   - Exercices disponibles: {sorted(years)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR lors du chargement: {str(e)}")
        return False

def test_tft_generation():
    """Teste la génération TFT"""
    try:
        from api.reports.tft_generator import generate_tft_and_sheets_from_database
        
        # Récupérer un financial_report_id
        financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        financial_report_ids = [fid for fid in financial_report_ids if fid]
        
        if not financial_report_ids:
            print("❌ Aucun financial_report_id trouvé")
            return False
        
        financial_report_id = financial_report_ids[0]
        print(f"🧪 Test de génération TFT pour {financial_report_id}")
        
        # Déterminer les dates
        account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
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
        
        print(f"✅ TFT généré ({tft_size} bytes), {sheets_count} feuilles maîtresses")
        print(f"✅ Période: {start_date} à {end_date}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération TFT: {str(e)}")
        return False

def main():
    """Fonction principale"""
    if len(sys.argv) != 2:
        print("Usage: python test_with_sqlite.py <fichier_csv>")
        print("Exemple: python test_with_sqlite.py api_financialreportaccountdetail_with_previous_year.csv")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    print("🚀 TEST AVEC SQLITE (CONTOURNEMENT POSTGRESQL)")
    print("=" * 60)
    
    # Appliquer les migrations
    print("🔄 Application des migrations...")
    os.system("python manage.py migrate")
    
    # Chargement des données
    success = load_csv_to_sqlite(csv_file_path)
    
    if success:
        print("\n🎉 CHARGEMENT TERMINÉ AVEC SUCCÈS!")
        
        # Test de génération TFT
        print("\n🧪 Test de génération TFT...")
        tft_success = test_tft_generation()
        
        if tft_success:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
            print("Le système fonctionne correctement avec SQLite.")
            print("\n📋 Pour utiliser PostgreSQL:")
            print("1. Installez psycopg2-binary: pip install psycopg2-binary")
            print("2. Configurez votre base PostgreSQL")
            print("3. Relancez avec le script PostgreSQL")
        else:
            print("\n⚠️  Test de génération TFT échoué")
    else:
        print("\n❌ ÉCHEC DU CHARGEMENT")
        print("Consultez les erreurs ci-dessus pour le dépannage")
        sys.exit(1)

if __name__ == "__main__":
    main()
