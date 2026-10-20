from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.claims.models import Claim
from apps.items.models import Item


class Notification(models.Model):
    class Kind(models.TextChoices):
        REPORT = 'REPORT', 'New community report'
        MATCH = 'MATCH', 'Potential match'
        CLAIM = 'CLAIM', 'Claim update'
        MESSAGE = 'MESSAGE', 'New message'
        STATUS = 'STATUS', 'Item status'
        MODERATION = 'MODERATION', 'Moderation update'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=140, blank=True, default='')
    message = models.CharField(max_length=300)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    claim = models.ForeignKey(Claim, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    conversation = models.ForeignKey('communication.Conversation', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    match = models.ForeignKey('matching.Match', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    moderation_report = models.ForeignKey('moderation.Report', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    dedupe_key = models.CharField(max_length=180, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)


class Conversation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='conversations')
    claim = models.ForeignKey(Claim, on_delete=models.PROTECT, related_name='conversations', null=True, blank=True)
    contact_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='item_contact_conversations',
        null=True,
        blank=True,
    )
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('claim',), name='one_conversation_per_claim'),
            models.UniqueConstraint(
                fields=('item', 'contact_user'),
                condition=Q(claim__isnull=True, contact_user__isnull=False),
                name='one_item_contact_conversation',
            ),
        ]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sent_messages')
    message_text = models.CharField(max_length=2000)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('sent_at',)