from rest_framework import serializers

from .models import Email


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = (
            'id',
            'address',
            'is_verified',
            'is_primary',
            'label',
        )
