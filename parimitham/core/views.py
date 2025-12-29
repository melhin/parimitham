import os

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Document


@require_http_methods(["GET"])
def delayed_hello_view(request):
    """Root endpoint that triggers a task"""
    from .tasks import delayed_hi

    delayed_hi.enqueue()
    return JsonResponse({"message": "Hello World from Django App"})


@require_http_methods(["GET"])
def health_check_view(request):
    """Health check endpoint"""
    return JsonResponse({"status": "ok"})


@csrf_exempt  # For simplicity in this example; in production, use proper CSRF protection
@require_http_methods(["POST"])
def stream_upload_view(request):
    try:
        # Get the file from the request
        file = request.FILES["file"]

        # Create a new Document instance
        document = Document.objects.create()

        # Define the upload path
        upload_path = os.path.join(settings.MEDIA_ROOT, "documents", f"document_{document.id}_{file.name}")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)

        # Save the file in chunks to handle large files
        with open(upload_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Update the document with the file path
        document.file.name = f"documents/document_{document.id}_{file.name}"
        document.save()

        return JsonResponse({"status": "success", "document_id": document.id, "message": "File uploaded successfully"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
