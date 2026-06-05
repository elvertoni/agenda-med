from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class ChatSession(TimeStampedModel):
    '''Conversational state for the WhatsApp chatbot.'''

    class State(models.TextChoices):
        IDLE = 'idle', 'Ocioso'
        AWAITING_SPECIALTY = 'awaiting_specialty', 'Aguardando especialidade'
        AWAITING_SLOT = 'awaiting_slot', 'Aguardando horário'
        AWAITING_CONFIRM = 'awaiting_confirm', 'Aguardando confirmação'

    phone_number = models.CharField(max_length=20, unique=True)
    state = models.CharField(
        max_length=30,
        choices=State.choices,
        default=State.IDLE,
    )
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-updated_at',)

    def __str__(self):
        return f'{self.phone_number} [{self.state}]'


class OtpCode(TimeStampedModel):
    '''One-time password for patient portal access via WhatsApp.'''

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otp_codes',
    )
    whatsapp_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('whatsapp_number', 'is_used', 'expires_at')),
        ]

    def __str__(self):
        return f'OTP para {self.whatsapp_number}'

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_locked(self):
        return bool(self.locked_until and timezone.now() < self.locked_until)

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used', 'updated_at'])

    def register_failed_attempt(self, *, max_attempts, lock_minutes):
        self.attempts += 1
        update_fields = ['attempts', 'updated_at']
        if self.attempts >= max_attempts:
            self.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
            update_fields.append('locked_until')
        self.save(update_fields=update_fields)


class PresenceConfirmation(TimeStampedModel):
    '''24-hour appointment presence confirmation.'''

    class Channel(models.TextChoices):
        WHATSAPP = 'whatsapp', 'WhatsApp'
        EMAIL = 'email', 'E-mail'

    class Response(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmado'
        NOT_CONFIRMED = 'not_confirmed', 'Não confirmado'
        NO_RESPONSE = 'no_response', 'Sem resposta'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        SENT = 'sent', 'Enviada'
        RESPONDED = 'responded', 'Respondida'
        FAILED = 'failed', 'Falhou'

    appointment = models.OneToOneField(
        'scheduling.Appointment',
        on_delete=models.CASCADE,
        related_name='presence_confirmation',
    )
    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
        default=Channel.WHATSAPP,
    )
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(blank=True, null=True)
    response = models.CharField(
        max_length=20,
        choices=Response.choices,
        default=Response.NO_RESPONSE,
    )
    responded_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    delivery_error = models.TextField(blank=True)

    class Meta:
        ordering = ('scheduled_for',)
        indexes = [
            models.Index(fields=('status', 'scheduled_for')),
        ]

    def __str__(self):
        return f'Confirmação de {self.appointment}'
