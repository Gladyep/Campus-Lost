from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'reporter', 'reported_user', 'item', 'reason', 'status', 'decision_reason', 'created_at', 'reviewed_at')
        read_only_fields = ('id', 'reporter', 'status', 'decision_reason', 'created_at', 'reviewed_at')