import random

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .tasks import cpu_intensive_work, cpu_intensive_work_task


@require_http_methods(["GET"])
def hello(request):
    sleep_time = random.randrange(6, 9)
    cpu_intensive_work(sleep_time)
    return JsonResponse({"message": "Hello World from Django App"})


@require_http_methods(["GET"])
def delayed_hello(request):
    sleep_time = random.randrange(6, 9)

    cpu_intensive_work_task.enqueue(sleep_time)
    return JsonResponse({"message": "Hello World from Django App"})


@require_http_methods(["GET"])
def health_check_view(request):
    """Health check endpoint"""
    if request.method == "GET":
        return JsonResponse({"status": "ok"})
