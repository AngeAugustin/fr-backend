#!/usr/bin/env python
"""
Script de surveillance standalone pour le traitement automatique des données
Peut être exécuté indépendamment de Django
"""

import os
import sys
import django
import time
import logging
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fr_backend.settings')
django.setup()

from api.reports.models import AccountData, BalanceUpload
from api.reports.signals import process_financial_report_async

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataMonitor:
    """Moniteur de données pour traitement automatique"""
    
    def __init__(self, interval=60, min_accounts=10):
        self.interval = interval
        self.min_accounts = min_accounts
        self.running = False
        
    def start_monitoring(self):
        """Démarre la surveillance continue"""
        logger.info(f"🚀 Démarrage du moniteur de données")
        logger.info(f"   Intervalle: {self.interval} secondes")
        logger.info(f"   Seuil minimum: {self.min_accounts} comptes")
        
        self.running = True
        
        try:
            while self.running:
                self.check_new_data()
                logger.info(f"⏳ Attente de {self.interval} secondes...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt du moniteur demandé par l'utilisateur")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Erreur dans le moniteur: {str(e)}")
            self.running = False
    
    def check_new_data(self):
        """Vérifie et traite les nouvelles données"""
        logger.info(f"🔍 Vérification des nouvelles données - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Récupérer les financial_report_id non traités
        all_financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        processed_ids = BalanceUpload.objects.filter(
            financial_report_id__isnull=False
        ).values_list('financial_report_id', flat=True).distinct()
        
        unprocessed_ids = [fid for fid in all_financial_report_ids if fid and fid not in processed_ids]
        
        if not unprocessed_ids:
            logger.info("✅ Aucune nouvelle donnée à traiter")
            return
        
        logger.info(f"📊 {len(unprocessed_ids)} financial_report_id(s) non traité(s)")
        
        # Traiter chaque financial_report_id
        for financial_report_id in unprocessed_ids:
            try:
                account_count = AccountData.objects.filter(financial_report_id=financial_report_id).count()
                
                if account_count < self.min_accounts:
                    logger.warning(f"⚠️  {financial_report_id}: {account_count} comptes (seuil: {self.min_accounts})")
                    continue
                
                logger.info(f"🔄 Traitement de {financial_report_id} ({account_count} comptes)...")
                
                # Traiter le financial_report_id
                process_financial_report_async(financial_report_id)
                
                logger.info(f"✅ {financial_report_id}: Traité avec succès")
                
            except Exception as e:
                logger.error(f"❌ {financial_report_id}: Erreur - {str(e)}")
    
    def process_all_pending(self):
        """Traite toutes les données en attente une seule fois"""
        logger.info("🔄 Traitement unique de toutes les données en attente")
        self.check_new_data()
    
    def get_status(self):
        """Retourne le statut actuel du système"""
        all_financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        processed_ids = BalanceUpload.objects.filter(
            financial_report_id__isnull=False
        ).values_list('financial_report_id', flat=True).distinct()
        
        unprocessed_ids = [fid for fid in all_financial_report_ids if fid and fid not in processed_ids]
        
        status = {
            'total_financial_report_ids': len(all_financial_report_ids),
            'processed_ids': len(processed_ids),
            'unprocessed_ids': len(unprocessed_ids),
            'unprocessed_list': unprocessed_ids,
            'timestamp': datetime.now().isoformat()
        }
        
        return status

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Moniteur de données pour traitement automatique TFT')
    parser.add_argument('--interval', type=int, default=60, help='Intervalle de surveillance en secondes')
    parser.add_argument('--min-accounts', type=int, default=10, help='Nombre minimum de comptes requis')
    parser.add_argument('--once', action='store_true', help='Exécuter une seule fois')
    parser.add_argument('--status', action='store_true', help='Afficher le statut actuel')
    
    args = parser.parse_args()
    
    monitor = DataMonitor(interval=args.interval, min_accounts=args.min_accounts)
    
    if args.status:
        status = monitor.get_status()
        print(f"📊 Statut du système:")
        print(f"   Total financial_report_ids: {status['total_financial_report_ids']}")
        print(f"   Traités: {status['processed_ids']}")
        print(f"   En attente: {status['unprocessed_ids']}")
        if status['unprocessed_list']:
            print(f"   IDs en attente: {', '.join(map(str, status['unprocessed_list']))}")
        return
    
    if args.once:
        monitor.process_all_pending()
    else:
        monitor.start_monitoring()

if __name__ == "__main__":
    main()
