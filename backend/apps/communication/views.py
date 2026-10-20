from django.db import transaction
from django.utils.html import strip_tags
from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.claims.models import Claim
from apps.items.models import Item
from .models import Conversation, Message, Notification
from .serializers import ConversationSerializer, MessageSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'patch', 'delete', 'head', 'options')

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).select_related(
            'item', 'claim__item', 'conversation', 'match', 'moderation_report',
        )
        category = self.request.query_params.get('category')
        category_kinds = {
            'lost-found': (Notification.Kind.REPORT, Notification.Kind.STATUS),
            'matches': (Notification.Kind.MATCH,),
            'claims': (Notification.Kind.CLAIM,),
            'messages': (Notification.Kind.MESSAGE,),
            'system': (Notification.Kind.MODERATION,),
        }
        if category in category_kinds:
            queryset = queryset.filter(kind__in=category_kinds[category])
        return queryset

    @decorators.action(detail=False, methods=('get',), url_path='unread-count')
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return response.Response({'count': count})

    @decorators.action(detail=False, methods=('patch',), url_path='read-all')
    def read_all(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return response.Response({'updated': updated, 'unread_count': 0})

    @decorators.action(detail=False, methods=('delete',), url_path='clear-read')
    def clear_read(self, request):
        deleted, _ = Notification.objects.filter(user=request.user, is_read=True).delete()
        return response.Response({'deleted': deleted})

    @decorators.action(detail=True, methods=('patch',), url_path='read')
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=('is_read',))
        return response.Response(self.get_serializer(notification).data)

    def partial_update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = bool(request.data.get('is_read', True))
        notification.save(update_fields=('is_read',))
        return response.Response(self.get_serializer(notification).data)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get', 'post', 'head', 'options')

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).select_related('item', 'claim').prefetch_related('messages').distinct()

    def create(self, request, *args, **kwargs):
        claim_id = request.data.get('claim')
        if claim_id:
            claim = Claim.objects.filter(pk=claim_id).select_related('item', 'claimant').first()
            if claim is None:
                raise ValidationError({'claim': 'A valid claim is required to start a conversation.'})
            if request.user.id not in (claim.claimant_id, claim.item.reporter_id):
                raise PermissionDenied('Only the claimant or finder can start this conversation.')
            participants = (claim.claimant, claim.item.reporter)
            with transaction.atomic():
                conversation, _ = Conversation.objects.get_or_create(claim=claim, defaults={'item': claim.item})
                conversation.participants.add(*participants)
        else:
            item = Item.objects.filter(pk=request.data.get('item')).select_related('reporter').first()
            if item is None:
                raise ValidationError({'item': 'A valid report is required to contact its reporter.'})
            if item.reporter_id == request.user.id:
                raise PermissionDenied('You cannot start a conversation with yourself.')
            if item.status in (Item.Status.RECOVERED, Item.Status.RETURNED, Item.Status.CLOSED):
                raise ValidationError({'item': 'This report is no longer accepting new conversations.'})
            with transaction.atomic():
                conversation, _ = Conversation.objects.get_or_create(
                    item=item,
                    claim=None,
                    contact_user=request.user,
                )
                conversation.participants.add(request.user, item.reporter)
        return response.Response(self.get_serializer(conversation).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=('get', 'post'), url_path='messages')
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == 'GET':
            return response.Response(MessageSerializer(conversation.messages.select_related('sender'), many=True).data)
        raw_text = request.data.get('message_text', '')
        if not isinstance(raw_text, str):
            raise ValidationError({'message_text': 'Messages must be plain text.'})
        text = strip_tags(raw_text).strip()
        if not text or len(text) > 2000:
            raise ValidationError({'message_text': 'Messages must contain 1 to 2000 characters.'})
        with transaction.atomic():
            message = Message.objects.create(conversation=conversation, sender=request.user, message_text=text)
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=('updated_at',))
            for recipient in conversation.participants.exclude(pk=request.user.pk):
                Notification.objects.get_or_create(
                    dedupe_key=f'message-{message.pk}-{recipient.pk}',
                    defaults={
                        'user': recipient,
                        'kind': Notification.Kind.MESSAGE,
                        'title': f'New message about {conversation.item.title[:100]}',
                        'message': 'A campus member sent a message about this item report.',
                        'item': conversation.item,
                        'conversation': conversation,
                    },
                )
        return response.Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)