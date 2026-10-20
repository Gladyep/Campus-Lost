from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, RegisterView, ProfileView
from apps.claims.views import ClaimViewSet, VerificationQuestionViewSet
from apps.communication.views import ConversationViewSet, NotificationViewSet
from apps.items.views import CategoryViewSet, ItemViewSet, VisualSearchView, search_found_reports
from apps.matching.views import MatchViewSet
from apps.moderation.views import AdminDashboardView, FlaggedClaimsView, ReportDecisionView, ReportViewSet

router = DefaultRouter()
router.register('items', ItemViewSet, basename='item')
router.register('categories', CategoryViewSet, basename='category')
router.register('matches', MatchViewSet, basename='match')
router.register('claims', ClaimViewSet, basename='claim')
router.register('verification-questions', VerificationQuestionViewSet, basename='verification-question')
router.register('conversations', ConversationViewSet, basename='conversation')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('reports', ReportViewSet, basename='report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/visual-search/', VisualSearchView.as_view(), name='visual-search'),
    path('api/items/search-found/', search_found_reports, name='search-found-reports'),
    path('api/admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('api/admin/flagged-claims/', FlaggedClaimsView.as_view(), name='flagged-claims'),
    path('api/admin/reports/<int:report_id>/decision/', ReportDecisionView.as_view(), name='report-decision'),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)