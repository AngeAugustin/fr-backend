from rest_framework import serializers

class BalanceUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
