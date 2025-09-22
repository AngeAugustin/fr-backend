#!/usr/bin/env python
"""
Script pour charger le fichier CSV dans PostgreSQL
Usage: python load_csv_to_postgresql.py api_financialreportaccountdetail_with_previous_year.csv
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData

def load_csv_to_postgresql(csv_file_path):
    """Charge le fichier CSV dans PostgreSQL"""
    
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
        
        # Nettoyer les données existantes pour ce financial_report_id (si spécifié)
        financial_report_id = df['financial_report_id'].iloc[0] if 'financial_report_id' in df.columns else None
        if financial_report_id:
            print(f"🧹 Nettoyage des données existantes pour financial_report_id: {financial_report_id}")
            AccountData.objects.filter(financial_report_id=financial_report_id).delete()
        
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
        print(f"💾 Insertion de {len(account_data_list)} enregistrements dans PostgreSQL...")
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

def test_database_connection():
    """Teste la connexion à la base de données"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        if result:
            print("✅ Connexion à PostgreSQL réussie")
            return True
        else:
            print("❌ Problème de connexion à PostgreSQL")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL: {str(e)}")
        return False

def main():
    """Fonction principale"""
    if len(sys.argv) != 2:
        print("Usage: python load_csv_to_postgresql.py <fichier_csv>")
        print("Exemple: python load_csv_to_postgresql.py api_financialreportaccountdetail_with_previous_year.csv")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    print("🚀 CHARGEMENT CSV VERS POSTGRESQL")
    print("=" * 50)
    
    # Test de connexion
    if not test_database_connection():
        print("\n❌ Impossible de continuer sans connexion à PostgreSQL")
        print("Vérifiez votre configuration de base de données dans settings.py")
        sys.exit(1)
    
    # Chargement des données
    success = load_csv_to_postgresql(csv_file_path)
    
    if success:
        print("\n🎉 CHARGEMENT TERMINÉ AVEC SUCCÈS!")
        print("\n📋 Prochaines étapes:")
        print("1. Démarrer le serveur: python manage.py runserver")
        print("2. Tester l'exploitation des données")
        print("3. Utiliser les APIs pour générer les rapports")
    else:
        print("\n❌ ÉCHEC DU CHARGEMENT")
        print("Consultez les erreurs ci-dessus pour le dépannage")
        sys.exit(1)

if __name__ == "__main__":
    main()
