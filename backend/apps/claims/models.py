from django.conf import settings
from django.db import models

from apps.items.models import Item


class Claim(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        UNDER_VERIFICATION = 'UNDER_VERIFICATION', 'Under verification'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        FLAGGED = 'FLAGGED', 'Flagged'
        DISPUTED = 'DISPUTED', 'Disputed'

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='claims')
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='claims')
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    evidence = models.TextField(max_length=2000)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_claims')
    decision_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('item', 'claimant'), name='unique_claimant_per_item')]
        ordering = ('-submitted_at',)


class VerificationQuestion(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='verification_questions')
    question_text = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ClaimAnswer(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(VerificationQuestion, on_delete=models.PROTECT, related_name='answers')
    answer_text = models.TextField(max_length=1000)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('claim', 'question'), name='unique_answer_per_question')]