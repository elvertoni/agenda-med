from django.contrib import admin

from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'cpf', 'whatsapp_number', 'health_plan', 'created_at')
    search_fields = ('full_name', 'cpf', 'whatsapp_number', 'email')
    list_filter = ('sex', 'health_plan')
    readonly_fields = ('created_at', 'updated_at')
