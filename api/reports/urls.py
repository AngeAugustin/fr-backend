from django.urls import path

from .views import BalanceUploadView, GeneratedFileDownloadView
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
                        'file_type': f.file_type,
                        'group_name': f.group_name,
                        'download_url': f'/api/reports/download-generated/{f.id}/',
                        'created_at': f.created_at
                    } for f in upload.generated_files.all()
                ]
            })
        return Response({'history': history})

urlpatterns = [
    path('upload-balance/', BalanceUploadView.as_view(), name='upload-balance'),
    path('balance-history/', BalanceHistoryView.as_view(), name='balance-history'),
    path('download-generated/<int:pk>/', GeneratedFileDownloadView.as_view(), name='download-generated'),
]
