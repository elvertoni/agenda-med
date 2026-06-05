from datetime import date

from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel


class AvailabilitySlot(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Disponível'
        RESERVED = 'reserved', 'Reservado'
        CANCELLED = 'cancelled', 'Cancelado'

    professional = models.ForeignKey(
        'professionals.Professional',
        on_delete=models.PROTECT,
        related_name='availability_slots',
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    class Meta:
        ordering = ('starts_at',)

    def __str__(self):
        return f'{self.professional} - {self.starts_at:%d/%m/%Y %H:%M}'


class Appointment(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Agendada'
        CONFIRMED = 'confirmed', 'Confirmada'
        NOT_CONFIRMED = 'not_confirmed', 'Não confirmada'
        CANCELLED = 'cancelled', 'Cancelada'
        COMPLETED = 'completed', 'Concluída'

    patient = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    professional = models.ForeignKey(
        'professionals.Professional',
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    availability_slot = models.OneToOneField(
        AvailabilitySlot,
        on_delete=models.PROTECT,
        related_name='appointment',
        blank=True,
        null=True,
    )
    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    reason = models.TextField(blank=True)
    health_plan_used = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ('-scheduled_at',)

    def __str__(self):
        return f'{self.patient} com {self.professional} em {self.scheduled_at:%d/%m/%Y %H:%M}'

    @property
    def patient_age(self):
        today = timezone.localdate()
        birth_date = self.patient.birth_date
        if isinstance(birth_date, str):
            birth_date = date.fromisoformat(birth_date)
        return (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
