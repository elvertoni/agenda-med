from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Appointment, AvailabilitySlot


@transaction.atomic
def reserve_slot(*, patient, availability_slot, reason='', health_plan_used=''):
    slot = AvailabilitySlot.objects.select_for_update().select_related('professional').get(
        pk=availability_slot.pk,
    )
    if slot.status != AvailabilitySlot.Status.AVAILABLE:
        raise ValidationError('Este horário não está mais disponível.')

    appointment = Appointment.objects.create(
        patient=patient,
        professional=slot.professional,
        availability_slot=slot,
        scheduled_at=slot.starts_at,
        reason=reason,
        health_plan_used=health_plan_used,
        status=Appointment.Status.SCHEDULED,
    )
    slot.status = AvailabilitySlot.Status.RESERVED
    slot.save(update_fields=['status', 'updated_at'])
    return appointment
