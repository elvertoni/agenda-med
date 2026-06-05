from django.contrib import admin

from .models import ExamProtocol, PriceItem, ServiceProtocol


@admin.register(PriceItem)
class PriceItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'price', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ServiceProtocol)
class ServiceProtocolAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ExamProtocol)
class ExamProtocolAdmin(admin.ModelAdmin):
    list_display = ('exam_name', 'specialty', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('exam_name',)
    readonly_fields = ('created_at', 'updated_at')
