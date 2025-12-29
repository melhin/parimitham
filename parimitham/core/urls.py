from django.urls import path

from .views import (
    delayed_hello_view,
    health_check_view,
    stream_upload_view,
)

urlpatterns = [
    path("hello/", delayed_hello_view, name="delayed_hello"),
    path("health/", health_check_view, name="health"),
    path("upload/", stream_upload_view, name="stream_upload"),
]
