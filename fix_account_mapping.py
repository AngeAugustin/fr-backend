#!/usr/bin/env python
"""
Script pour corriger le mapping des comptes selon le format réel
"""

import os
import sys
import django
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData

def analyze_real_account_structure():
    """Analyse la structure réelle des comptes"""
    
    print("🔍 ANALYSE DE LA STRUCTURE RÉELLE DES COMPTES")
    print("=" * 60)
    
    # Analyser les comptes avec des soldes significatifs
    significant_accounts = AccountData.objects.filter(balance__gt=100000).values_list('account_number', 'account_label', 'balance')
    
    print("📊 COMPTES AVEC SOLDES SIGNIFICATIFS (>100K):")
    for account, label, balance in significant_accounts[:20]:
        print(f"   {account}: {label} - {balance:,.2f}")
    
    # Analyser les préfixes les plus communs
    print(f"\n📋 PRÉFIXES LES PLUS COMMUNS:")
    prefixes = {}
    for account, label, balance in significant_accounts:
        if '-' in account:
            prefix = account.split('-')[0]
            if prefix.startswith('0000'):
                clean_prefix = prefix[4:]  # Enlever les 0000
            else:
                clean_prefix = prefix
            
            if clean_prefix not in prefixes:
                prefixes[clean_prefix] = {'count': 0, 'total_balance': 0, 'examples': []}
            
            prefixes[clean_prefix]['count'] += 1
            prefixes[clean_prefix]['total_balance'] += float(balance)
            if len(prefixes[clean_prefix]['examples']) < 3:
                prefixes[clean_prefix]['examples'].append(account)
    
    # Trier par solde total
    sorted_prefixes = sorted(prefixes.items(), key=lambda x: x[1]['total_balance'], reverse=True)
    
    for prefix, data in sorted_prefixes[:15]:
        print(f"   {prefix}: {data['count']} comptes, {data['total_balance']:,.2f} total")
        print(f"      Exemples: {data['examples']}")
    
    return sorted_prefixes

def suggest_new_mapping():
    """Suggère un nouveau mapping basé sur la structure réelle"""
    
    print(f"\n💡 SUGGESTION DE NOUVEAU MAPPING:")
    print("=" * 60)
    
    # Analyser les comptes par catégorie
    categories = {
        'Trésorerie': [],
        'Créances': [],
        'Dettes': [],
        'Produits': [],
        'Charges': [],
        'Immobilisations': [],
        'Capitaux propres': []
    }
    
    # Analyser les comptes significatifs
    significant_accounts = AccountData.objects.filter(balance__gt=100000).values_list('account_number', 'account_label', 'balance')
    
    for account, label, balance in significant_accounts:
        if '-' in account:
            prefix = account.split('-')[0]
            if prefix.startswith('0000'):
                clean_prefix = prefix[4:]
            else:
                clean_prefix = prefix
            
            # Classer par préfixe
            if clean_prefix.startswith('2'):
                categories['Immobilisations'].append((account, label, balance))
            elif clean_prefix.startswith('4'):
                categories['Créances'].append((account, label, balance))
            elif clean_prefix.startswith('5'):
                categories['Trésorerie'].append((account, label, balance))
            elif clean_prefix.startswith('6'):
                categories['Charges'].append((account, label, balance))
            elif clean_prefix.startswith('7'):
                categories['Produits'].append((account, label, balance))
            elif clean_prefix.startswith('1'):
                categories['Capitaux propres'].append((account, label, balance))
    
    # Afficher les catégories
    for category, accounts in categories.items():
        if accounts:
            print(f"\n📊 {category.upper()}:")
            for account, label, balance in accounts[:5]:
                print(f"   {account}: {label} - {balance:,.2f}")
    
    # Suggérer le nouveau mapping
    print(f"\n🔧 NOUVEAU MAPPING SUGGÉRÉ:")
    print("""
    # Adapter le mapping aux formats réels
    def filter_by_prefix(df, prefixes):
        def match_prefix(acc):
            acc = str(acc)
            if '-' in acc:
                # Format: 0000279-01 -> 279
                prefix = acc.split('-')[0]
                if prefix.startswith('0000'):
                    clean_prefix = prefix[4:]
                else:
                    clean_prefix = prefix
                
                for p in prefixes:
                    if clean_prefix.startswith(p):
                        return True
            else:
                # Format: 66411000
                for p in prefixes:
                    if acc.startswith(p):
                        return True
            return False
        return df[df['account_number'].apply(match_prefix)]
    """)

def main():
    """Fonction principale"""
    print("🔧 CORRECTION DU MAPPING DES COMPTES")
    print("=" * 60)
    
    analyze_real_account_structure()
    suggest_new_mapping()
    
    print(f"\n🎯 CONCLUSION:")
    print("Le problème principal est que les numéros de comptes sont au format")
    print("'0000279-01' au lieu de '279', ce qui empêche le mapping SYSCOHADA.")
    print("Il faut adapter la fonction filter_by_prefix pour gérer ce format.")

if __name__ == "__main__":
    main()
