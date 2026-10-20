from datetime import date

from django.db import transaction
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_GET
from rest_framework import decorators, permissions, viewsets
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Item
from .permissions import IsReporterOrReadOnly
from .serializers import CategorySerializer, ItemSerializer
from .visual_search import InvalidVisualSearchFilter, InvalidVisualSearchImage, search_found_items


class ItemDeletionConflict(APIException):
    status_code = 409
    default_detail = 'This report has claim or conversation history and cannot be deleted.'
    default_code = 'report_has_history'


@require_GET
def search_found_reports(request):
    queryset = Item.objects.filter(
        item_type=Item.Type.FOUND,
        status=Item.Status.OPEN,
    ).select_related('category').prefetch_related('images').order_by('-created_at')

    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))

    category = request.GET.get('category', '').strip()
    if category:
        queryset = queryset.filter(Q(category__name__iexact=category) | Q(category__slug__iexact=category))

    location = request.GET.get('location', '').strip()
    if location:
        queryset = queryset.filter(location__icontains=location)

    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    try:
        parsed_start = date.fromisoformat(start_date) if start_date else None
        parsed_end = date.fromisoformat(end_date) if end_date else None
    except ValueError:
        return JsonResponse({'date': 'Enter dates in YYYY-MM-DD format.'}, status=400)
    if parsed_start and parsed_end and parsed_end < parsed_start:
        return JsonResponse({'end_date': 'End date must be on or after the start date.'}, status=400)
    if parsed_start:
        queryset = queryset.filter(event_date__gte=parsed_start)
    if parsed_end:
        queryset = queryset.filter(event_date__lte=parsed_end)

    results = []
    for item in queryset:
        images = []
        for item_image in item.images.all():
            try:
                image_url = request.build_absolute_uri(item_image.image.url)
            except ValueError:
                continue
            images.append({'id': item_image.pk, 'image': image_url})
        results.append({
            'id': item.pk,
            'title': item.title,
            'reporter_id': item.reporter_id,
            'description': item.description,
            'item_type': item.item_type,
            'category_name': item.category.name,
            'location': item.location,
            'event_date': item.event_date.isoformat(),
            'status': item.status,
            'is_reporter': request.user.is_authenticated and item.reporter_id == request.user.pk,
            'images': images,
        })
    return JsonResponse(results, safe=False)


class VisualSearchView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uploaded_image = request.FILES.get('image')
        if uploaded_image is None:
            return Response({'image': 'Choose an image to search.'}, status=400)

        try:
            matches = search_found_items(
                uploaded_image,
                category=request.data.get('category', '').strip(),
                location=request.data.get('location', '').strip(),
                event_date=request.data.get('event_date', '').strip(),
            )
        except InvalidVisualSearchImage as error:
            return Response({'image': str(error)}, status=400)
        except InvalidVisualSearchFilter as error:
            return Response({'event_date': str(error)}, status=400)

        results = []
        for match in matches:
            item = match['item']
            results.append({
                'id': item.pk,
                'title': item.title,
                'reporter_id': item.reporter_id,
                'description': item.description,
                'item_type': item.item_type,
                'category': item.category.name,
                'category_name': item.category.name,
                'location': item.location,
                'event_date': item.event_date.isoformat(),
                'status': item.status,
                'is_reporter': item.reporter_id == request.user.id,
                'images': [{'image': request.build_absolute_uri(match['image'].image.url)}],
                'similarity': match['similarity'],
            })

        return Response({'count': len(results), 'results': results})


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)


class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsReporterOrReadOnly)
    search_fields = ('title', 'description', 'location', 'category__name')
    ordering_fields = ('created_at', 'event_date', 'title')
    ordering = ('-created_at',)

    def get_queryset(self):
        queryset = Item.objects.select_related('category', 'reporter').prefetch_related('images')
        if self.request.query_params.get('mine') == 'true':
            if not self.request.user.is_authenticated:
                return queryset.none()
            queryset = queryset.filter(reporter=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter in Item.Status.values:
            queryset = queryset.filter(status=status_filter)
        elif self.request.query_params.get('mine') != 'true':
            queryset = queryset.exclude(status__in=(Item.Status.CLOSED, Item.Status.RETURNED, Item.Status.RECOVERED))
            if self.action == 'destroy' and self.request.user.is_authenticated:
                queryset = queryset | Item.objects.filter(reporter=self.request.user)
        item_type = self.request.query_params.get('item_type') or self.request.query_params.get('type')
        if item_type in Item.Type.values:
            queryset = queryset.filter(item_type=item_type)
            if status_filter != Item.Status.RECOVERED:
                queryset = queryset.exclude(status=Item.Status.RECOVERED)
        category = self.request.query_params.get('category_name') or self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(Q(category__name__iexact=category) | Q(category__slug__iexact=category))
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        date_after = self.request.query_params.get('date_after')
        date_before = self.request.query_params.get('date_before')
        if date_after:
            queryset = queryset.filter(event_date__gte=date_after)
        if date_before:
            queryset = queryset.filter(event_date__lte=date_before)
        return queryset

    def perform_create(self, serializer):
        with transaction.atomic():
            item = serializer.save(reporter=self.request.user)
            from apps.matching.services import evaluate_matches
            from apps.communication.services import notify_new_report

            evaluate_matches(item)
            notify_new_report(item)

    def perform_update(self, serializer):
        with transaction.atomic():
            previous_status = serializer.instance.status
            item = serializer.save()
            from apps.matching.services import evaluate_matches
            from apps.communication.services import notify_item_status

            evaluate_matches(item)
            notify_item_status(item, previous_status, self.request.user)

    def perform_destroy(self, instance):
        if instance.reporter_id != self.request.user.pk and not self.request.user.is_staff:
            raise PermissionDenied('Only the report owner or a moderator may delete this report.')
        image_files = [(image.image.storage, image.image.name) for image in instance.images.all() if image.image]
        try:
            instance.delete()
        except ProtectedError as error:
            raise ItemDeletionConflict() from error
        for storage, name in image_files:
            transaction.on_commit(lambda storage=storage, name=name: storage.delete(name))

    @decorators.action(detail=True, methods=('post',), url_path='recover')
    def recover(self, request, pk=None):
        item = self.get_object()
        if item.reporter_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Only the report owner or a moderator may mark this item recovered.')
        if item.status in (Item.Status.RECOVERED, Item.Status.RETURNED, Item.Status.CLOSED):
            raise ValidationError({'status': 'This report can no longer be marked recovered.'})
        previous_status = item.status
        item.status = Item.Status.RECOVERED
        item.save(update_fields=('status', 'updated_at'))
        from apps.communication.services import notify_item_status

        notify_item_status(item, previous_status, request.user)
        return Response(self.get_serializer(item).data)