from django.db.models import Q
from rest_framework import permissions, viewsets

from .models import Match
from .serializers import MatchSerializer


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Match.objects.filter(
            Q(lost_item__reporter=self.request.user) | Q(found_item__reporter=self.request.user)
        ).filter(
            lost_item__status='OPEN', found_item__status='OPEN'
        ).select_related('lost_item', 'found_item').order_by('-match_score')