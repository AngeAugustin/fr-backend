from django.urls import path

from .views import BalanceUploadView, GeneratedFileDownloadView, GeneratedFileCommentView, ProcessAccountDataView, AutoProcessView
from .models import BalanceUpload
from rest_framework.views import APIView
from rest_framework.response import Response

class BalanceHistoryView(APIView):
    def get(self, request):
        uploads = BalanceUpload.objects.order_by('-uploaded_at')
        history = []
        for upload in uploads:
            history.append({
                'id': upload.id,
                'file': upload.file.url if upload.file else None,
                'start_date': upload.start_date,
                'end_date': upload.end_date,
                'uploaded_at': upload.uploaded_at,
                'status': upload.status,
                'error_message': upload.error_message,
                'generated_files': [
                    {
                        'id': f.id,
                        'file_type': f.file_type,
                        'group_name': f.group_name,
                        'download_url': f'/api/reports/download-generated/{f.id}/',
                        'comment': f.comment,  # Commentaire de chaque feuille maîtresse
                        'created_at': f.created_at
                    } for f in upload.generated_files.all()
                ],
                'tft_json': upload.tft_json,
                'feuilles_maitresses_json': upload.feuilles_maitresses_json,
                'coherence': upload.coherence_json
            })
        return Response({'history': history})

urlpatterns = [
    path('upload-balance/', BalanceUploadView.as_view(), name='upload-balance'),
    path('balance-history/', BalanceHistoryView.as_view(), name='balance-history'),
    path('download-generated/<int:pk>/', GeneratedFileDownloadView.as_view(), name='download-generated'),
    path('comment/<int:generated_file_id>/', GeneratedFileCommentView.as_view(), name='comment'),
    # Nouvelles URLs pour le traitement automatique
    path('process-account-data/', ProcessAccountDataView.as_view(), name='process-account-data'),
    path('auto-process/', AutoProcessView.as_view(), name='auto-process'),
]
