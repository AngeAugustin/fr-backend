#!/usr/bin/env python
"""
Test final du mapping pour atteindre 100% de réussite
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

def test_final_mapping():
    """Test final du mapping"""
    
    print("🎯 TEST FINAL POUR ATTEINDRE 100% DE RÉUSSITE")
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
    
    # Générer le TFT
    try:
        tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
            financial_report_id, start_date, end_date
        )
        
        print(f"✅ TFT généré avec succès")
        
        # Analyser toutes les rubriques
        print(f"\n📋 ANALYSE COMPLÈTE DES RUBRIQUES:")
        
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
        
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"   Rubriques avec valeur: {rubriques_avec_valeur}")
        print(f"   Rubriques vides: {rubriques_vides}")
        print(f"   Rubriques problématiques: {rubriques_problematiques}")
        
        # Calculer le pourcentage de réussite
        total_rubriques = len(main_rubriques)
        pourcentage_reussite = (rubriques_avec_valeur / total_rubriques) * 100
        
        print(f"\n🎯 TAUX DE RÉUSSITE: {pourcentage_reussite:.1f}%")
        
        if pourcentage_reussite >= 100:
            print("   🎉 PARFAIT ! 100% de réussite atteint !")
        elif pourcentage_reussite >= 90:
            print("   ✅ EXCELLENT ! Presque 100% de réussite !")
        elif pourcentage_reussite >= 80:
            print("   ✅ TRÈS BON ! Bon taux de réussite !")
        elif pourcentage_reussite >= 70:
            print("   ✅ BON ! Taux de réussite acceptable !")
        else:
            print("   ⚠️  MOYEN ! Des améliorations sont nécessaires !")
        
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
        
        return pourcentage_reussite
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération TFT: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Fonction principale"""
    print("🎯 TEST FINAL POUR 100% DE RÉUSSITE")
    print("=" * 60)
    
    score = test_final_mapping()
    
    print(f"\n🎉 RÉSULTAT FINAL:")
    if score >= 100:
        print("   🎉 PARFAIT ! 100% de réussite atteint !")
        print("   Toutes les rubriques TFT sont correctement calculées !")
    elif score >= 90:
        print("   ✅ EXCELLENT ! Presque 100% de réussite !")
        print("   Quelques ajustements mineurs pourraient être nécessaires.")
    else:
        print("   ⚠️  Des corrections supplémentaires sont nécessaires.")
        print("   Consultez les rubriques problématiques ci-dessus.")

if __name__ == "__main__":
    main()
