from django.contrib import admin

from .models import Category, Item, ItemImage


admin.site.register(Category)
admin.site.register(Item)
admin.site.register(ItemImage)