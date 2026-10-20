from difflib import SequenceMatcher

from django.db import transaction

from apps.items.models import Item
from .models import Match

MATCH_THRESHOLD = 35
NOTIFICATION_THRESHOLD = 65


def score_items(first, second):
    category_score = 25 if first.category_id == second.category_id else 0
    title_score = 10 * SequenceMatcher(None, first.title.casefold(), second.title.casefold()).ratio()
    first_words = {word.casefold() for word in first.description.split() if len(word) > 2}
    second_words = {word.casefold() for word in second.description.split() if len(word) > 2}
    union = first_words | second_words
    description_score = 25 * len(first_words & second_words) / len(union) if union else 0
    location_score = 20 * SequenceMatcher(None, first.location.casefold(), second.location.casefold()).ratio()
    days_apart = abs((first.event_date - second.event_date).days)
    date_score = 20 * max(0, 1 - days_apart / 31)
    return round(category_score + title_score + description_score + location_score + date_score, 2)


@transaction.atomic
def evaluate_matches(item):
    if item.status != Item.Status.OPEN:
        return
    opposite_type = Item.Type.FOUND if item.item_type == Item.Type.LOST else Item.Type.LOST
    candidates = Item.objects.filter(item_type=opposite_type, status=Item.Status.OPEN).exclude(reporter=item.reporter).select_related('category', 'reporter')
    from apps.communication.models import Notification

    for candidate in candidates:
        lost_item, found_item = (item, candidate) if item.item_type == Item.Type.LOST else (candidate, item)
        score = score_items(lost_item, found_item)
        if score < MATCH_THRESHOLD:
            Match.objects.filter(lost_item=lost_item, found_item=found_item).delete()
            continue
        match, _ = Match.objects.update_or_create(
            lost_item=lost_item,
            found_item=found_item,
            defaults={'match_score': score},
        )
        if score >= NOTIFICATION_THRESHOLD:
            for recipient, related_item in ((lost_item.reporter, lost_item), (found_item.reporter, found_item)):
                Notification.objects.get_or_create(
                    dedupe_key=f'match-{match.pk}-{recipient.pk}',
                    defaults={
                        'user': recipient,
                        'kind': Notification.Kind.MATCH,
                        'title': 'Potential item match',
                        'message': 'A possible match was found for one of your reports.',
                        'item': related_item,
                        'match': match,
                    },
                )