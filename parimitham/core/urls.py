from django.urls import path
from .views import RootView, HealthCheckView

urlpatterns = [
    path('', RootView.as_view(), name='root'),
    path('health/', HealthCheckView.as_view(), name='health'),
]
