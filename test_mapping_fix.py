#!/usr/bin/env python
"""
Test spécifique pour vérifier que les mappings fonctionnent après correction
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

def test_mapping_fix():
    """Teste que les mappings fonctionnent après correction"""
    
    print("🧪 TEST DU MAPPING CORRIGÉ")
    print("=" * 50)
    
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
    
    # Générer le TFT
    try:
        tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
            financial_report_id, start_date, end_date
        )
        
        print(f"✅ TFT généré avec succès")
        
        # Vérifier les rubriques principales
        print(f"\n📋 RUBRIQUES PRINCIPALES:")
        
        main_rubriques = ['ZA', 'FA', 'FB', 'FC', 'FD', 'FE', 'BF', 'ZB', 'FF', 'FG', 'FH', 'FI', 'FJ', 'ZC', 'FK', 'FL', 'FM', 'FO', 'FP', 'ZE', 'G', 'ZH']
        
        rubriques_avec_valeur = 0
        rubriques_vides = 0
        rubriques_problematiques = 0
        
        for rubrique in main_rubriques:
            if rubrique in tft_data:
                data = tft_data[rubrique]
                if isinstance(data, dict) and 'montant' in data:
                    montant = data['montant']
                    if montant is None:
                        rubriques_problematiques += 1
                        print(f"   ❌ {rubrique}: None")
                    elif abs(montant) < 0.01:
                        rubriques_vides += 1
                        print(f"   ⚠️  {rubrique}: {montant:.2f} (vide)")
                    else:
                        rubriques_avec_valeur += 1
                        print(f"   ✅ {rubrique}: {montant:,.2f}")
                else:
                    rubriques_problematiques += 1
                    print(f"   ❌ {rubrique}: Données incorrectes")
            else:
                rubriques_problematiques += 1
                print(f"   ❌ {rubrique}: Absente")
        
        print(f"\n📊 RÉSUMÉ:")
        print(f"   Rubriques avec valeur: {rubriques_avec_valeur}")
        print(f"   Rubriques vides: {rubriques_vides}")
        print(f"   Rubriques problématiques: {rubriques_problematiques}")
        
        # Vérifier la cohérence
        print(f"\n🔍 COHÉRENCE TFT:")
        print(f"   Cohérent: {coherence.get('is_coherent', 'N/A')}")
        
        if coherence.get('is_coherent', False):
            print("   ✅ TFT cohérent")
        else:
            print("   ⚠️  TFT non cohérent")
            if 'details' in coherence:
                details = coherence['details']
                variation_tft = details.get('flux_operationnels', 0) + details.get('flux_investissement', 0) + details.get('flux_financement', 0)
                variation_treso = details.get('treso_cloture', 0) - details.get('treso_ouverture', 0)
                print(f"      Variation TFT: {variation_tft:,.2f}")
                print(f"      Variation Trésorerie: {variation_treso:,.2f}")
                print(f"      Écart: {abs(variation_tft - variation_treso):,.2f}")
        
        # Vérifier les feuilles maîtresses
        print(f"\n📋 FEUILLES MAÎTRESSES:")
        print(f"   Nombre de groupes: {len(sheets_contents)}")
        
        for group_name, content in sheets_contents.items():
            if content:
                print(f"   ✅ {group_name}: {len(content)} bytes")
            else:
                print(f"   ❌ {group_name}: Vide")
        
        # Évaluation finale
        print(f"\n🎯 ÉVALUATION FINALE:")
        score = (rubriques_avec_valeur / len(main_rubriques)) * 100
        
        if score >= 80:
            print(f"   ✅ EXCELLENT: {score:.1f}% des rubriques ont des valeurs")
        elif score >= 60:
            print(f"   ✅ BON: {score:.1f}% des rubriques ont des valeurs")
        elif score >= 40:
            print(f"   ⚠️  MOYEN: {score:.1f}% des rubriques ont des valeurs")
        else:
            print(f"   ❌ INSUFFISANT: {score:.1f}% des rubriques ont des valeurs")
        
        return score >= 40
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération TFT: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🔧 TEST DE LA CORRECTION DU MAPPING")
    print("=" * 60)
    
    success = test_mapping_fix()
    
    if success:
        print(f"\n🎉 SUCCÈS: Le mapping fonctionne maintenant !")
        print("Les données sont correctement exploitées.")
    else:
        print(f"\n❌ ÉCHEC: Le mapping ne fonctionne toujours pas.")
        print("Des corrections supplémentaires sont nécessaires.")

if __name__ == "__main__":
    main()
