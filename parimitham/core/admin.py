from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "status", "created_at", "modified_at")
    list_filter = ("status", "created_at", "modified_at")
    search_fields = ("id", "file")
    readonly_fields = ("created_at", "modified_at")

    fieldsets = (
        (None, {"fields": ("file", "status")}),
        ("Timestamps", {"fields": ("created_at", "modified_at")}),
    )

    actions = ["mark_as_completed", "mark_as_failed"]

    def mark_as_completed(self, request, queryset):
        queryset.update(status=Document.DocumentStatus.COMPLETED)

    def mark_as_failed(self, request, queryset):
        queryset.update(status=Document.DocumentStatus.FAILURE)

    mark_as_completed.short_description = "Mark selected documents as completed"
    mark_as_failed.short_description = "Mark selected documents as failed"
