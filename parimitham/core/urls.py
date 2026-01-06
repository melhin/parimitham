from django.urls import path

from .views import delayed_hello, health_check_view, hello

urlpatterns = [
    path("hello/", hello, name="hello"),
    path("dhello/", delayed_hello, name="delayed_hello"),
    path("health/", health_check_view, name="health"),
]
