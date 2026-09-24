from django.contrib import admin
from .models import Section, Task

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "section", "completed", "updated_at")
    list_filter = ("section", "completed")
    search_fields = ("title", "owner__username")
    list_select_related = ("owner", "section")
    readonly_fields = ("created_at", "updated_at")

