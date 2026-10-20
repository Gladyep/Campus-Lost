from django.contrib.auth import get_user_model

from apps.claims.models import Claim
from apps.items.models import Item
from .models import Notification


def create_notification(*, recipient, kind, title, message, dedupe_key, item=None, claim=None, conversation=None, match=None, moderation_report=None):
    if recipient is None:
        return None
    notification, _ = Notification.objects.get_or_create(
        dedupe_key=dedupe_key,
        defaults={
            'user': recipient,
            'kind': kind,
            'title': title[:140],
            'message': message[:300],
            'item': item,
            'claim': claim,
            'conversation': conversation,
            'match': match,
            'moderation_report': moderation_report,
        },
    )
    return notification


def notify_new_report(item):
    User = get_user_model()
    date_label = item.event_date.strftime('%b %d, %Y').replace(' 0', ' ')
    if item.item_type == Item.Type.LOST:
        recipients = User.objects.exclude(pk=item.reporter_id).iterator(chunk_size=500)
        for recipient in recipients:
            create_notification(
                recipient=recipient,
                kind=Notification.Kind.REPORT,
                title='New lost-item report',
                message=f'{item.title} · {item.category.name} · {item.location} · {date_label}',
                item=item,
                dedupe_key=f'new-item-{item.pk}-user-{recipient.pk}',
            )
        return

    from apps.matching.services import NOTIFICATION_THRESHOLD

    potential_lost_reports = item.found_matches.filter(
        match_score__gte=NOTIFICATION_THRESHOLD,
        lost_item__status=Item.Status.OPEN,
    ).select_related('lost_item__reporter')
    for match in potential_lost_reports:
        lost_item = match.lost_item
        create_notification(
            recipient=lost_item.reporter,
            kind=Notification.Kind.REPORT,
            title='A found item may match your report',
            message=f'{item.title} · {item.category.name} · found at {item.location} · {date_label}.',
            item=item,
            match=match,
            dedupe_key=f'found-item-{item.pk}-lost-report-{lost_item.pk}-owner-{lost_item.reporter_id}',
        )


def notify_item_status(item, previous_status, actor):
    if previous_status == item.status:
        return

    recipient_ids = set(item.conversations.values_list('participants__pk', flat=True).distinct())
    if item.reporter_id != actor.pk:
        recipient_ids.add(item.reporter_id)
    recipient_ids.discard(actor.pk)
    status_stamp = item.updated_at.isoformat() if item.updated_at else 'updated'
    status_label = item.get_status_display().lower()
    User = get_user_model()
    for recipient in User.objects.filter(pk__in=recipient_ids):
        create_notification(
            recipient=recipient,
            kind=Notification.Kind.STATUS,
            title='Report status updated',
            message=f'The status for "{item.title[:180]}" changed to {status_label}.',
            item=item,
            dedupe_key=f'item-status-{item.pk}-{status_stamp}-user-{recipient.pk}',
        )


def notify_claim_submitted(claim, actor):
    if claim.item.reporter_id == actor.pk:
        return
    create_notification(
        recipient=claim.item.reporter,
        kind=Notification.Kind.CLAIM,
        title='New claim received',
        message=f'A campus member submitted a claim for {claim.item.title}. Review it privately.',
        item=claim.item,
        claim=claim,
        dedupe_key=f'claim-submitted-{claim.pk}-owner-{claim.item.reporter_id}',
    )


def notify_claimant_update(claim, actor, *, requested_information=False):
    if claim.claimant_id != actor.pk:
        if requested_information:
            title = 'More verification information requested'
            message = f'The report owner requested more information about your claim for {claim.item.title}.'
        else:
            title = 'Claim status updated'
            message = f'Your claim for {claim.item.title} is now {claim.get_status_display().lower()}.'
        create_notification(
            recipient=claim.claimant,
            kind=Notification.Kind.CLAIM,
            title=title,
            message=message,
            item=claim.item,
            claim=claim,
            dedupe_key=f'claim-status-{claim.pk}-{claim.status}-{claim.reviewed_at.isoformat() if claim.reviewed_at else claim.pk}',
        )

    if claim.status in (Claim.Status.FLAGGED, Claim.Status.DISPUTED):
        User = get_user_model()
        for user in User.objects.filter(is_staff=True).exclude(pk=actor.pk):
            create_notification(
                recipient=user,
                kind=Notification.Kind.MODERATION,
                title='Claim requires review',
                message=f'A claim for {claim.item.title} was flagged for review.',
                item=claim.item,
                claim=claim,
                dedupe_key=f'claim-review-{claim.pk}-{claim.status}-admin-{user.pk}',
            )


def notify_claim_answers(claim, actor):
    if claim.item.reporter_id == actor.pk:
        return
    create_notification(
        recipient=claim.item.reporter,
        kind=Notification.Kind.CLAIM,
        title='Verification information received',
        message=f'The claimant provided verification information for {claim.item.title}.',
        item=claim.item,
        claim=claim,
        dedupe_key=(
            f'claim-answers-{claim.pk}-'
            f'{claim.reviewed_at.isoformat() if claim.reviewed_at else "initial"}'
        ),
    )


def notify_new_message(message, actor):
    conversation = message.conversation
    for recipient in conversation.participants.exclude(pk=actor.pk):
        create_notification(
            recipient=recipient,
            kind=Notification.Kind.MESSAGE,
            title=f'New message about {conversation.item.title[:100]}',
            message='A campus member sent a message about this item report.',
            item=conversation.item,
            conversation=conversation,
            dedupe_key=f'message-{message.pk}-{recipient.pk}',
        )


def notify_moderation_report_created(report, actor):
    User = get_user_model()
    for administrator in User.objects.filter(is_staff=True).exclude(pk=actor.pk):
        create_notification(
            recipient=administrator,
            kind=Notification.Kind.MODERATION,
            title='Report requires review',
            message='A new report was submitted for administrator review.',
            item=report.item,
            moderation_report=report,
            dedupe_key=f'moderation-report-{report.pk}-admin-{administrator.pk}',
        )


def notify_moderation_report_decision(report, actor):
    recipients = {report.reporter}
    if report.reported_user_id:
        recipients.add(report.reported_user)
    if report.item_id:
        recipients.add(report.item.reporter)
    for recipient in recipients:
        if recipient.pk == actor.pk:
            continue
        create_notification(
            recipient=recipient,
            kind=Notification.Kind.MODERATION,
            title='Report review completed',
            message=f'A report connected to your account or item was {report.get_status_display().lower()}.',
            item=report.item,
            moderation_report=report,
            dedupe_key=f'moderation-decision-{report.pk}-{report.status}-user-{recipient.pk}',
        )