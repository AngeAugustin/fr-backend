from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, Http404
from .models import GeneratedFile, BalanceUpload, AccountData
from .serializers import GeneratedFileCommentSerializer
from .tft_generator import generate_tft_and_sheets_from_database
import os
from datetime import datetime, date
import math
import pandas as pd
import numpy as np

def determine_tft_dates(financial_report_id):
    """
    Détermine les dates de début et fin pour le TFT selon la logique SYSCOHADA
    - Si N et N-1 disponibles : 01/01/N-1 à 31/12/N
    - Si N uniquement : 01/01/N à 31/12/N
    """
    account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
    
    # Analyser les exercices disponibles
    exercices = set()
    for data in account_data:
        exercices.add(data.created_at.year)
    
    exercices = sorted(exercices)
    
    if len(exercices) >= 2:
        # N-1 et N disponibles : 01/01/N-1 à 31/12/N
        n_1 = exercices[-2]  # N-1
        n = exercices[-1]    # N
        start_date = date(n_1, 1, 1)   # 01/01/N-1
        end_date = date(n, 12, 31)     # 31/12/N
    elif len(exercices) == 1:
        # Un seul exercice : 01/01/N à 31/12/N
        n = exercices[0]
        start_date = date(n, 1, 1)     # 01/01/N
        end_date = date(n, 12, 31)     # 31/12/N
    else:
        # Aucun exercice détecté
        raise ValueError("Aucun exercice détecté dans les données")
    
    return start_date, end_date

class GeneratedFileDownloadView(APIView):
    def get(self, request, pk):
        try:
            gen_file = GeneratedFile.objects.get(pk=pk)
        except GeneratedFile.DoesNotExist:
            raise Http404("Fichier non trouvé")
        if not gen_file.file_content:
            return Response({'error': 'Aucun contenu binaire enregistré.'}, status=404)
        response = HttpResponse(gen_file.file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Génération du nom de fichier avec type et "generated"
        if gen_file.file_type == 'TFT':
            filename = f"generated_tft_{pk}.xlsx"
        elif gen_file.file_type == 'feuille_maitresse':
            group_name = gen_file.group_name or 'feuille'
            filename = f"generated_feuille_maitresse_{group_name}_{pk}.xlsx"
        else:
            filename = f"generated_{gen_file.file_type}_{pk}.xlsx"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BalanceUploadSerializer
from django.core.files.storage import default_storage
from django.conf import settings
import os
from .tft_generator import generate_tft_and_sheets

from .models import BalanceUpload, GeneratedFile

class BalanceUploadView(APIView):
    def post(self, request):
        serializer = BalanceUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            # Enregistrement de l'upload
            balance_upload = BalanceUpload.objects.create(
                file=file,
                start_date=start_date,
                end_date=end_date,
                user=request.user if request.user.is_authenticated else None
            )
            abs_path = balance_upload.file.path
            try:
                # Nouvelle version : la fonction doit retourner le contenu binaire des fichiers générés
                tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets(abs_path, start_date, end_date)
                # Enregistrement du fichier TFT uniquement en base
                GeneratedFile.objects.create(
                    balance_upload=balance_upload,
                    file_type='TFT',
                    file_content=tft_content
                )
                # Enregistrement des feuilles maîtresses uniquement en base
                for group_name, sheet_content in sheets_contents.items():
                    GeneratedFile.objects.create(
                        balance_upload=balance_upload,
                        file_type='feuille_maitresse',
                        group_name=group_name,
                        file_content=sheet_content
                    )
                balance_upload.status = 'success'
                balance_upload.save()
                # Préparation de la réponse avec les fichiers et les données JSON
                # Préparation de l'historique avec liens de téléchargement
                history = {
                    'id': balance_upload.id,
                    'file': balance_upload.file.url,
                    'start_date': balance_upload.start_date,
                    'end_date': balance_upload.end_date,
                    'uploaded_at': balance_upload.uploaded_at,
                    'status': balance_upload.status,
                    'generated_files': [
                        {
                            'id': f.id,
                            'file_type': f.file_type,
                            'group_name': f.group_name,
                            'download_url': f'/api/reports/download-generated/{f.id}/',
                            'comment': f.comment,  # Commentaire de chaque feuille maîtresse
                            'created_at': f.created_at
                        } for f in balance_upload.generated_files.all()
                    ]
                }
                import math
                import pandas as pd
                import numpy as np
                def sanitize(obj):
                    if isinstance(obj, dict):
                        return {k: sanitize(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [sanitize(v) for v in obj]
                    elif isinstance(obj, (np.integer, np.int32, np.int64)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float32, np.float64)):
                        if math.isnan(obj) or math.isinf(obj):
                            return None
                        return float(obj)
                    elif isinstance(obj, float):
                        if math.isnan(obj) or math.isinf(obj):
                            return None
                        return obj
                    elif isinstance(obj, pd.Timestamp):
                        return obj.isoformat()
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    else:
                        return obj
                tft_data_clean = sanitize(tft_data)
                sheets_data_clean = sanitize(sheets_data)
                # Stockage des données JSON dans BalanceUpload
                balance_upload.tft_json = tft_data_clean
                balance_upload.feuilles_maitresses_json = sheets_data_clean
                balance_upload.coherence_json = coherence
                balance_upload.save()
                return Response({
                    'tft_json': tft_data_clean,
                    'feuilles_maitresses_json': sheets_data_clean,
                    'coherence': coherence,
                    'history': history
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                balance_upload.status = 'error'
                balance_upload.error_message = str(e)
                balance_upload.save()
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GeneratedFileCommentView(APIView):
    """
    API pour ajouter ou mettre à jour un commentaire sur une feuille maîtresse spécifique.
    Accepte POST et PUT sur le même endpoint.
    """
    def post(self, request, generated_file_id):
        """Ajouter ou mettre à jour un commentaire sur une feuille maîtresse"""
        try:
            generated_file = GeneratedFile.objects.get(id=generated_file_id)
        except GeneratedFile.DoesNotExist:
            return Response({'error': 'Feuille maîtresse non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = GeneratedFileCommentSerializer(data=request.data)
        if serializer.is_valid():
            generated_file.comment = serializer.validated_data.get('comment')
            generated_file.save()
            return Response({
                'message': 'Commentaire ajouté/mis à jour avec succès',
                'comment': generated_file.comment,
                'generated_file_id': generated_file.id,
                'group_name': generated_file.group_name,
                'file_type': generated_file.file_type
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, generated_file_id):
        """Mettre à jour un commentaire (même logique que POST)"""
        return self.post(request, generated_file_id)

class ProcessAccountDataView(APIView):
    """Vue pour traiter automatiquement les données AccountData et générer les rapports"""
    
    def post(self, request):
        """Traite les données AccountData et génère les rapports automatiquement"""
        financial_report_id = request.data.get('financial_report_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not all([financial_report_id, start_date, end_date]):
            return Response({
                'error': 'financial_report_id, start_date et end_date sont requis'
            }, status=400)
        
        # Vérifier si les données existent
        account_data = AccountData.objects.filter(financial_report_id=financial_report_id)
        if not account_data.exists():
            return Response({
                'error': f'Aucune donnée trouvée pour financial_report_id: {financial_report_id}'
            }, status=404)
        
        # Vérifier si un traitement existe déjà pour ce financial_report_id
        existing_upload = BalanceUpload.objects.filter(financial_report_id=financial_report_id).first()
        if existing_upload:
            return Response({
                'message': 'Traitement déjà effectué pour ce financial_report_id',
                'balance_upload_id': existing_upload.id,
                'status': existing_upload.status
            }, status=200)
        
        try:
            # Créer un BalanceUpload pour l'historique
            balance_upload = BalanceUpload.objects.create(
                file=None,  # Pas de fichier uploadé
                start_date=start_date,
                end_date=end_date,
                user=request.user if request.user.is_authenticated else None,
                status='processing',
                financial_report_id=financial_report_id
            )
            
            # Générer les rapports depuis la base de données
            tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
                financial_report_id, start_date, end_date
            )
            
            # Enregistrer le fichier TFT
            GeneratedFile.objects.create(
                balance_upload=balance_upload,
                file_type='TFT',
                file_content=tft_content
            )
            
            # Enregistrer les feuilles maîtresses
            for group_name, sheet_content in sheets_contents.items():
                GeneratedFile.objects.create(
                    balance_upload=balance_upload,
                    file_type='feuille_maitresse',
                    group_name=group_name,
                    file_content=sheet_content
                )
            
            # Fonction de nettoyage des données pour JSON
            def sanitize(obj):
                if isinstance(obj, dict):
                    return {k: sanitize(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [sanitize(v) for v in obj]
                elif isinstance(obj, (np.integer, np.int32, np.int64)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float32, np.float64)):
                    if math.isnan(obj) or math.isinf(obj):
                        return None
                    return float(obj)
                elif isinstance(obj, float):
                    if math.isnan(obj) or math.isinf(obj):
                        return None
                    return obj
                elif isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
            
            # Nettoyer les données pour le JSON
            tft_data_clean = sanitize(tft_data)
            sheets_data_clean = sanitize(sheets_data)
            
            # Mettre à jour le BalanceUpload avec les résultats
            balance_upload.status = 'success'
            balance_upload.tft_json = tft_data_clean
            balance_upload.feuilles_maitresses_json = sheets_data_clean
            balance_upload.coherence_json = coherence
            balance_upload.save()
            
            # Préparer l'historique avec liens de téléchargement
            history = {
                'id': balance_upload.id,
                'file': None,  # Pas de fichier uploadé
                'start_date': balance_upload.start_date,
                'end_date': balance_upload.end_date,
                'uploaded_at': balance_upload.uploaded_at,
                'status': balance_upload.status,
                'financial_report_id': balance_upload.financial_report_id,
                'generated_files': [
                    {
                        'id': f.id,
                        'file_type': f.file_type,
                        'group_name': f.group_name,
                        'download_url': f'/api/reports/download-generated/{f.id}/',
                        'comment': f.comment,
                        'created_at': f.created_at
                    } for f in balance_upload.generated_files.all()
                ]
            }
            
            return Response({
                'message': 'Traitement effectué avec succès',
                'balance_upload_id': balance_upload.id,
                'tft_json': tft_data_clean,
                'feuilles_maitresses_json': sheets_data_clean,
                'coherence': coherence,
                'history': history
            }, status=201)
            
        except Exception as e:
            # En cas d'erreur, marquer le traitement comme échoué
            if 'balance_upload' in locals():
                balance_upload.status = 'error'
                balance_upload.error_message = str(e)
                balance_upload.save()
            
            return Response({
                'error': f'Erreur lors du traitement: {str(e)}'
            }, status=500)
    
    def get(self, request):
        """Liste tous les financial_report_id disponibles dans AccountData"""
        financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        processed_ids = BalanceUpload.objects.filter(
            financial_report_id__isnull=False
        ).values_list('financial_report_id', flat=True).distinct()
        
        available_ids = []
        for fid in financial_report_ids:
            if fid:  # Ignorer les valeurs vides
                available_ids.append({
                    'financial_report_id': fid,
                    'processed': fid in processed_ids,
                    'account_count': AccountData.objects.filter(financial_report_id=fid).count()
                })
        
        return Response({
            'available_financial_report_ids': available_ids
        })

class AutoProcessView(APIView):
    """Vue pour traiter automatiquement toutes les nouvelles données AccountData"""
    
    def post(self, request):
        """Traite automatiquement toutes les données AccountData non traitées"""
        # Récupérer tous les financial_report_id non traités
        all_financial_report_ids = AccountData.objects.values_list('financial_report_id', flat=True).distinct()
        processed_ids = BalanceUpload.objects.filter(
            financial_report_id__isnull=False
        ).values_list('financial_report_id', flat=True).distinct()
        
        unprocessed_ids = [fid for fid in all_financial_report_ids if fid and fid not in processed_ids]
        
        if not unprocessed_ids:
            return Response({
                'message': 'Aucune nouvelle donnée à traiter',
                'processed_count': 0
            })
        
        results = []
        success_count = 0
        
        for financial_report_id in unprocessed_ids:
            try:
                # Déterminer les dates selon la logique SYSCOHADA
                start_date, end_date = determine_tft_dates(financial_report_id)
                
                # Créer un BalanceUpload
                balance_upload = BalanceUpload.objects.create(
                    file=None,
                    start_date=start_date,
                    end_date=end_date,
                    user=request.user if request.user.is_authenticated else None,
                    status='processing',
                    financial_report_id=financial_report_id
                )
                
                # Générer les rapports
                tft_content, sheets_contents, tft_data, sheets_data, coherence = generate_tft_and_sheets_from_database(
                    financial_report_id, start_date, end_date
                )
                
                # Enregistrer les fichiers
                GeneratedFile.objects.create(
                    balance_upload=balance_upload,
                    file_type='TFT',
                    file_content=tft_content
                )
                
                for group_name, sheet_content in sheets_contents.items():
                    GeneratedFile.objects.create(
                        balance_upload=balance_upload,
                        file_type='feuille_maitresse',
                        group_name=group_name,
                        file_content=sheet_content
                    )
                
                # Fonction de nettoyage
                def sanitize(obj):
                    if isinstance(obj, dict):
                        return {k: sanitize(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [sanitize(v) for v in obj]
                    elif isinstance(obj, (np.integer, np.int32, np.int64)):
                        return int(obj)
                    elif isinstance(obj, (np.floating, np.float32, np.float64)):
                        if math.isnan(obj) or math.isinf(obj):
                            return None
                        return float(obj)
                    elif isinstance(obj, float):
                        if math.isnan(obj) or math.isinf(obj):
                            return None
                        return obj
                    elif isinstance(obj, pd.Timestamp):
                        return obj.isoformat()
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    else:
                        return obj
                
                # Mettre à jour le BalanceUpload
                balance_upload.status = 'success'
                balance_upload.tft_json = sanitize(tft_data)
                balance_upload.feuilles_maitresses_json = sanitize(sheets_data)
                balance_upload.coherence_json = coherence
                balance_upload.save()
                
                results.append({
                    'financial_report_id': financial_report_id,
                    'status': 'success',
                    'balance_upload_id': balance_upload.id,
                    'start_date': start_date,
                    'end_date': end_date
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    'financial_report_id': financial_report_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return Response({
            'message': f'Traitement automatique terminé',
            'total_processed': len(unprocessed_ids),
            'success_count': success_count,
            'error_count': len(unprocessed_ids) - success_count,
            'results': results
        })

