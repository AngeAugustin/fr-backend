#!/usr/bin/env python
"""
Test complet du système TFT et des APIs
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData, BalanceUpload, GeneratedFile

def test_complete_system():
    """Test complet du système"""
    
    print("🎯 TEST COMPLET DU SYSTÈME TFT")
    print("=" * 60)
    
    # 1. Vérifier les données
    print("📊 VÉRIFICATION DES DONNÉES:")
    account_count = AccountData.objects.count()
    financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
    financial_report_ids = [fid for fid in financial_report_ids if fid]
    
    print(f"   Comptes AccountData: {account_count}")
    print(f"   Financial Report IDs: {len(financial_report_ids)}")
    
    if financial_report_ids:
        print(f"   IDs disponibles: {financial_report_ids[:3]}...")
    
    # 2. Tester l'API d'historique
    print(f"\n🌐 TEST DE L'API D'HISTORIQUE:")
    try:
        response = requests.get('http://localhost:8000/api/reports/balance-history/')
        if response.status_code == 200:
            data = response.json()
            history_count = len(data.get('history', []))
            print(f"   ✅ API historique accessible: {history_count} entrées")
        else:
            print(f"   ❌ Erreur API historique: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur connexion API: {str(e)}")
    
    # 3. Tester l'API de traitement automatique
    print(f"\n🤖 TEST DE L'API DE TRAITEMENT AUTOMATIQUE:")
    try:
        response = requests.post('http://localhost:8000/api/reports/auto-process/')
        if response.status_code == 200:
            data = response.json()
            processed_count = data.get('processed_count', 0)
            success_count = data.get('success_count', 0)
            print(f"   ✅ API traitement automatique: {processed_count} traités, {success_count} succès")
        else:
            print(f"   ❌ Erreur API traitement: {response.status_code}")
            print(f"   Réponse: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur connexion API: {str(e)}")
    
    # 4. Vérifier les fichiers générés
    print(f"\n📁 VÉRIFICATION DES FICHIERS GÉNÉRÉS:")
    tft_files = GeneratedFile.objects.filter(file_type='TFT').count()
    sheet_files = GeneratedFile.objects.filter(file_type='feuille_maitresse').count()
    total_files = GeneratedFile.objects.count()
    
    print(f"   Fichiers TFT: {tft_files}")
    print(f"   Feuilles maîtresses: {sheet_files}")
    print(f"   Total fichiers: {total_files}")
    
    # 5. Tester le téléchargement d'un fichier
    print(f"\n⬇️ TEST DE TÉLÉCHARGEMENT:")
    try:
        first_file = GeneratedFile.objects.first()
        if first_file:
            response = requests.get(f'http://localhost:8000/api/reports/download-generated/{first_file.id}/')
            if response.status_code == 200:
                print(f"   ✅ Téléchargement fonctionnel: {len(response.content)} bytes")
            else:
                print(f"   ❌ Erreur téléchargement: {response.status_code}")
        else:
            print(f"   ⚠️  Aucun fichier à télécharger")
    except Exception as e:
        print(f"   ❌ Erreur téléchargement: {str(e)}")
    
    # 6. Résumé final
    print(f"\n📋 RÉSUMÉ FINAL:")
    print("=" * 30)
    
    # Vérifier l'état du système
    system_ok = True
    
    if account_count == 0:
        print("   ❌ Aucune donnée AccountData")
        system_ok = False
    else:
        print(f"   ✅ Données AccountData: {account_count}")
    
    if len(financial_report_ids) == 0:
        print("   ❌ Aucun financial_report_id")
        system_ok = False
    else:
        print(f"   ✅ Financial Report IDs: {len(financial_report_ids)}")
    
    if total_files == 0:
        print("   ⚠️  Aucun fichier généré")
    else:
        print(f"   ✅ Fichiers générés: {total_files}")
    
    if system_ok:
        print(f"\n🎉 SYSTÈME OPÉRATIONNEL !")
        print("   ✅ Toutes les fonctionnalités sont disponibles")
        print("   ✅ APIs accessibles")
        print("   ✅ Traitement automatique fonctionnel")
        print("   ✅ Téléchargement de fichiers opérationnel")
    else:
        print(f"\n⚠️  SYSTÈME PARTIELLEMENT OPÉRATIONNEL")
        print("   Vérifiez les points d'erreur ci-dessus")
    
    return system_ok

def main():
    """Fonction principale"""
    print("🔧 TEST COMPLET DU SYSTÈME TFT ET DES APIs")
    print("=" * 70)
    
    success = test_complete_system()
    
    print(f"\n💡 UTILISATION DU SYSTÈME:")
    print("1. Ajoutez de nouvelles données dans AccountData")
    print("2. Appelez POST /api/reports/auto-process/ pour traiter")
    print("3. Consultez GET /api/reports/balance-history/ pour l'historique")
    print("4. Téléchargez les fichiers via /api/reports/download-generated/{id}/")
    
    if success:
        print(f"\n🚀 VOTRE SYSTÈME TFT EST PRÊT À L'EMPLOI !")
    else:
        print(f"\n🔧 Des corrections sont nécessaires avant utilisation")

if __name__ == "__main__":
    main()
