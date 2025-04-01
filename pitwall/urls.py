# f1_dashboard/urls.py - Make sure it looks like this
from django.contrib import admin
from django.urls import path, include  # Ensure include is imported

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("telemetry.urls")),  # THIS LINE IS CRUCIAL
]
