from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.items.models import Item
from .models import Claim, ClaimAnswer, VerificationQuestion
from .serializers import ClaimAnswerSerializer, ClaimSerializer, VerificationQuestionSerializer


class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'patch', 'head', 'options')

    def get_queryset(self):
        queryset = Claim.objects.select_related('item', 'claimant').prefetch_related('answers__question')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(item__reporter=self.request.user) | queryset.filter(claimant=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            item = Item.objects.select_for_update().get(pk=serializer.validated_data['item'].pk)
            if Claim.objects.filter(item=item, claimant=self.request.user).exists():
                raise ValidationError({'item': 'You already submitted a claim for this item.'})
            claim = serializer.save()
            if item.status == Item.Status.OPEN:
                item.status = Item.Status.CLAIM_PENDING
                item.save(update_fields=('status', 'updated_at'))

    def _assert_participant(self, claim):
        if not self.request.user.is_staff and self.request.user.id not in (claim.claimant_id, claim.item.reporter_id):
            raise PermissionDenied('You are not a participant in this claim.')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self._assert_participant(instance)
        return response.Response(self.get_serializer(instance).data)

    @decorators.action(detail=True, methods=('post',), url_path='answers')
    def answers(self, request, pk=None):
        claim = self.get_object()
        self._assert_participant(claim)
        if request.user.id != claim.claimant_id:
            raise PermissionDenied('Only the claimant can submit verification answers.')
        submitted = request.data.get('answers', [])
        if not isinstance(submitted, list) or not submitted:
            raise ValidationError({'answers': 'Submit at least one verification answer.'})
        saved = []
        with transaction.atomic():
            for answer in submitted:
                question = VerificationQuestion.objects.filter(pk=answer.get('question'), item=claim.item, is_active=True).first()
                if question is None:
                    raise ValidationError({'question': 'A verification question is invalid or inactive.'})
                entry, _ = ClaimAnswer.objects.update_or_create(
                    claim=claim,
                    question=question,
                    defaults={'answer_text': answer.get('answer_text', '').strip()},
                )
                if not entry.answer_text:
                    raise ValidationError({'answer_text': 'Answers cannot be empty.'})
                saved.append(entry)
        if claim.status == Claim.Status.PENDING:
            claim.status = Claim.Status.UNDER_VERIFICATION
            claim.save(update_fields=('status',))
            claim.item.status = Item.Status.UNDER_VERIFICATION
            claim.item.save(update_fields=('status', 'updated_at'))
        return response.Response(ClaimAnswerSerializer(saved, many=True).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=('patch',), url_path='decision')
    def decision(self, request, pk=None):
        with transaction.atomic():
            claim = Claim.objects.select_for_update().select_related('item').get(pk=pk)
            self.check_object_permissions(request, claim)
            if request.user.id != claim.item.reporter_id and not request.user.is_staff:
                raise PermissionDenied('Only the finder or a moderator can decide this claim.')
            next_status = request.data.get('status')
            allowed = {Claim.Status.UNDER_VERIFICATION, Claim.Status.APPROVED, Claim.Status.REJECTED, Claim.Status.FLAGGED, Claim.Status.DISPUTED}
            if next_status not in allowed:
                raise ValidationError({'status': 'Choose a valid claim decision.'})
            if claim.status in {Claim.Status.APPROVED, Claim.Status.REJECTED}:
                raise ValidationError({'status': 'This claim has already received a final decision.'})
            claim.status = next_status
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.decision_reason = str(request.data.get('reason', '')).strip()[:500]
            claim.save(update_fields=('status', 'reviewed_by', 'reviewed_at', 'decision_reason'))
            if next_status == Claim.Status.APPROVED:
                claim.item.status = Item.Status.CLAIM_PENDING
                claim.item.save(update_fields=('status', 'updated_at'))
            from apps.moderation.models import AuditLog

            AuditLog.objects.create(actor=request.user, action=f'claim_{next_status.lower()}', entity_type='claim', entity_id=str(claim.pk), metadata={'reason': claim.decision_reason})
        return response.Response(self.get_serializer(claim).data)


class VerificationQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = VerificationQuestionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def get_queryset(self):
        queryset = VerificationQuestion.objects.select_related('item')
        item_id = self.request.query_params.get('item')
        if self.request.method in permissions.SAFE_METHODS:
            if self.request.user.is_staff:
                return queryset.filter(item_id=item_id) if item_id else queryset
            if not item_id:
                return queryset.none()
            return queryset.filter(item_id=item_id).filter(
                Q(item__reporter=self.request.user) |
                Q(item__claims__claimant=self.request.user, is_active=True)
            ).distinct()
        return queryset.filter(item__reporter=self.request.user)

    def perform_create(self, serializer):
        item = serializer.validated_data['item']
        if item.reporter_id != self.request.user.id:
            raise PermissionDenied('Only the report owner may manage verification questions.')
        if item.item_type != Item.Type.FOUND:
            raise ValidationError({'item': 'Verification questions are for found reports.'})
        serializer.save()