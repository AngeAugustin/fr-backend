#!/usr/bin/env python
"""
Test final des feuilles maîtresses avec le nouveau mapping
"""

import os
import sys
import django
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData
from api.reports.tft_generator import generate_tft_and_sheets_from_database

def test_final_master_sheets():
    """Test final des feuilles maîtresses avec le nouveau mapping"""
    
    print("🎯 TEST FINAL DES FEUILLES MAÎTRESSES")
    print("=" * 60)
    
    # Récupérer un financial_report_id pour test
    financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
    financial_report_ids = [fid for fid in financial_report_ids if fid]
    
    if not financial_report_ids:
        print("❌ Aucune donnée disponible")
        return
    
    financial_report_id = financial_report_ids[0]
    
    # Déterminer les dates
    account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
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
        print("❌ Aucun exercice détecté")
        return
    
    print(f"📅 Période: {start_date} à {end_date}")
    
    # Générer le TFT et les feuilles maîtresses
    try:
        tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
            financial_report_id, start_date, end_date
        )
        
        print(f"✅ TFT et feuilles maîtresses générés avec succès")
        
        # Nouveau mapping corrigé
        new_groups = {
            'financier': ['431', '521'],
            'Clients-Ventes': ['411', '419', '445', '622', '628', '631', '661', '758'],
            'Fournisseurs-Achats': ['283', '284', '401', '409', '422', '445', '447', '476', '605', '633', '637', '641', '658', '661', '664', '681'],
            'personnel': ['422', '447', '633', '641', '661', '664'],
            'Impots-Taxes': ['447', '641'],
            'Immobilisations': ['244', '624'],
            'stocks': ['605'],
            'capitaux_propres': ['121'],
            'Provisions R-C': ['121'],
        }
        
        # Analyser chaque groupe avec le nouveau mapping
        print(f"\n📋 ANALYSE AVEC LE NOUVEAU MAPPING:")
        print("=" * 50)
        
        total_groups = len(new_groups)
        groups_with_data = 0
        groups_empty = 0
        groups_problematic = 0
        
        for group_name, prefixes in new_groups.items():
            print(f"\n🔍 Groupe: {group_name}")
            print(f"   Préfixes configurés: {prefixes}")
            
            # Vérifier si le groupe a des données
            if group_name in sheets_contents and sheets_contents[group_name]:
                content_size = len(sheets_contents[group_name])
                print(f"   ✅ Contenu généré: {content_size} bytes")
                
                # Vérifier les données du groupe
                if group_name in sheets_data and sheets_data[group_name]:
                    group_data = sheets_data[group_name]
                    if isinstance(group_data, list) and len(group_data) > 0:
                        print(f"   ✅ Données trouvées: {len(group_data)} comptes")
                        groups_with_data += 1
                        
                        # Afficher quelques exemples de comptes
                        print(f"   📊 Exemples de comptes:")
                        for i, compte in enumerate(group_data[:3]):
                            if isinstance(compte, dict):
                                account_num = compte.get('account_number', 'N/A')
                                balance = compte.get('balance', 0)
                                print(f"      {account_num}: {balance:,.2f}")
                    else:
                        print(f"   ⚠️  Données vides ou incorrectes")
                        groups_empty += 1
                else:
                    print(f"   ⚠️  Pas de données structurées")
                    groups_empty += 1
            else:
                print(f"   ❌ Aucun contenu généré")
                groups_problematic += 1
            
            # Analyser les mappings spécifiques
            print(f"   📊 Analyse des préfixes:")
            matching_accounts = 0
            total_balance = 0
            
            for prefix in prefixes:
                # Rechercher les comptes correspondants
                accounts = AccountData.objects.filter(
                    financial_report_id=financial_report_id,
                    created_at__year=exercices[-1]  # N
                ).filter(
                    account_number__startswith=prefix
                )
                
                count = accounts.count()
                balance = sum(float(acc.balance) for acc in accounts)
                
                matching_accounts += count
                total_balance += balance
                
                if count > 0:
                    print(f"      ✅ {prefix}: {count} comptes, {balance:,.2f}")
                else:
                    print(f"      ❌ {prefix}: Aucun compte trouvé")
            
            print(f"   📊 Total: {matching_accounts} comptes, {total_balance:,.2f}")
            
            if matching_accounts > 0:
                print(f"   ✅ Mapping fonctionnel")
            else:
                print(f"   ❌ Mapping non fonctionnel")
        
        # Résumé final
        print(f"\n📊 RÉSUMÉ FINAL DES FEUILLES MAÎTRESSES:")
        print("=" * 50)
        print(f"   Total des groupes: {total_groups}")
        print(f"   Groupes avec données: {groups_with_data}")
        print(f"   Groupes vides: {groups_empty}")
        print(f"   Groupes problématiques: {groups_problematic}")
        
        # Calculer le pourcentage de réussite
        pourcentage_reussite = (groups_with_data / total_groups) * 100
        
        print(f"\n🎯 TAUX DE RÉUSSITE DES FEUILLES MAÎTRESSES: {pourcentage_reussite:.1f}%")
        
        if pourcentage_reussite >= 100:
            print("   🎉 PARFAIT ! Toutes les feuilles maîtresses sont correctement mappées !")
        elif pourcentage_reussite >= 90:
            print("   ✅ EXCELLENT ! Presque toutes les feuilles maîtresses sont correctement mappées !")
        elif pourcentage_reussite >= 80:
            print("   ✅ TRÈS BON ! La plupart des feuilles maîtresses sont correctement mappées !")
        elif pourcentage_reussite >= 70:
            print("   ✅ BON ! Taux de réussite acceptable pour les feuilles maîtresses !")
        else:
            print("   ⚠️  MOYEN ! Des améliorations sont nécessaires pour les feuilles maîtresses !")
        
        return pourcentage_reussite
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des feuilles maîtresses: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Fonction principale"""
    print("🎯 TEST FINAL DES FEUILLES MAÎTRESSES AVEC NOUVEAU MAPPING")
    print("=" * 70)
    
    score = test_final_master_sheets()
    
    print(f"\n🎉 RÉSULTAT FINAL:")
    if score >= 100:
        print("   🎉 PARFAIT ! Toutes les feuilles maîtresses sont correctement mappées !")
        print("   Le système est entièrement fonctionnel !")
    elif score >= 90:
        print("   ✅ EXCELLENT ! Presque toutes les feuilles maîtresses sont correctement mappées !")
        print("   Quelques ajustements mineurs pourraient être nécessaires.")
    else:
        print("   ⚠️  Des corrections supplémentaires sont nécessaires.")
        print("   Consultez les groupes problématiques ci-dessus.")

if __name__ == "__main__":
    main()
