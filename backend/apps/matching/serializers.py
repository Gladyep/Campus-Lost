from rest_framework import serializers

from .models import Match


class MatchSerializer(serializers.ModelSerializer):
    lost_title = serializers.CharField(source='lost_item.title', read_only=True)
    found_title = serializers.CharField(source='found_item.title', read_only=True)
    lost_location = serializers.CharField(source='lost_item.location', read_only=True)
    found_location = serializers.CharField(source='found_item.location', read_only=True)

    class Meta:
        model = Match
        fields = ('id', 'lost_item', 'found_item', 'lost_title', 'found_title', 'lost_location', 'found_location', 'match_score', 'updated_at')