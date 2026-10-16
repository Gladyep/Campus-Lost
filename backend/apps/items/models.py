from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    description = models.CharField(max_length=240, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Item(models.Model):
    class Type(models.TextChoices):
        LOST = 'LOST', 'Lost'
        FOUND = 'FOUND', 'Found'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        CLAIM_PENDING = 'CLAIM_PENDING', 'Claim pending'
        UNDER_VERIFICATION = 'UNDER_VERIFICATION', 'Under verification'
        RETURNED = 'RETURNED', 'Returned'
        RECOVERED = 'RECOVERED', 'Recovered'
        CLOSED = 'CLOSED', 'Closed'
        DISPUTED = 'DISPUTED', 'Disputed'

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=2000)
    item_type = models.CharField(max_length=8, choices=Type.choices, db_index=True)
    location = models.CharField(max_length=200, db_index=True)
    event_date = models.DateField(db_index=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('item_type', 'status', 'event_date'))]

    def __str__(self):
        return self.title


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item-images/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)