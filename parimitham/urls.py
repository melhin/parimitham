from django.urls import include, path

urlpatterns = [
    path("", include("parimitham.core.urls")),
]
