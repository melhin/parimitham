from django.conf import settings
from django.contrib import admin
from django.urls import include, path

print(settings.STATIC_URL, settings.STATIC_ROOT)
urlpatterns = [
    path("", include("parimitham.core.urls")),
    path("admin/", admin.site.urls),
]
