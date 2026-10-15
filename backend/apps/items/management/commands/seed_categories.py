from django.core.management.base import BaseCommand

from apps.items.models import Category


class Command(BaseCommand):
    help = 'Create or update the standard CampusConnect item categories.'

    def handle(self, *args, **options):
        for name in ('Electronics', 'Bags', 'Keys', 'Accessories', 'Books', 'Clothing', 'Other'):
            Category.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS('Standard categories are ready.'))