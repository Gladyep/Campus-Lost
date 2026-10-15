from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Item
from .permissions import IsReporterOrReadOnly
from .serializers import CategorySerializer, ItemSerializer
from .visual_search import InvalidVisualSearchFilter, InvalidVisualSearchImage, search_found_items


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
                'description': item.description,
                'item_type': item.item_type,
                'category': item.category.name,
                'category_name': item.category.name,
                'location': item.location,
                'event_date': item.event_date.isoformat(),
                'status': item.status,
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
        else:
            queryset = queryset.exclude(status__in=(Item.Status.CLOSED, Item.Status.RETURNED))
        item_type = self.request.query_params.get('item_type') or self.request.query_params.get('type')
        if item_type in Item.Type.values:
            queryset = queryset.filter(item_type=item_type)
        status_filter = self.request.query_params.get('status')
        if status_filter in Item.Status.values:
            queryset = queryset.filter(status=status_filter)
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
        item = serializer.save(reporter=self.request.user)
        from apps.matching.services import evaluate_matches

        evaluate_matches(item)

    def perform_update(self, serializer):
        item = serializer.save()
        from apps.matching.services import evaluate_matches

        evaluate_matches(item)

    def perform_destroy(self, instance):
        instance.status = Item.Status.CLOSED
        instance.save(update_fields=('status', 'updated_at'))