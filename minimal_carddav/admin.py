# admin.py
from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["display_name", "phone_short", "phone_mobile", "email", "is_deleted", "revision"]
    list_filter = ["is_deleted"]
    search_fields = ["display_name", "email", "phone_short", "phone_mobile"]
    readonly_fields = ["uid", "revision", "updated_at"]

    def save_model(self, request, obj, form, change):
        if change:  # nur bei Bearbeitung, nicht bei Neuanlage
            obj.revision += 1
        super().save_model(request, obj, form, change)