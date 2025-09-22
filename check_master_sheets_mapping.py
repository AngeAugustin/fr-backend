#!/usr/bin/env python
"""
Vérification des mappings des feuilles maîtresses
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

def check_master_sheets_mapping():
    """Vérifie les mappings des feuilles maîtresses"""
    
    print("🔍 VÉRIFICATION DES MAPPINGS DES FEUILLES MAÎTRESSES")
    print("=" * 70)
    
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
        
        # Définir les groupes de feuilles maîtresses
        groups = {
            'financier': ['501', '502', '503', '504', '505', '506', '521', '522', '523', '524', '531', '532', '533', '541', '542', '58', '59'],
            'Clients-Ventes': ['411', '416', '417', '418', '419', '491', '701', '702', '703', '704', '705', '706', '707', '708', '781'],
            'Fournisseurs-Achats': ['401', '402', '403', '408', '409', '419', '601', '602', '603', '604', '605', '606', '607', '608'],
            'personnel': ['421', '422', '423', '424', '425', '43', '447', '661', '662', '663', '664', '665', '666', '667', '668'],
            'Impots-Taxes': ['441', '442', '443', '444', '445', '446', '447', '448', '449', '631', '633', '635', '695'],
            'Immobilisations Corporelles - Incorporelles': ['201', '203', '204', '205', '208', '211', '212', '213', '214', '215', '218', '237', '238'],
            'immobilisations_financieres': ['251', '256', '261', '262', '264', '265', '266', '267', '268', '269', '274', '275'],
            'stocks': ['311', '321', '322', '323', '331', '335', '341', '345', '351', '358', '39'],
            'capitaux_propres': ['101', '103', '104', '105', '106', '108', '109', '110', '130', '131'],
            'Provisions R-C': ['141', '142', '143', '148', '149'],
        }
        
        # Analyser chaque groupe de feuilles maîtresses
        print(f"\n📋 ANALYSE DES FEUILLES MAÎTRESSES:")
        print("=" * 50)
        
        total_groups = len(groups)
        groups_with_data = 0
        groups_empty = 0
        groups_problematic = 0
        
        for group_name, prefixes in groups.items():
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
        print(f"\n🔍 ANALYSE DÉTAILLÉE DES MAPPINGS:")
        print("=" * 50)
        
        # Vérifier chaque groupe individuellement
        for group_name, prefixes in groups.items():
            print(f"\n📊 {group_name.upper()}:")
            
            # Compter les comptes correspondants dans les données
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
                    print(f"   ✅ Préfixe {prefix}: {count} comptes, {balance:,.2f}")
                else:
                    print(f"   ❌ Préfixe {prefix}: Aucun compte trouvé")
            
            print(f"   📊 Total: {matching_accounts} comptes, {total_balance:,.2f}")
            
            if matching_accounts > 0:
                print(f"   ✅ Mapping fonctionnel")
            else:
                print(f"   ❌ Mapping non fonctionnel")
        
        # Résumé final
        print(f"\n📊 RÉSUMÉ DES FEUILLES MAÎTRESSES:")
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

def suggest_master_sheets_improvements():
    """Suggère des améliorations pour les feuilles maîtresses"""
    
    print(f"\n💡 SUGGESTIONS D'AMÉLIORATION:")
    print("=" * 50)
    
    # Définir les groupes pour l'analyse
    groups = {
        'financier': ['501', '502', '503', '504', '505', '506', '521', '522', '523', '524', '531', '532', '533', '541', '542', '58', '59'],
        'Clients-Ventes': ['411', '416', '417', '418', '419', '491', '701', '702', '703', '704', '705', '706', '707', '708', '781'],
        'Fournisseurs-Achats': ['401', '402', '403', '408', '409', '419', '601', '602', '603', '604', '605', '606', '607', '608'],
        'personnel': ['421', '422', '423', '424', '425', '43', '447', '661', '662', '663', '664', '665', '666', '667', '668'],
        'Impots-Taxes': ['441', '442', '443', '444', '445', '446', '447', '448', '449', '631', '633', '635', '695'],
        'Immobilisations Corporelles - Incorporelles': ['201', '203', '204', '205', '208', '211', '212', '213', '214', '215', '218', '237', '238'],
        'immobilisations_financieres': ['251', '256', '261', '262', '264', '265', '266', '267', '268', '269', '274', '275'],
        'stocks': ['311', '321', '322', '323', '331', '335', '341', '345', '351', '358', '39'],
        'capitaux_propres': ['101', '103', '104', '105', '106', '108', '109', '110', '130', '131'],
        'Provisions R-C': ['141', '142', '143', '148', '149'],
    }
    
    # Analyser les groupes existants
    print("📋 Groupes existants:")
    for group_name, prefixes in groups.items():
        print(f"   - {group_name}: {prefixes}")
    
    # Suggérer des améliorations basées sur les données réelles
    print(f"\n🔧 Améliorations suggérées:")
    print("1. Vérifier que tous les préfixes correspondent aux comptes réels")
    print("2. Ajouter des préfixes manquants pour les comptes non mappés")
    print("3. Optimiser les groupes pour une meilleure organisation")
    print("4. Vérifier la cohérence des calculs dans chaque groupe")

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION COMPLÈTE DES FEUILLES MAÎTRESSES")
    print("=" * 70)
    
    score = check_master_sheets_mapping()
    suggest_master_sheets_improvements()
    
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
