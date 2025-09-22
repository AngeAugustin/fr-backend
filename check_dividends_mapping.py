#!/usr/bin/env python
"""
Script pour vérifier et corriger le mapping des dividendes versés (FM)
"""

import os
import sys
import django
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData

def check_dividends_accounts():
    """Vérifie les comptes de dividendes dans les données"""
    
    print("🔍 VÉRIFICATION DES COMPTES DE DIVIDENDES")
    print("=" * 50)
    
    # Comptes SYSCOHADA pour les dividendes versés
    dividends_accounts_syscohada = [
        '457',  # Dividendes à payer
        '108',  # Compte de l'exploitant (prélèvements)
        '675',  # Charges exceptionnelles - dividendes
        '775',  # Produits exceptionnels - dividendes
    ]
    
    print("📋 Comptes SYSCOHADA pour dividendes versés:")
    for account in dividends_accounts_syscohada:
        print(f"   - {account}")
    
    # Vérifier dans nos données
    print(f"\n🔍 Recherche dans les données AccountData:")
    
    for account in dividends_accounts_syscohada:
        # Recherche exacte
        exact_matches = AccountData.objects.filter(account_number=account)
        if exact_matches.exists():
            print(f"   ✅ {account}: {exact_matches.count()} enregistrement(s)")
            for match in exact_matches[:3]:  # Afficher les 3 premiers
                print(f"      - {match.account_number}: {match.account_label} (Solde: {match.balance})")
        else:
            # Recherche par préfixe
            prefix_matches = AccountData.objects.filter(account_number__startswith=account)
            if prefix_matches.exists():
                print(f"   ✅ {account}*: {prefix_matches.count()} enregistrement(s) avec préfixe")
                for match in prefix_matches[:3]:
                    print(f"      - {match.account_number}: {match.account_label} (Solde: {match.balance})")
            else:
                print(f"   ❌ {account}: Aucun compte trouvé")
    
    # Recherche plus large pour les dividendes
    print(f"\n🔍 Recherche élargie (dividendes, prélèvements, distributions):")
    
    keywords = ['dividende', 'prélèvement', 'distribution', 'exploitant', 'associé']
    
    for keyword in keywords:
        matches = AccountData.objects.filter(account_label__icontains=keyword)
        if matches.exists():
            print(f"   ✅ '{keyword}': {matches.count()} compte(s)")
            for match in matches[:3]:
                print(f"      - {match.account_number}: {match.account_label} (Solde: {match.balance})")
        else:
            print(f"   ❌ '{keyword}': Aucun compte trouvé")

def suggest_fm_mapping():
    """Suggère le mapping correct pour FM"""
    
    print(f"\n💡 SUGGESTION DE MAPPING POUR FM (DIVIDENDES VERSÉS):")
    print("-" * 50)
    
    print("Selon SYSCOHADA, FM devrait inclure:")
    print("1. Compte 457 - Dividendes à payer (variation)")
    print("2. Compte 108 - Compte de l'exploitant (prélèvements nets)")
    print("3. Compte 675 - Charges exceptionnelles (dividendes)")
    print("4. Compte 775 - Produits exceptionnels (dividendes)")
    
    print(f"\n📝 Correction suggérée dans tft_generator.py:")
    print("""
    {'ref': 'FM', 'libelle': 'Dividendes versés', 'formule': None, 'prefixes': ['457', '108', '675', '775']},
    """)
    
    # Vérifier si ces comptes existent dans nos données
    suggested_accounts = ['457', '108', '675', '775']
    existing_accounts = []
    
    for account in suggested_accounts:
        if AccountData.objects.filter(account_number=account).exists():
            existing_accounts.append(account)
    
    if existing_accounts:
        print(f"\n✅ Comptes disponibles dans nos données: {', '.join(existing_accounts)}")
    else:
        print(f"\n⚠️  Aucun des comptes suggérés n'existe dans nos données")
        print("   Cela explique pourquoi FM est vide")

def main():
    """Fonction principale"""
    print("🔍 ANALYSE DES DIVIDENDES VERSÉS (FM)")
    print("=" * 50)
    
    check_dividends_accounts()
    suggest_fm_mapping()
    
    print(f"\n🎯 CONCLUSION:")
    print("La rubrique FM est vide car elle n'est pas mappée aux comptes comptables.")
    print("Il faut corriger le mapping dans tft_generator.py pour inclure les comptes 457, 108, 675, 775.")

if __name__ == "__main__":
    main()
