#!/usr/bin/env python
"""
Script pour corriger les mappings des feuilles maîtresses
"""

import os
import sys
import django
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData

def analyze_real_account_prefixes():
    """Analyse les vrais préfixes de comptes dans les données"""
    
    print("🔍 ANALYSE DES VRAIS PRÉFIXES POUR LES FEUILLES MAÎTRESSES")
    print("=" * 70)
    
    # Récupérer un financial_report_id pour test
    financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
    financial_report_ids = [fid for fid in financial_report_ids if fid]
    
    if not financial_report_ids:
        print("❌ Aucune donnée disponible")
        return
    
    financial_report_id = financial_report_ids[0]
    
    # Analyser tous les comptes avec des soldes significatifs
    significant_accounts = AccountData.objects.filter(
        financial_report_id=financial_report_id,
        balance__gt=1000  # Seuil de 1K pour les comptes significatifs
    ).values_list('account_number', 'account_label', 'balance')
    
    print(f"📊 COMPTES AVEC SOLDES SIGNIFICATIFS (>1K): {len(significant_accounts)}")
    
    # Classer par catégorie selon les libellés et numéros
    categories = {
        'Trésorerie': [],
        'Créances': [],
        'Dettes': [],
        'Produits': [],
        'Charges': [],
        'Immobilisations': [],
        'Capitaux propres': [],
        'Stocks': [],
        'Autres': []
    }
    
    for account, label, balance in significant_accounts:
        label_lower = str(label).lower() if label else ""
        account_str = str(account)
        
        # Extraire le préfixe réel
        if '-' in account_str:
            prefix = account_str.split('-')[0]
            if prefix.startswith('0000'):
                clean_prefix = prefix[4:]
            else:
                clean_prefix = prefix.lstrip('0')
        else:
            clean_prefix = account_str[:3]
        
        # Classification par mots-clés dans les libellés
        if any(word in label_lower for word in ['banque', 'caisse', 'trésorerie', 'chèque', 'virement']):
            categories['Trésorerie'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['client', 'créance', 'facture', 'vente', 'chiffre']):
            categories['Créances'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['fournisseur', 'dette', 'emprunt', 'prêt', 'découvert']):
            categories['Dettes'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['produit', 'vente', 'chiffre', 'chiffre d\'affaires', 'ca']):
            categories['Produits'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['charge', 'achat', 'personnel', 'salaire', 'amortissement']):
            categories['Charges'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['immobilisation', 'matériel', 'mobilier', 'terrain', 'bâtiment']):
            categories['Immobilisations'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['capital', 'résultat', 'bénéfice', 'perte', 'associé']):
            categories['Capitaux propres'].append((account, label, balance, clean_prefix))
        elif any(word in label_lower for word in ['stock', 'marchandise', 'matière', 'produit fini']):
            categories['Stocks'].append((account, label, balance, clean_prefix))
        else:
            categories['Autres'].append((account, label, balance, clean_prefix))
    
    # Afficher les résultats
    print(f"\n📋 RÉSULTATS PAR CATÉGORIE:")
    for category, accounts in categories.items():
        if accounts:
            print(f"\n📊 {category.upper()}: {len(accounts)} comptes")
            
            # Extraire les préfixes uniques
            prefixes = set()
            for account, label, balance, prefix in accounts:
                prefixes.add(prefix)
            
            print(f"   Préfixes trouvés: {sorted(prefixes)}")
            
            # Afficher quelques exemples
            for account, label, balance, prefix in accounts[:5]:
                print(f"   {account} ({prefix}): {label} - {balance:,.2f}")
    
    return categories

def suggest_new_master_sheets_mapping(categories):
    """Suggère un nouveau mapping pour les feuilles maîtresses"""
    
    print(f"\n💡 NOUVEAU MAPPING SUGGÉRÉ POUR LES FEUILLES MAÎTRESSES:")
    print("=" * 70)
    
    # Construire le nouveau mapping basé sur les données réelles
    new_groups = {}
    
    # 1. Trésorerie
    treso_accounts = categories.get('Trésorerie', [])
    if treso_accounts:
        treso_prefixes = set()
        for account, label, balance, prefix in treso_accounts:
            treso_prefixes.add(prefix)
        new_groups['financier'] = sorted(list(treso_prefixes))
        print(f"✅ financier: {new_groups['financier']}")
    
    # 2. Créances et Ventes
    creances_accounts = categories.get('Créances', [])
    produits_accounts = categories.get('Produits', [])
    if creances_accounts or produits_accounts:
        creances_prefixes = set()
        for account, label, balance, prefix in creances_accounts:
            creances_prefixes.add(prefix)
        for account, label, balance, prefix in produits_accounts:
            creances_prefixes.add(prefix)
        new_groups['Clients-Ventes'] = sorted(list(creances_prefixes))
        print(f"✅ Clients-Ventes: {new_groups['Clients-Ventes']}")
    
    # 3. Dettes et Achats
    dettes_accounts = categories.get('Dettes', [])
    charges_accounts = categories.get('Charges', [])
    if dettes_accounts or charges_accounts:
        dettes_prefixes = set()
        for account, label, balance, prefix in dettes_accounts:
            dettes_prefixes.add(prefix)
        for account, label, balance, prefix in charges_accounts:
            dettes_prefixes.add(prefix)
        new_groups['Fournisseurs-Achats'] = sorted(list(dettes_prefixes))
        print(f"✅ Fournisseurs-Achats: {new_groups['Fournisseurs-Achats']}")
    
    # 4. Personnel
    personnel_accounts = [acc for acc in charges_accounts if any(word in str(acc[1]).lower() for word in ['personnel', 'salaire', 'charge sociale'])]
    if personnel_accounts:
        personnel_prefixes = set()
        for account, label, balance, prefix in personnel_accounts:
            personnel_prefixes.add(prefix)
        new_groups['personnel'] = sorted(list(personnel_prefixes))
        print(f"✅ personnel: {new_groups['personnel']}")
    
    # 5. Impôts et Taxes
    impots_accounts = [acc for acc in charges_accounts if any(word in str(acc[1]).lower() for word in ['impôt', 'taxe', 'tva', 'fiscal'])]
    if impots_accounts:
        impots_prefixes = set()
        for account, label, balance, prefix in impots_accounts:
            impots_prefixes.add(prefix)
        new_groups['Impots-Taxes'] = sorted(list(impots_prefixes))
        print(f"✅ Impots-Taxes: {new_groups['Impots-Taxes']}")
    
    # 6. Immobilisations
    immo_accounts = categories.get('Immobilisations', [])
    if immo_accounts:
        immo_prefixes = set()
        for account, label, balance, prefix in immo_accounts:
            immo_prefixes.add(prefix)
        new_groups['Immobilisations'] = sorted(list(immo_prefixes))
        print(f"✅ Immobilisations: {new_groups['Immobilisations']}")
    
    # 7. Stocks
    stocks_accounts = categories.get('Stocks', [])
    if stocks_accounts:
        stocks_prefixes = set()
        for account, label, balance, prefix in stocks_accounts:
            stocks_prefixes.add(prefix)
        new_groups['stocks'] = sorted(list(stocks_prefixes))
        print(f"✅ stocks: {new_groups['stocks']}")
    
    # 8. Capitaux propres
    cap_propres_accounts = categories.get('Capitaux propres', [])
    if cap_propres_accounts:
        cap_prefixes = set()
        for account, label, balance, prefix in cap_propres_accounts:
            cap_prefixes.add(prefix)
        new_groups['capitaux_propres'] = sorted(list(cap_prefixes))
        print(f"✅ capitaux_propres: {new_groups['capitaux_propres']}")
    
    return new_groups

def main():
    """Fonction principale"""
    print("🔧 CORRECTION DES MAPPINGS DES FEUILLES MAÎTRESSES")
    print("=" * 70)
    
    categories = analyze_real_account_prefixes()
    new_groups = suggest_new_master_sheets_mapping(categories)
    
    print(f"\n🎯 NOUVEAU MAPPING COMPLET:")
    print("=" * 40)
    for group_name, prefixes in new_groups.items():
        print(f"{group_name}: {prefixes}")
    
    print(f"\n💡 PROCHAINES ÉTAPES:")
    print("1. Mettre à jour le fichier tft_generator.py avec ce nouveau mapping")
    print("2. Tester les feuilles maîtresses avec le nouveau mapping")
    print("3. Atteindre 100% de réussite pour les feuilles maîtresses !")

if __name__ == "__main__":
    main()
