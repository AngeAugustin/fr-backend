"""
Commande Django pour surveiller et traiter automatiquement les nouvelles données
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from api.reports.models import AccountData, BalanceUpload
from api.reports.signals import process_financial_report_async
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Surveille et traite automatiquement les nouvelles données AccountData'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Intervalle de surveillance en secondes (défaut: 60)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Exécuter une seule fois au lieu de surveiller en continu'
        )
        parser.add_argument(
            '--min-accounts',
            type=int,
            default=10,
            help='Nombre minimum de comptes requis pour traiter (défaut: 10)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        min_accounts = options['min_accounts']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Démarrage de la surveillance automatique des données\n'
                f'   Intervalle: {interval} secondes\n'
                f'   Mode: {"Une fois" if run_once else "Continu"}\n'
                f'   Seuil minimum: {min_accounts} comptes'
            )
        )
        
        if run_once:
            self.process_new_data(min_accounts)
        else:
            self.monitor_continuously(interval, min_accounts)

    def process_new_data(self, min_accounts):
        """Traite toutes les nouvelles données non traitées"""
        self.stdout.write('🔍 Recherche des nouvelles données...')
        
        # Récupérer tous les financial_report_id non traités
        all_financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        processed_ids = BalanceUpload.objects.filter(
            financial_report_id__isnull=False
        ).values_list('financial_report_id', flat=True).distinct()
        
        unprocessed_ids = [fid for fid in all_financial_report_ids if fid and fid not in processed_ids]
        
        if not unprocessed_ids:
            self.stdout.write(
                self.style.WARNING('⚠️  Aucune nouvelle donnée à traiter')
            )
            return
        
        self.stdout.write(f'📊 {len(unprocessed_ids)} financial_report_id(s) à traiter')
        
        success_count = 0
        error_count = 0
        
        for financial_report_id in unprocessed_ids:
            try:
                # Vérifier le nombre de comptes
                account_count = AccountData.objects.filter(financial_report_id=financial_report_id).count()
                
                if account_count < min_accounts:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  {financial_report_id}: {account_count} comptes (seuil: {min_accounts})'
                        )
                    )
                    continue
                
                self.stdout.write(f'🔄 Traitement de {financial_report_id} ({account_count} comptes)...')
                
                # Traiter le financial_report_id
                process_financial_report_async(financial_report_id)
                success_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {financial_report_id}: Traité avec succès')
                )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ {financial_report_id}: Erreur - {str(e)}')
                )
        
        # Résumé
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Résumé du traitement:\n'
                f'   ✅ Succès: {success_count}\n'
                f'   ❌ Erreurs: {error_count}\n'
                f'   📈 Total: {len(unprocessed_ids)}'
            )
        )

    def monitor_continuously(self, interval, min_accounts):
        """Surveille en continu les nouvelles données"""
        import time
        
        self.stdout.write('🔄 Surveillance continue activée...')
        self.stdout.write('   Appuyez sur Ctrl+C pour arrêter')
        
        try:
            while True:
                self.stdout.write(f'\n⏰ {timezone.now().strftime("%Y-%m-%d %H:%M:%S")} - Vérification...')
                
                # Compter les nouvelles données
                all_financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
                processed_ids = BalanceUpload.objects.filter(
                    financial_report_id__isnull=False
                ).values_list('financial_report_id', flat=True).distinct()
                
                unprocessed_ids = [fid for fid in all_financial_report_ids if fid and fid not in processed_ids]
                
                if unprocessed_ids:
                    self.stdout.write(f'📊 {len(unprocessed_ids)} nouvelle(s) donnée(s) détectée(s)')
                    self.process_new_data(min_accounts)
                else:
                    self.stdout.write('✅ Aucune nouvelle donnée')
                
                # Attendre l'intervalle suivant
                self.stdout.write(f'⏳ Attente de {interval} secondes...')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\n🛑 Surveillance arrêtée par l\'utilisateur')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Erreur lors de la surveillance: {str(e)}')
            )
