from rest_framework import serializers
from .models import AuditEntry


class AuditEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEntry
        fields = [
            'id', 'user_name', 'user_role', 'action',
            'entity_type', 'entity_id', 'details',
            'ip_address', 'timestamp',
        ]
