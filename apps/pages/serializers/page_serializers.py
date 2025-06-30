from rest_framework import serializers
from apps.pages.models import URLRecord

class URLRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = URLRecord
        fields = ['id', 'url_pattern', 'name', 'show_name']
