from django.contrib import admin
from .models import Report

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'date_created', 'date_updated')
    search_fields = ('title', 'source')
    list_filter = ('date_created', 'source')
    ordering = ('-date_created',)
