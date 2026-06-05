import random
import re
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from accounts.models import PatientProfile
from scheduling.models import Appointment

from .models import OtpCode, PresenceConfirmation
from .whatsapp import WhatsAppGateway


def normalize_whatsapp_number(value):
    return re.sub(r'\D', '', value or '')


def find_patient_by_whatsapp(whatsapp_number):
    normalized_number = normalize_whatsapp_number(whatsapp_number)
    if not normalized_number:
        return None

    for patient in PatientProfile.objects.select_related('user'):
        if normalize_whatsapp_number(patient.whatsapp_number) == normalized_number:
            return patient
    return None


def generate_otp_code():
    return ''.join(str(random.SystemRandom().randint(0, 9)) for _ in range(6))


@transaction.atomic
def request_otp(whatsapp_number, *, gateway=None):
    patient = find_patient_by_whatsapp(whatsapp_number)
    if patient is None:
        raise ValidationError('Número de WhatsApp não encontrado.')

    normalized_number = normalize_whatsapp_number(patient.whatsapp_number)
    now = timezone.now()
    OtpCode.objects.filter(
        user=patient.user,
        whatsapp_number=normalized_number,
        is_used=False,
        expires_at__gt=now,
    ).update(is_used=True, updated_at=now)

    otp = OtpCode.objects.create(
        user=patient.user,
        whatsapp_number=normalized_number,
        code=generate_otp_code(),
        expires_at=now + timedelta(minutes=settings.OTP_CODE_TTL_MINUTES),
    )

    (gateway or WhatsAppGateway()).send_otp(
        whatsapp_number=patient.whatsapp_number,
        code=otp.code,
    )
    return otp


def validate_otp(whatsapp_number, code):
    normalized_number = normalize_whatsapp_number(whatsapp_number)
    error_message = None
    user = None

    with transaction.atomic():
        otp = (
            OtpCode.objects.select_for_update()
            .filter(whatsapp_number=normalized_number, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if otp is None:
            error_message = 'Código inválido ou expirado.'
        elif otp.is_locked:
            error_message = 'Acesso bloqueado temporariamente por excesso de tentativas.'
        elif otp.is_expired:
            otp.mark_used()
            error_message = 'Código expirado. Solicite um novo código.'
        elif otp.code != (code or '').strip():
            otp.register_failed_attempt(
                max_attempts=settings.OTP_MAX_ATTEMPTS,
                lock_minutes=settings.OTP_LOCK_MINUTES,
            )
            error_message = 'Código inválido.'
        else:
            otp.mark_used()
            user = otp.user

    if error_message:
        raise ValidationError(error_message)
    return user


def schedule_presence_confirmation(
    appointment,
    *,
    channel=PresenceConfirmation.Channel.WHATSAPP,
):
    scheduled_for = appointment.scheduled_at - timedelta(hours=24)
    confirmation, _created = PresenceConfirmation.objects.update_or_create(
        appointment=appointment,
        defaults={
            'channel': channel,
            'scheduled_for': scheduled_for,
            'status': PresenceConfirmation.Status.PENDING,
            'response': PresenceConfirmation.Response.NO_RESPONSE,
            'sent_at': None,
            'responded_at': None,
            'delivery_error': '',
        },
    )
    return confirmation


def get_due_presence_confirmations(*, now=None):
    now = now or timezone.now()
    return PresenceConfirmation.objects.select_related(
        'appointment',
        'appointment__patient',
        'appointment__professional',
    ).filter(
        status=PresenceConfirmation.Status.PENDING,
        scheduled_for__lte=now,
        appointment__status=Appointment.Status.SCHEDULED,
    )


def send_presence_confirmation(confirmation, *, whatsapp_gateway=None):
    appointment = confirmation.appointment
    patient = appointment.patient
    try:
        if confirmation.channel == PresenceConfirmation.Channel.EMAIL:
            send_mail(
                subject='Confirmação de presença',
                message=(
                    f'Confirme sua presença na consulta com {appointment.professional} '
                    f'em {timezone.localtime(appointment.scheduled_at):%d/%m/%Y %H:%M}.'
                ),
                from_email=None,
                recipient_list=[patient.email],
                fail_silently=True,
            )
        else:
            (whatsapp_gateway or WhatsAppGateway()).send_presence_confirmation(
                whatsapp_number=patient.whatsapp_number,
                appointment=appointment,
            )
    except Exception as error:
        confirmation.status = PresenceConfirmation.Status.FAILED
        confirmation.delivery_error = str(error)
        confirmation.save(update_fields=['status', 'delivery_error', 'updated_at'])
        return confirmation

    confirmation.status = PresenceConfirmation.Status.SENT
    confirmation.sent_at = timezone.now()
    confirmation.delivery_error = ''
    confirmation.save(update_fields=['status', 'sent_at', 'delivery_error', 'updated_at'])
    return confirmation


def send_due_presence_confirmations(*, now=None, whatsapp_gateway=None):
    sent = 0
    failed = 0
    for confirmation in get_due_presence_confirmations(now=now):
        send_presence_confirmation(confirmation, whatsapp_gateway=whatsapp_gateway)
        if confirmation.status == PresenceConfirmation.Status.SENT:
            sent += 1
        else:
            failed += 1
    return {'sent': sent, 'failed': failed}


def record_presence_response(confirmation, response):
    if response not in PresenceConfirmation.Response.values:
        raise ValidationError('Resposta de confirmação inválida.')

    appointment = confirmation.appointment
    confirmation.response = response
    confirmation.responded_at = timezone.now()
    confirmation.status = PresenceConfirmation.Status.RESPONDED
    confirmation.save(update_fields=['response', 'responded_at', 'status', 'updated_at'])

    if response == PresenceConfirmation.Response.CONFIRMED:
        appointment.status = Appointment.Status.CONFIRMED
    elif response == PresenceConfirmation.Response.NOT_CONFIRMED:
        appointment.status = Appointment.Status.NOT_CONFIRMED
    appointment.save(update_fields=['status', 'updated_at'])
    return confirmation
