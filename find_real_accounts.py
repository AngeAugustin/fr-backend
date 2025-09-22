#!/usr/bin/env python
"""
Trouve les vrais comptes correspondant aux catégories SYSCOHADA
"""

import os
import sys
import django
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData

def find_real_accounts():
    """Trouve les vrais comptes correspondant aux catégories SYSCOHADA"""
    
    print("🔍 RECHERCHE DES VRAIS COMPTES CORRESPONDANTS")
    print("=" * 60)
    
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
        balance__gt=10000  # Seuil de 10K pour les comptes significatifs
    ).values_list('account_number', 'account_label', 'balance')
    
    print(f"📊 COMPTES AVEC SOLDES SIGNIFICATIFS (>10K): {len(significant_accounts)}")
    
    # Classer par catégorie selon les libellés
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
        
        # Classification par mots-clés dans les libellés
        if any(word in label_lower for word in ['banque', 'caisse', 'trésorerie', 'chèque', 'virement']):
            categories['Trésorerie'].append((account, label, balance))
        elif any(word in label_lower for word in ['client', 'créance', 'facture', 'vente', 'chiffre']):
            categories['Créances'].append((account, label, balance))
        elif any(word in label_lower for word in ['fournisseur', 'dette', 'emprunt', 'prêt', 'découvert']):
            categories['Dettes'].append((account, label, balance))
        elif any(word in label_lower for word in ['produit', 'vente', 'chiffre', 'chiffre d\'affaires', 'ca']):
            categories['Produits'].append((account, label, balance))
        elif any(word in label_lower for word in ['charge', 'achat', 'personnel', 'salaire', 'amortissement']):
            categories['Charges'].append((account, label, balance))
        elif any(word in label_lower for word in ['immobilisation', 'matériel', 'mobilier', 'terrain', 'bâtiment']):
            categories['Immobilisations'].append((account, label, balance))
        elif any(word in label_lower for word in ['capital', 'résultat', 'bénéfice', 'perte', 'associé']):
            categories['Capitaux propres'].append((account, label, balance))
        elif any(word in label_lower for word in ['stock', 'marchandise', 'matière', 'produit fini']):
            categories['Stocks'].append((account, label, balance))
        else:
            categories['Autres'].append((account, label, balance))
    
    # Afficher les résultats
    for category, accounts in categories.items():
        if accounts:
            print(f"\n📋 {category.upper()}: {len(accounts)} comptes")
            for account, label, balance in accounts[:10]:  # Afficher les 10 premiers
                print(f"   {account}: {label} - {balance:,.2f}")
    
    return categories

def suggest_mapping_corrections(categories):
    """Suggère les corrections de mapping"""
    
    print(f"\n💡 CORRECTIONS DE MAPPING SUGGÉRÉES:")
    print("=" * 60)
    
    # 1. Trésorerie (ZA, G, ZH)
    treso_accounts = categories.get('Trésorerie', [])
    if treso_accounts:
        print(f"\n🔧 1. TRÉSORERIE (ZA, G, ZH):")
        print("   Comptes trouvés:")
        for account, label, balance in treso_accounts[:5]:
            print(f"      {account}: {label}")
        
        # Extraire les préfixes
        treso_prefixes = set()
        for account, _, _ in treso_accounts:
            if '-' in account:
                prefix = account.split('-')[0]
                if prefix.startswith('0000'):
                    clean_prefix = prefix[4:]
                else:
                    clean_prefix = prefix.lstrip('0')
                treso_prefixes.add(clean_prefix)
            else:
                treso_prefixes.add(account[:3])
        
        print(f"   Préfixes à utiliser: {sorted(treso_prefixes)}")
    
    # 2. Investissement (FF, FG, FH, FI, FJ, ZC)
    inv_accounts = categories.get('Immobilisations', [])
    if inv_accounts:
        print(f"\n🔧 2. INVESTISSEMENT (FF, FG, FH, FI, FJ, ZC):")
        print("   Comptes trouvés:")
        for account, label, balance in inv_accounts[:5]:
            print(f"      {account}: {label}")
        
        # Extraire les préfixes
        inv_prefixes = set()
        for account, _, _ in inv_accounts:
            if '-' in account:
                prefix = account.split('-')[0]
                if prefix.startswith('0000'):
                    clean_prefix = prefix[4:]
                else:
                    clean_prefix = prefix.lstrip('0')
                inv_prefixes.add(clean_prefix)
            else:
                inv_prefixes.add(account[:3])
        
        print(f"   Préfixes à utiliser: {sorted(inv_prefixes)}")
    
    # 3. Financement (FO, FP, ZE)
    fin_accounts = categories.get('Dettes', [])
    if fin_accounts:
        print(f"\n🔧 3. FINANCEMENT (FO, FP, ZE):")
        print("   Comptes trouvés:")
        for account, label, balance in fin_accounts[:5]:
            print(f"      {account}: {label}")
        
        # Extraire les préfixes
        fin_prefixes = set()
        for account, _, _ in fin_accounts:
            if '-' in account:
                prefix = account.split('-')[0]
                if prefix.startswith('0000'):
                    clean_prefix = prefix[4:]
                else:
                    clean_prefix = prefix.lstrip('0')
                fin_prefixes.add(clean_prefix)
            else:
                fin_prefixes.add(account[:3])
        
        print(f"   Préfixes à utiliser: {sorted(fin_prefixes)}")
    
    # 4. Subventions (FL)
    subv_accounts = [acc for acc in categories.get('Capitaux propres', []) if 'subvention' in str(acc[1]).lower()]
    if subv_accounts:
        print(f"\n🔧 4. SUBVENTIONS (FL):")
        print("   Comptes trouvés:")
        for account, label, balance in subv_accounts[:5]:
            print(f"      {account}: {label}")
    
    # 5. Dividendes (FM)
    div_accounts = [acc for acc in categories.get('Capitaux propres', []) if any(word in str(acc[1]).lower() for word in ['dividende', 'prélèvement', 'associé'])]
    if div_accounts:
        print(f"\n🔧 5. DIVIDENDES (FM):")
        print("   Comptes trouvés:")
        for account, label, balance in div_accounts[:5]:
            print(f"      {account}: {label}")

def main():
    """Fonction principale"""
    print("🔍 RECHERCHE DES VRAIS COMPTES POUR 100% DE RÉUSSITE")
    print("=" * 70)
    
    categories = find_real_accounts()
    suggest_mapping_corrections(categories)
    
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    print("1. Identifier les vrais préfixes de comptes")
    print("2. Mettre à jour les mappings dans tft_generator.py")
    print("3. Tester les corrections une par une")
    print("4. Atteindre 100% de réussite !")

if __name__ == "__main__":
    main()
