from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.claims.models import Claim
from apps.items.models import Item
from .models import AuditLog, Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'head', 'options')

    def get_queryset(self):
        queryset = Report.objects.select_related('reporter', 'reported_user', 'item')
        return queryset if self.request.user.is_staff else queryset.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        if not serializer.validated_data.get('item') and not serializer.validated_data.get('reported_user'):
            raise ValidationError('A report must identify an item or a user.')
        with transaction.atomic():
            report = serializer.save(reporter=self.request.user)
            from apps.communication.services import notify_moderation_report_created

            notify_moderation_report_created(report, self.request.user)


class AdminDashboardView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        return Response({
            'open_items': Item.objects.filter(status=Item.Status.OPEN).count(),
            'pending_claims': Claim.objects.filter(status__in=(Claim.Status.PENDING, Claim.Status.UNDER_VERIFICATION, Claim.Status.FLAGGED, Claim.Status.DISPUTED)).count(),
            'pending_reports': Report.objects.filter(status=Report.Status.PENDING).count(),
            'recent_reports': list(Report.objects.filter(status=Report.Status.PENDING).values(
                'id', 'reason', 'created_at', 'item__title', 'reported_user__name',
            )[:10]),
        })


class FlaggedClaimsView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        claims = Claim.objects.filter(status__in=(Claim.Status.FLAGGED, Claim.Status.DISPUTED)).select_related('item', 'claimant')
        return Response([{
            'id': claim.id,
            'item_title': claim.item.title,
            'claimant_name': claim.claimant.name,
            'status': claim.status,
            'submitted_at': claim.submitted_at,
        } for claim in claims])


class ReportDecisionView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, report_id):
        decision = request.data.get('status')
        reason = str(request.data.get('reason', '')).strip()[:500]
        if decision not in (Report.Status.RESOLVED, Report.Status.DISMISSED):
            raise ValidationError({'status': 'Choose RESOLVED or DISMISSED.'})
        with transaction.atomic():
            report = Report.objects.select_for_update().get(pk=report_id)
            report.status = decision
            report.decision_reason = reason
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
            report.save(update_fields=('status', 'decision_reason', 'reviewed_by', 'reviewed_at'))
            AuditLog.objects.create(actor=request.user, action=f'report_{decision.lower()}', entity_type='report', entity_id=str(report.pk), metadata={'reason': reason})
            from apps.communication.services import notify_moderation_report_decision

            notify_moderation_report_decision(report, request.user)
        return Response(ReportSerializer(report).data, status=status.HTTP_200_OK)