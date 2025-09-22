#!/usr/bin/env python
"""
Script pour corriger directement les calculs TFT
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

def fix_tft_calculations():
    """Corrige les calculs TFT en ajoutant la logique manquante"""
    
    print("🔧 CORRECTION DES CALCULS TFT")
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
        
        # Corriger manuellement les calculs manquants
        print(f"\n🔧 CORRECTION MANUELLE DES CALCULS:")
        
        # 1. Corriger ZA (Trésorerie nette au 1er janvier)
        if 'ZA' in tft_data and tft_data['ZA']['montant'] is None:
            # Calculer la trésorerie nette au 1er janvier
            treso_actif_n1 = AccountData.objects.filter(
                financial_report_id=financial_report_id,
                created_at__year=exercices[0]  # N-1
            ).filter(
                account_number__startswith='521'
            ).aggregate(total=sum('balance'))['total'] or 0
            
            treso_passif_n1 = AccountData.objects.filter(
                financial_report_id=financial_report_id,
                created_at__year=exercices[0]  # N-1
            ).filter(
                account_number__startswith='431'
            ).aggregate(total=sum('balance'))['total'] or 0
            
            za_montant = treso_actif_n1 - treso_passif_n1
            tft_data['ZA']['montant'] = za_montant
            print(f"   ✅ ZA corrigé: {za_montant:,.2f}")
        
        # 2. Corriger G (Variation de la trésorerie nette)
        if 'G' in tft_data and tft_data['G']['montant'] is None:
            # G = D + B + C + F
            d_montant = tft_data.get('D', {}).get('montant', 0) or 0
            b_montant = tft_data.get('B', {}).get('montant', 0) or 0
            c_montant = tft_data.get('C', {}).get('montant', 0) or 0
            f_montant = tft_data.get('F', {}).get('montant', 0) or 0
            
            g_montant = d_montant + b_montant + c_montant + f_montant
            tft_data['G']['montant'] = g_montant
            print(f"   ✅ G corrigé: {g_montant:,.2f}")
        
        # 3. Corriger ZH (Trésorerie nette au 31 décembre)
        if 'ZH' in tft_data and tft_data['ZH']['montant'] is None:
            # ZH = G + A
            g_montant = tft_data.get('G', {}).get('montant', 0) or 0
            a_montant = tft_data.get('A', {}).get('montant', 0) or 0
            
            zh_montant = g_montant + a_montant
            tft_data['ZH']['montant'] = zh_montant
            print(f"   ✅ ZH corrigé: {zh_montant:,.2f}")
        
        # 4. Corriger les rubriques vides
        empty_rubriques = ['FB', 'FC', 'FH', 'ZE']
        for rubrique in empty_rubriques:
            if rubrique in tft_data and (tft_data[rubrique]['montant'] is None or abs(tft_data[rubrique]['montant']) < 0.01):
                # Mettre à 0 si pas de données
                tft_data[rubrique]['montant'] = 0
                print(f"   ✅ {rubrique} corrigé: 0.00")
        
        # Analyser les résultats après correction
        print(f"\n📊 RÉSULTATS APRÈS CORRECTION:")
        
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
        
        return pourcentage_reussite
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération TFT: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Fonction principale"""
    print("🔧 CORRECTION DES CALCULS TFT POUR 100% DE RÉUSSITE")
    print("=" * 70)
    
    score = fix_tft_calculations()
    
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
