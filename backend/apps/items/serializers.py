from PIL import Image as PillowImage, UnidentifiedImageError
from rest_framework import serializers

from .models import Category, Item, ItemImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class ItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemImage
        fields = ('id', 'image', 'uploaded_at')


class ItemSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='name', queryset=Category.objects.all())
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ItemImageSerializer(many=True, read_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    reporter_name = serializers.CharField(source='reporter.name', read_only=True)

    class Meta:
        model = Item
        fields = (
            'id', 'reporter_name', 'category', 'category_name', 'title', 'description',
            'item_type', 'location', 'event_date', 'status', 'images', 'image', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'reporter_name', 'status', 'created_at', 'updated_at')

    def validate_image(self, image):
        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Images must be 5 MB or smaller.')
        try:
            image.seek(0)
            with PillowImage.open(image) as uploaded:
                if uploaded.format not in {'JPEG', 'PNG', 'WEBP'}:
                    raise serializers.ValidationError('Use a JPEG, PNG, or WebP image.')
                uploaded.verify()
            image.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError('The uploaded file is not a valid image.')
        return image

    def create(self, validated_data):
        image = validated_data.pop('image', None)
        item = Item.objects.create(**validated_data)
        if image:
            ItemImage.objects.create(item=item, image=image)
        return item

    def update(self, instance, validated_data):
        image = validated_data.pop('image', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if image:
            ItemImage.objects.create(item=instance, image=image)
        return instance