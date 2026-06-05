from django.contrib import admin

from .models import Appointment, AvailabilitySlot


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ('professional', 'starts_at', 'ends_at', 'status')
    list_filter = ('status', 'professional')
    search_fields = ('professional__full_name',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'professional', 'scheduled_at', 'status')
    list_filter = ('status', 'professional')
    search_fields = ('patient__full_name', 'professional__full_name')
