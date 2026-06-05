from django.contrib import admin

from .models import Professional, Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialty', 'registration_number', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('full_name', 'registration_number')
    readonly_fields = ('created_at', 'updated_at')
