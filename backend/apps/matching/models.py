from django.db import models

from apps.items.models import Item


class Match(models.Model):
    lost_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='lost_matches')
    found_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='found_matches')
    match_score = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('lost_item', 'found_item'), name='unique_lost_found_match')]
        ordering = ('-match_score', '-updated_at')

    def __str__(self):
        return f'{self.lost_item_id}:{self.found_item_id} ({self.match_score})'