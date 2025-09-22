#!/usr/bin/env python
"""
Diagnostic simple des obstacles à l'exploitation des données
"""

import os
import sys
import django
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData, BalanceUpload, GeneratedFile

def main():
    """Diagnostic simple"""
    
    print("🔍 DIAGNOSTIC SIMPLE - OBSTACLES À L'EXPLOITATION")
    print("=" * 60)
    
    # 1. Vérifier les données de base
    print("📊 DONNÉES DE BASE:")
    total_accounts = AccountData.objects.count()
    print(f"   Total enregistrements: {total_accounts}")
    
    if total_accounts == 0:
        print("❌ PROBLÈME MAJEUR: Aucune donnée")
        return
    
    # 2. Vérifier les financial_report_ids
    financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
    financial_report_ids = [fid for fid in financial_report_ids if fid]
    print(f"   Financial Report IDs: {len(financial_report_ids)}")
    
    # 3. Vérifier les exercices
    exercices = set()
    for data in AccountData.objects.all()[:1000]:  # Échantillon
        exercices.add(data.created_at.year)
    
    exercices = sorted(exercices)
    print(f"   Exercices: {exercices}")
    
    # 4. Vérifier les types de données
    print(f"\n🔍 TYPES DE DONNÉES:")
    sample = AccountData.objects.first()
    if sample:
        print(f"   account_number: {type(sample.account_number)}")
        print(f"   balance: {type(sample.balance)}")
        print(f"   total_debit: {type(sample.total_debit)}")
        print(f"   total_credit: {type(sample.total_credit)}")
        print(f"   created_at: {type(sample.created_at)}")
    
    # 5. Vérifier les soldes
    print(f"\n📊 SOLDES:")
    positive = AccountData.objects.filter(balance__gt=0).count()
    negative = AccountData.objects.filter(balance__lt=0).count()
    zero = AccountData.objects.filter(balance=0).count()
    
    print(f"   Positifs: {positive}")
    print(f"   Négatifs: {negative}")
    print(f"   Zéro: {zero}")
    
    # 6. Vérifier les comptes uniques
    unique_accounts = AccountData.objects.values_list('account_number', flat=True).distinct().count()
    print(f"   Comptes uniques: {unique_accounts}")
    
    # 7. Vérifier les problèmes potentiels
    print(f"\n⚠️  PROBLÈMES POTENTIELS:")
    
    # Vérifier les comptes avec des numéros bizarres
    weird_accounts = AccountData.objects.exclude(account_number__regex=r'^[0-9]+$').count()
    if weird_accounts > 0:
        print(f"   ❌ Comptes avec numéros non-numériques: {weird_accounts}")
    
    # Vérifier les soldes extrêmes
    extreme_balances = AccountData.objects.filter(
        balance__gt=1000000
    ).count()
    if extreme_balances > 0:
        print(f"   ⚠️  Comptes avec soldes > 1M: {extreme_balances}")
    
    # Vérifier les dates
    future_dates = AccountData.objects.filter(created_at__gt=datetime.now()).count()
    if future_dates > 0:
        print(f"   ⚠️  Dates futures: {future_dates}")
    
    # 8. Vérifier les mappings
    print(f"\n🗺️  MAPPINGS:")
    
    # Comptes SYSCOHADA principaux
    syscohada_main = ['101', '401', '411', '501', '521', '601', '701']
    mapped_count = 0
    
    for account in syscohada_main:
        if AccountData.objects.filter(account_number=account).exists():
            mapped_count += 1
            print(f"   ✅ {account}: Présent")
        else:
            print(f"   ❌ {account}: Absent")
    
    print(f"   Score mapping: {mapped_count}/{len(syscohada_main)}")
    
    # 9. Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    
    if weird_accounts > 0:
        print("   - Nettoyer les numéros de comptes non-numériques")
    
    if mapped_count < len(syscohada_main) * 0.5:
        print("   - Vérifier la structure du plan comptable")
    
    if unique_accounts < 100:
        print("   - Vérifier la diversité des comptes")
    
    print("   - Vérifier la cohérence des exercices")
    print("   - S'assurer que les soldes sont corrects")
    
    print(f"\n🎯 CONCLUSION:")
    if total_accounts > 0 and len(financial_report_ids) > 0 and len(exercices) > 0:
        print("✅ Les données de base sont présentes et exploitables")
        print("⚠️  Vérifiez les mappings et la cohérence des calculs")
    else:
        print("❌ Problèmes majeurs détectés - données non exploitables")

if __name__ == "__main__":
    main()
