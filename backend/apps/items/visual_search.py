from datetime import date
from math import sqrt
from warnings import catch_warnings, simplefilter

from django.db.models import Q
from PIL import Image as PillowImage
from PIL import UnidentifiedImageError

from .models import Item

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096
MAX_IMAGE_PIXELS = 16_000_000
MAX_CANDIDATES = 250
MAX_RESULTS = 20
MIN_SIMILARITY = 0.38
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}


class InvalidVisualSearchImage(ValueError):
    pass


class InvalidVisualSearchFilter(ValueError):
    pass


def _image_signature(image_file):
    try:
        image_file.seek(0)
        with catch_warnings():
            simplefilter('error', PillowImage.DecompressionBombWarning)
            with PillowImage.open(image_file) as opened:
                if opened.format not in ALLOWED_FORMATS:
                    raise InvalidVisualSearchImage('Use a JPG, PNG, or WEBP image.')
                width, height = opened.size
                if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION or width * height > MAX_IMAGE_PIXELS:
                    raise InvalidVisualSearchImage('Images must be no larger than 4096 x 4096 pixels.')
                opened.load()
                image = opened.convert('RGB')

        try:
            pixel_image = image.resize((12, 12), PillowImage.Resampling.LANCZOS)
            pixels = tuple(channel for pixel in pixel_image.getdata() for channel in pixel)
            pixel_image.close()

            gray_image = image.convert('L').resize((9, 8), PillowImage.Resampling.LANCZOS)
            gray_pixels = gray_image.load()
            difference_hash = tuple(
                gray_pixels[x, y] > gray_pixels[x + 1, y]
                for y in range(8)
                for x in range(8)
            )
            gray_image.close()

            raw_histogram = image.histogram()
            color_histogram = tuple(
                sum(raw_histogram[channel * 256 + start:channel * 256 + start + 16])
                for channel in range(3)
                for start in range(0, 256, 16)
            )
            return pixels, difference_hash, color_histogram
        finally:
            image.close()
    except InvalidVisualSearchImage:
        raise
    except (PillowImage.DecompressionBombError, PillowImage.DecompressionBombWarning, UnidentifiedImageError, OSError, ValueError) as error:
        raise InvalidVisualSearchImage('The uploaded file is not a valid image.') from error
    finally:
        image_file.seek(0)


def _cosine_similarity(left, right):
    dot_product = sum(a * b for a, b in zip(left, right))
    magnitude = sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    return dot_product / magnitude if magnitude else 0.0


def _visual_similarity(left, right):
    left_pixels, left_hash, left_histogram = left
    right_pixels, right_hash, right_histogram = right

    pixel_similarity = 1 - sum(abs(a - b) for a, b in zip(left_pixels, right_pixels)) / (255 * len(left_pixels))
    hash_similarity = sum(a == b for a, b in zip(left_hash, right_hash)) / len(left_hash)
    histogram_similarity = _cosine_similarity(left_histogram, right_histogram)
    return max(0.0, min(1.0, 0.55 * pixel_similarity + 0.15 * hash_similarity + 0.30 * histogram_similarity))


def search_found_items(uploaded_image, *, category='', location='', event_date=''):
    if uploaded_image.size > MAX_UPLOAD_BYTES:
        raise InvalidVisualSearchImage('Images must be 5 MB or smaller.')

    query_signature = _image_signature(uploaded_image)
    candidates = Item.objects.filter(
        item_type=Item.Type.FOUND,
        status=Item.Status.OPEN,
        images__isnull=False,
    ).select_related(
        'category',
    ).prefetch_related(
        'images',
    ).distinct()

    if category:
        candidates = candidates.filter(Q(category__name__iexact=category) | Q(category__slug__iexact=category))
    if location:
        candidates = candidates.filter(location__icontains=location)
    if event_date:
        try:
            parsed_date = date.fromisoformat(event_date)
        except (TypeError, ValueError) as error:
            raise InvalidVisualSearchFilter('Use a valid reported date.') from error
        candidates = candidates.filter(event_date=parsed_date)

    ranked = []
    for item in candidates.order_by('-created_at')[:MAX_CANDIDATES]:
        best_match = None
        for item_image in item.images.all():
            try:
                with item_image.image.open('rb') as stored_image:
                    signature = _image_signature(stored_image)
            except (InvalidVisualSearchImage, OSError, ValueError):
                continue
            score = _visual_similarity(query_signature, signature)
            if best_match is None or score > best_match['score']:
                best_match = {'item': item, 'image': item_image, 'score': score}

        if best_match and best_match['score'] >= MIN_SIMILARITY:
            ranked.append(best_match)

    ranked.sort(key=lambda result: result['score'], reverse=True)
    return [
        {**result, 'similarity': round(result['score'] * 100)}
        for result in ranked[:MAX_RESULTS]
    ]