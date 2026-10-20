from rest_framework import serializers

from .models import Match


class MatchSerializer(serializers.ModelSerializer):
    lost_title = serializers.CharField(source='lost_item.title', read_only=True)
    found_title = serializers.CharField(source='found_item.title', read_only=True)
    lost_reporter_id = serializers.IntegerField(source='lost_item.reporter_id', read_only=True)
    found_reporter_id = serializers.IntegerField(source='found_item.reporter_id', read_only=True)
    lost_description = serializers.CharField(source='lost_item.description', read_only=True)
    found_description = serializers.CharField(source='found_item.description', read_only=True)
    lost_location = serializers.CharField(source='lost_item.location', read_only=True)
    found_location = serializers.CharField(source='found_item.location', read_only=True)
    lost_event_date = serializers.DateField(source='lost_item.event_date', read_only=True)
    found_event_date = serializers.DateField(source='found_item.event_date', read_only=True)
    lost_status = serializers.CharField(source='lost_item.status', read_only=True)
    found_status = serializers.CharField(source='found_item.status', read_only=True)
    lost_category = serializers.CharField(source='lost_item.category.name', read_only=True)
    found_category = serializers.CharField(source='found_item.category.name', read_only=True)
    lost_image = serializers.SerializerMethodField()
    found_image = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = (
            'id', 'lost_item', 'found_item', 'lost_reporter_id', 'found_reporter_id',
            'lost_title', 'found_title', 'lost_description', 'found_description',
            'lost_location', 'found_location', 'lost_event_date', 'found_event_date',
            'lost_status', 'found_status', 'lost_category', 'found_category',
            'lost_image', 'found_image', 'match_score', 'updated_at',
        )

    def get_lost_image(self, match):
        return self._image_url(match.lost_item)

    def get_found_image(self, match):
        return self._image_url(match.found_item)

    def _image_url(self, item):
        image = next(iter(item.images.all()), None)
        if image is None:
            return ''
        request = self.context.get('request')
        try:
            url = image.image.url
        except ValueError:
            return ''
        return request.build_absolute_uri(url) if request else url