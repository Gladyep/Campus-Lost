from django.conf import settings
from django.db import models

from apps.claims.models import Claim
from apps.items.models import Item


class Notification(models.Model):
    class Kind(models.TextChoices):
        MATCH = 'MATCH', 'Potential match'
        CLAIM = 'CLAIM', 'Claim update'
        MESSAGE = 'MESSAGE', 'New message'
        STATUS = 'STATUS', 'Item status'
        MODERATION = 'MODERATION', 'Moderation update'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    message = models.CharField(max_length=300)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    dedupe_key = models.CharField(max_length=180, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)


class Conversation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='conversations')
    claim = models.ForeignKey(Claim, on_delete=models.PROTECT, related_name='conversations')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('claim',), name='one_conversation_per_claim')]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sent_messages')
    message_text = models.CharField(max_length=2000)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('sent_at',)