from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/customers/", include("apps.customers.urls")),
    path("api/bookings/", include("apps.bookings.urls")),
]
