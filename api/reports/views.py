from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse, Http404
from .models import GeneratedFile, BalanceUpload
from .serializers import GeneratedFileCommentSerializer
import os

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

