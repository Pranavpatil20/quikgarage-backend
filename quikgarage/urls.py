from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({'status': 'ok', 'service': 'quikgarage'})


urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/garages/', include('apps.garages.urls')),
    path('api/v1/vehicles/', include('apps.vehicles.urls')),
    path('api/v1/bookings/', include('apps.bookings.urls')),
    path('api/v1/invoices/', include('apps.invoices.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
