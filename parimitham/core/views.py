from django.http import JsonResponse
from django.views import View


class RootView(View):
    """Root endpoint that triggers a task"""
    
    def get(self, request):
        from .tasks import delayed_hi
        delayed_hi.enqueue()
        return JsonResponse({"message": "Hello World from Django App"})


class HealthCheckView(View):
    """Health check endpoint"""
    
    def get(self, request):
        return JsonResponse({"status": "ok"})
