from rest_framework import serializers

class BalanceUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

class GeneratedFileCommentSerializer(serializers.Serializer):
    comment = serializers.CharField(max_length=2000, allow_blank=True, allow_null=True)