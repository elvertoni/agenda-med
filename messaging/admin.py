from django.contrib import admin

from .models import ChatSession, OtpCode, PresenceConfirmation
from .services import record_presence_response


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'state', 'updated_at')
    list_filter = ('state',)
    search_fields = ('phone_number',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = (
        'whatsapp_number',
        'user',
        'expires_at',
        'is_used',
        'attempts',
        'locked_until',
        'created_at',
    )
    list_filter = ('is_used', 'expires_at', 'locked_until')
    search_fields = ('whatsapp_number', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PresenceConfirmation)
class PresenceConfirmationAdmin(admin.ModelAdmin):
    list_display = (
        'appointment',
        'channel',
        'scheduled_for',
        'sent_at',
        'response',
        'status',
    )
    list_filter = ('channel', 'response', 'status', 'scheduled_for')
    search_fields = (
        'appointment__patient__full_name',
        'appointment__professional__full_name',
    )
    readonly_fields = ('created_at', 'updated_at', 'sent_at', 'responded_at')
    actions = ('mark_confirmed', 'mark_not_confirmed')

    @admin.action(description='Registrar como confirmado')
    def mark_confirmed(self, request, queryset):
        for confirmation in queryset.select_related('appointment'):
            record_presence_response(
                confirmation,
                PresenceConfirmation.Response.CONFIRMED,
            )

    @admin.action(description='Registrar como não confirmado')
    def mark_not_confirmed(self, request, queryset):
        for confirmation in queryset.select_related('appointment'):
            record_presence_response(
                confirmation,
                PresenceConfirmation.Response.NOT_CONFIRMED,
            )
