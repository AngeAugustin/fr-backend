#!/usr/bin/env python
"""
Analyse précise des problèmes pour atteindre 100% de réussite
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

def analyze_specific_issues():
    """Analyse précise des problèmes spécifiques"""
    
    print("🔍 ANALYSE PRÉCISE DES PROBLÈMES")
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
    
    # 1. Analyser les comptes de trésorerie (ZA, G, ZH)
    print(f"\n🔍 PROBLÈME 1: COMPTES DE TRÉSORERIE (ZA, G, ZH)")
    print("-" * 50)
    
    treso_accounts = ['50', '51', '53']
    treso_found = {}
    
    for prefix in treso_accounts:
        # Rechercher les comptes correspondants
        matching_accounts = []
        for account in AccountData.objects.filter(financial_report_id=financial_report_id):
            account_str = str(account.account_number)
            if '-' in account_str:
                clean_prefix = account_str.split('-')[0]
                if clean_prefix.startswith('0000'):
                    clean_prefix = clean_prefix[4:]
                else:
                    clean_prefix = clean_prefix.lstrip('0')
                
                if clean_prefix.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
            else:
                if account_str.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
        
        treso_found[prefix] = matching_accounts
        print(f"   Préfixe {prefix}: {len(matching_accounts)} comptes trouvés")
        for acc, bal in matching_accounts[:5]:
            print(f"      {acc}: {bal:,.2f}")
    
    # 2. Analyser les comptes d'investissement (FF, FG, FH, FI, FJ, ZC)
    print(f"\n🔍 PROBLÈME 2: COMPTES D'INVESTISSEMENT (FF, FG, FH, FI, FJ, ZC)")
    print("-" * 50)
    
    inv_accounts = ['20', '21', '26', '27', '251', '261', '262']
    inv_found = {}
    
    for prefix in inv_accounts:
        matching_accounts = []
        for account in AccountData.objects.filter(financial_report_id=financial_report_id):
            account_str = str(account.account_number)
            if '-' in account_str:
                clean_prefix = account_str.split('-')[0]
                if clean_prefix.startswith('0000'):
                    clean_prefix = clean_prefix[4:]
                else:
                    clean_prefix = clean_prefix.lstrip('0')
                
                if clean_prefix.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
            else:
                if account_str.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
        
        inv_found[prefix] = matching_accounts
        print(f"   Préfixe {prefix}: {len(matching_accounts)} comptes trouvés")
        for acc, bal in matching_accounts[:3]:
            print(f"      {acc}: {bal:,.2f}")
    
    # 3. Analyser les comptes de financement (FO, FP, ZE)
    print(f"\n🔍 PROBLÈME 3: COMPTES DE FINANCEMENT (FO, FP, ZE)")
    print("-" * 50)
    
    fin_accounts = ['15', '16', '17', '18', '19']
    fin_found = {}
    
    for prefix in fin_accounts:
        matching_accounts = []
        for account in AccountData.objects.filter(financial_report_id=financial_report_id):
            account_str = str(account.account_number)
            if '-' in account_str:
                clean_prefix = account_str.split('-')[0]
                if clean_prefix.startswith('0000'):
                    clean_prefix = clean_prefix[4:]
                else:
                    clean_prefix = clean_prefix.lstrip('0')
                
                if clean_prefix.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
            else:
                if account_str.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
        
        fin_found[prefix] = matching_accounts
        print(f"   Préfixe {prefix}: {len(matching_accounts)} comptes trouvés")
        for acc, bal in matching_accounts[:3]:
            print(f"      {acc}: {bal:,.2f}")
    
    # 4. Analyser les comptes de subventions (FL)
    print(f"\n🔍 PROBLÈME 4: COMPTES DE SUBVENTIONS (FL)")
    print("-" * 50)
    
    subv_accounts = ['14']
    subv_found = {}
    
    for prefix in subv_accounts:
        matching_accounts = []
        for account in AccountData.objects.filter(financial_report_id=financial_report_id):
            account_str = str(account.account_number)
            if '-' in account_str:
                clean_prefix = account_str.split('-')[0]
                if clean_prefix.startswith('0000'):
                    clean_prefix = clean_prefix[4:]
                else:
                    clean_prefix = clean_prefix.lstrip('0')
                
                if clean_prefix.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
            else:
                if account_str.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
        
        subv_found[prefix] = matching_accounts
        print(f"   Préfixe {prefix}: {len(matching_accounts)} comptes trouvés")
        for acc, bal in matching_accounts[:3]:
            print(f"      {acc}: {bal:,.2f}")
    
    # 5. Analyser les comptes de dividendes (FM)
    print(f"\n🔍 PROBLÈME 5: COMPTES DE DIVIDENDES (FM)")
    print("-" * 50)
    
    div_accounts = ['457', '108', '675', '775']
    div_found = {}
    
    for prefix in div_accounts:
        matching_accounts = []
        for account in AccountData.objects.filter(financial_report_id=financial_report_id):
            account_str = str(account.account_number)
            if '-' in account_str:
                clean_prefix = account_str.split('-')[0]
                if clean_prefix.startswith('0000'):
                    clean_prefix = clean_prefix[4:]
                else:
                    clean_prefix = clean_prefix.lstrip('0')
                
                if clean_prefix.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
            else:
                if account_str.startswith(prefix):
                    matching_accounts.append((account.account_number, account.balance))
        
        div_found[prefix] = matching_accounts
        print(f"   Préfixe {prefix}: {len(matching_accounts)} comptes trouvés")
        for acc, bal in matching_accounts[:3]:
            print(f"      {acc}: {bal:,.2f}")
    
    return {
        'treso': treso_found,
        'investissement': inv_found,
        'financement': fin_found,
        'subventions': subv_found,
        'dividendes': div_found
    }

def main():
    """Fonction principale"""
    print("🔍 ANALYSE PRÉCISE POUR ATTEINDRE 100% DE RÉUSSITE")
    print("=" * 70)
    
    issues = analyze_specific_issues()
    
    print(f"\n💡 PLAN DE CORRECTION:")
    print("=" * 30)
    
    # Analyser les résultats
    total_issues = 0
    fixable_issues = 0
    
    for category, accounts in issues.items():
        for prefix, matching in accounts.items():
            if len(matching) == 0:
                total_issues += 1
                print(f"   ❌ {category} - {prefix}: Aucun compte trouvé")
            else:
                fixable_issues += 1
                print(f"   ✅ {category} - {prefix}: {len(matching)} comptes trouvés")
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   Problèmes identifiés: {total_issues}")
    print(f"   Problèmes résolvables: {fixable_issues}")
    
    if total_issues == 0:
        print("   🎉 Tous les comptes nécessaires sont présents !")
    else:
        print("   ⚠️  Des corrections sont nécessaires")

if __name__ == "__main__":
    main()
