from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import PatientProfile, User
from professionals.models import Professional, Specialty
from scheduling.models import Appointment, AvailabilitySlot

from .chatbot import parse_intent
from .models import ChatSession, OtpCode, PresenceConfirmation
from .services import (
    find_patient_by_whatsapp,
    get_due_presence_confirmations,
    normalize_whatsapp_number,
    record_presence_response,
    request_otp,
    schedule_presence_confirmation,
    send_due_presence_confirmations,
    send_presence_confirmation,
    validate_otp,
)


class MockGateway:
    def __init__(self):
        self.sent_otp = []
        self.sent_confirmations = []
        self.sent_messages = []

    def send_otp(self, *, whatsapp_number, code):
        self.sent_otp.append({'whatsapp_number': whatsapp_number, 'code': code})
        return True

    def send_presence_confirmation(self, *, whatsapp_number, appointment):
        self.sent_confirmations.append(
            {'whatsapp_number': whatsapp_number, 'appointment': appointment}
        )
        return True

    def send_message(self, *, whatsapp_number, message):
        self.sent_messages.append(
            {'whatsapp_number': whatsapp_number, 'message': message}
        )
        return True


def make_user(**kwargs):
    defaults = {
        'email': 'user@example.com',
        'password': 'testpass123',
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_patient(user=None, whatsapp_number='5511999990000', **kwargs):
    if user is None:
        user = make_user()
    defaults = {
        'user': user,
        'full_name': 'Paciente Teste',
        'birth_date': '1990-01-01',
        'sex': 'O',
        'address': 'Rua Teste 123',
        'phone': '5511999990001',
        'whatsapp_number': whatsapp_number,
        'email': user.email,
        'cpf': '12345678901',
    }
    defaults.update(kwargs)
    return PatientProfile.objects.create(**defaults)


def make_specialty(**kwargs):
    defaults = {'name': 'Clínica Geral', 'description': 'Especialidade teste'}
    defaults.update(kwargs)
    return Specialty.objects.create(**defaults)


def make_professional(specialty=None, **kwargs):
    if specialty is None:
        specialty = make_specialty()
    defaults = {
        'specialty': specialty,
        'full_name': 'Dr. Teste',
        'registration_number': 'CRM-12345',
        'bio': 'Bio teste',
    }
    defaults.update(kwargs)
    return Professional.objects.create(**defaults)


def make_slot(professional=None, starts_at=None, **kwargs):
    if professional is None:
        professional = make_professional()
    if starts_at is None:
        starts_at = timezone.now() + timedelta(days=3)
    defaults = {
        'professional': professional,
        'starts_at': starts_at,
        'ends_at': starts_at + timedelta(hours=1),
        'status': AvailabilitySlot.Status.AVAILABLE,
    }
    defaults.update(kwargs)
    return AvailabilitySlot.objects.create(**defaults)


def make_appointment(patient=None, slot=None, **kwargs):
    if patient is None:
        patient = make_patient()
    if slot is None:
        slot = make_slot()
    defaults = {
        'patient': patient,
        'professional': slot.professional,
        'availability_slot': slot,
        'scheduled_at': slot.starts_at,
        'status': Appointment.Status.SCHEDULED,
    }
    defaults.update(kwargs)
    return Appointment.objects.create(**defaults)


class ChatSessionModelTests(TestCase):
    def test_create_session_defaults(self):
        session = ChatSession.objects.create(phone_number='5511999990000')
        self.assertEqual(session.state, ChatSession.State.IDLE)
        self.assertEqual(session.context, {})
        self.assertEqual(session.phone_number, '5511999990000')

    def test_str(self):
        session = ChatSession.objects.create(phone_number='5511999990000')
        self.assertEqual(str(session), '5511999990000 [idle]')

    def test_str_with_state(self):
        session = ChatSession.objects.create(
            phone_number='5511999990000',
            state=ChatSession.State.AWAITING_SPECIALTY,
        )
        self.assertEqual(str(session), '5511999990000 [awaiting_specialty]')

    def test_all_states(self):
        for state in ChatSession.State.values:
            session = ChatSession.objects.create(
                phone_number=f'5511{state}99990000',
                state=state,
            )
            self.assertEqual(session.state, state)

    def test_phone_number_unique(self):
        ChatSession.objects.create(phone_number='5511999990000')
        with self.assertRaises(Exception):
            ChatSession.objects.create(phone_number='5511999990000')

    def test_context_json(self):
        session = ChatSession.objects.create(
            phone_number='5511999990000',
            context={'specialty_pk': 1, 'step': 2},
        )
        session.refresh_from_db()
        self.assertEqual(session.context['specialty_pk'], 1)
        self.assertEqual(session.context['step'], 2)


class OtpCodeModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_create_otp(self):
        now = timezone.now()
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=now + timedelta(minutes=10),
        )
        self.assertFalse(otp.is_used)
        self.assertEqual(otp.attempts, 0)
        self.assertIsNone(otp.locked_until)

    def test_is_expired_false(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertFalse(otp.is_expired)

    def test_is_expired_true(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertTrue(otp.is_expired)

    def test_is_locked_false_no_locked_until(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertFalse(otp.is_locked)

    def test_is_locked_false_expired_lock(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
            locked_until=timezone.now() - timedelta(minutes=1),
        )
        self.assertFalse(otp.is_locked)

    def test_is_locked_true(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
            locked_until=timezone.now() + timedelta(minutes=15),
        )
        self.assertTrue(otp.is_locked)

    def test_mark_used(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertFalse(otp.is_used)
        otp.mark_used()
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_register_failed_attempt_increments(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        otp.register_failed_attempt(max_attempts=3, lock_minutes=15)
        otp.refresh_from_db()
        self.assertEqual(otp.attempts, 1)
        self.assertIsNone(otp.locked_until)

    def test_register_failed_attempt_locks_at_max(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        for _ in range(3):
            otp.register_failed_attempt(max_attempts=3, lock_minutes=15)
        otp.refresh_from_db()
        self.assertEqual(otp.attempts, 3)
        self.assertIsNotNone(otp.locked_until)
        self.assertTrue(otp.is_locked)

    def test_str(self):
        otp = OtpCode.objects.create(
            user=self.user,
            whatsapp_number='5511999990000',
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertEqual(str(otp), 'OTP para 5511999990000')


class PresenceConfirmationModelTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.slot = make_slot()
        self.appointment = make_appointment(patient=self.patient, slot=self.slot)

    def test_create_confirmation(self):
        confirmation = self.appointment.presence_confirmation
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.PENDING)
        self.assertEqual(
            confirmation.response, PresenceConfirmation.Response.NO_RESPONSE
        )
        self.assertEqual(confirmation.channel, PresenceConfirmation.Channel.WHATSAPP)
        self.assertIsNone(confirmation.sent_at)
        self.assertIsNone(confirmation.responded_at)
        self.assertEqual(confirmation.delivery_error, '')

    def test_str(self):
        confirmation = self.appointment.presence_confirmation
        self.assertIn('Confirmação', str(confirmation))


@override_settings(OTP_CODE_TTL_MINUTES=10, OTP_MAX_ATTEMPTS=3, OTP_LOCK_MINUTES=15)
class OtpServiceTests(TestCase):
    def test_normalize_whatsapp_number_strips_non_digits(self):
        self.assertEqual(normalize_whatsapp_number('+55 (11) 99999-0000'), '5511999990000')

    def test_normalize_whatsapp_number_none(self):
        self.assertEqual(normalize_whatsapp_number(None), '')

    def test_normalize_whatsapp_number_empty(self):
        self.assertEqual(normalize_whatsapp_number(''), '')

    def test_normalize_whatsapp_number_already_clean(self):
        self.assertEqual(normalize_whatsapp_number('5511999990000'), '5511999990000')

    def test_find_patient_by_whatsapp_success(self):
        patient = make_patient(whatsapp_number='5511999990000')
        found = find_patient_by_whatsapp('5511999990000')
        self.assertEqual(found.pk, patient.pk)

    def test_find_patient_by_whatsapp_with_formatting(self):
        patient = make_patient(whatsapp_number='+55 (11) 99999-0000')
        found = find_patient_by_whatsapp('5511999990000')
        self.assertEqual(found.pk, patient.pk)

    def test_find_patient_by_whatsapp_not_found(self):
        make_patient(whatsapp_number='5511999990000')
        self.assertIsNone(find_patient_by_whatsapp('5511999999999'))

    def test_find_patient_by_whatsapp_empty(self):
        self.assertIsNone(find_patient_by_whatsapp(''))

    @patch('messaging.services.WhatsAppGateway')
    def test_request_otp_success(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        patient = make_patient(whatsapp_number='5511999990000')

        otp = request_otp('5511999990000')

        self.assertIsNotNone(otp)
        self.assertFalse(otp.is_used)
        self.assertEqual(otp.user, patient.user)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
        self.assertEqual(len(mock_gateway.sent_otp), 1)

    @patch('messaging.services.WhatsAppGateway')
    def test_request_otp_invalidates_previous(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        make_patient(whatsapp_number='5511999990000')

        otp1 = request_otp('5511999990000')
        self.assertFalse(otp1.is_used)

        otp2 = request_otp('5511999990000')
        otp1.refresh_from_db()
        self.assertTrue(otp1.is_used)
        self.assertFalse(otp2.is_used)

    def test_request_otp_invalid_number(self):
        with self.assertRaises(ValidationError):
            request_otp('0000000000000')

    @patch('messaging.services.WhatsAppGateway')
    def test_validate_otp_success(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        patient = make_patient(whatsapp_number='5511999990000')
        otp = request_otp('5511999990000')

        user = validate_otp('5511999990000', otp.code)

        self.assertEqual(user, patient.user)
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    @patch('messaging.services.WhatsAppGateway')
    def test_validate_otp_wrong_code(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        make_patient(whatsapp_number='5511999990000')
        request_otp('5511999990000')

        with self.assertRaises(ValidationError):
            validate_otp('5511999990000', '000000')

    @patch('messaging.services.WhatsAppGateway')
    def test_validate_otp_expired(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        make_patient(whatsapp_number='5511999990000')

        otp = request_otp('5511999990000')
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save(update_fields=['expires_at'])

        with self.assertRaises(ValidationError):
            validate_otp('5511999990000', otp.code)

    @patch('messaging.services.WhatsAppGateway')
    def test_validate_otp_locked(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        make_patient(whatsapp_number='5511999990000')
        otp = request_otp('5511999990000')

        for _ in range(3):
            try:
                validate_otp('5511999990000', '000000')
            except ValidationError:
                pass

        with self.assertRaises(ValidationError) as ctx:
            validate_otp('5511999990000', otp.code)
        self.assertIn('bloqueado', str(ctx.exception))

    @patch('messaging.services.WhatsAppGateway')
    def test_validate_otp_no_code_exists(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        with self.assertRaises(ValidationError):
            validate_otp('5511999990000', '123456')


@override_settings(OTP_CODE_TTL_MINUTES=10, OTP_MAX_ATTEMPTS=3, OTP_LOCK_MINUTES=15)
class PresenceConfirmationServiceTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.specialty = make_specialty()
        self.professional = make_professional(specialty=self.specialty)
        self.slot = make_slot(professional=self.professional)
        self.appointment = make_appointment(
            patient=self.patient, slot=self.slot
        )

    def test_schedule_confirmation(self):
        confirmation = schedule_presence_confirmation(self.appointment)
        expected_scheduled = self.appointment.scheduled_at - timedelta(hours=24)
        self.assertEqual(confirmation.appointment, self.appointment)
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.PENDING)
        self.assertEqual(confirmation.channel, PresenceConfirmation.Channel.WHATSAPP)
        self.assertEqual(confirmation.scheduled_for, expected_scheduled)

    def test_schedule_confirmation_email_channel(self):
        confirmation = schedule_presence_confirmation(
            self.appointment,
            channel=PresenceConfirmation.Channel.EMAIL,
        )
        self.assertEqual(confirmation.channel, PresenceConfirmation.Channel.EMAIL)

    def test_schedule_confirmation_idempotent(self):
        c1 = schedule_presence_confirmation(self.appointment)
        c2 = schedule_presence_confirmation(self.appointment)
        self.assertEqual(c1.pk, c2.pk)

    def test_get_due_confirmations(self):
        confirmation = schedule_presence_confirmation(self.appointment)
        confirmation.scheduled_for = timezone.now() - timedelta(hours=1)
        confirmation.save(update_fields=['scheduled_for'])

        due = get_due_presence_confirmations(now=timezone.now())
        self.assertEqual(due.count(), 1)
        self.assertEqual(due.first(), confirmation)

    def test_get_due_confirmations_not_yet_due(self):
        confirmation = schedule_presence_confirmation(self.appointment)
        confirmation.scheduled_for = timezone.now() + timedelta(hours=1)
        confirmation.save(update_fields=['scheduled_for'])

        due = get_due_presence_confirmations(now=timezone.now())
        self.assertEqual(due.count(), 0)

    def test_get_due_confirmations_filters_by_appointment_status(self):
        confirmation = schedule_presence_confirmation(self.appointment)
        confirmation.scheduled_for = timezone.now() - timedelta(hours=1)
        confirmation.save(update_fields=['scheduled_for'])

        self.appointment.status = Appointment.Status.CANCELLED
        self.appointment.save(update_fields=['status'])

        due = get_due_presence_confirmations(now=timezone.now())
        self.assertEqual(due.count(), 0)

    def test_get_due_confirmations_excludes_sent(self):
        confirmation = schedule_presence_confirmation(self.appointment)
        confirmation.scheduled_for = timezone.now() - timedelta(hours=1)
        confirmation.status = PresenceConfirmation.Status.SENT
        confirmation.save(update_fields=['scheduled_for', 'status'])

        due = get_due_presence_confirmations(now=timezone.now())
        self.assertEqual(due.count(), 0)

    @patch('messaging.services.WhatsAppGateway')
    def test_send_confirmation_whatsapp(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        confirmation = schedule_presence_confirmation(self.appointment)

        result = send_presence_confirmation(confirmation)

        self.assertEqual(result.status, PresenceConfirmation.Status.SENT)
        self.assertIsNotNone(result.sent_at)
        self.assertEqual(len(mock_gateway.sent_confirmations), 1)

    @patch('messaging.services.send_mail')
    def test_send_confirmation_email(self, mock_send_mail):
        mock_send_mail.return_value = 1
        confirmation = schedule_presence_confirmation(
            self.appointment,
            channel=PresenceConfirmation.Channel.EMAIL,
        )

        result = send_presence_confirmation(confirmation)

        self.assertEqual(result.status, PresenceConfirmation.Status.SENT)
        self.assertIsNotNone(result.sent_at)
        mock_send_mail.assert_called_once()

    @patch('messaging.services.WhatsAppGateway')
    def test_send_confirmation_failure(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway.send_presence_confirmation = (
            lambda *a, **kw: (_ for _ in ()).throw(ConnectionError('timeout'))
        )
        mock_gateway_cls.return_value = mock_gateway
        confirmation = schedule_presence_confirmation(self.appointment)

        result = send_presence_confirmation(confirmation)

        self.assertEqual(result.status, PresenceConfirmation.Status.FAILED)
        self.assertIn('timeout', result.delivery_error)

    def test_record_response_confirmed(self):
        confirmation = schedule_presence_confirmation(self.appointment)

        record_presence_response(
            confirmation, PresenceConfirmation.Response.CONFIRMED
        )

        confirmation.refresh_from_db()
        self.appointment.refresh_from_db()
        self.assertEqual(
            confirmation.response, PresenceConfirmation.Response.CONFIRMED
        )
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.RESPONDED)
        self.assertIsNotNone(confirmation.responded_at)
        self.assertEqual(self.appointment.status, Appointment.Status.CONFIRMED)

    def test_record_response_not_confirmed(self):
        confirmation = schedule_presence_confirmation(self.appointment)

        record_presence_response(
            confirmation, PresenceConfirmation.Response.NOT_CONFIRMED
        )

        confirmation.refresh_from_db()
        self.appointment.refresh_from_db()
        self.assertEqual(
            confirmation.response, PresenceConfirmation.Response.NOT_CONFIRMED
        )
        self.assertEqual(self.appointment.status, Appointment.Status.NOT_CONFIRMED)

    def test_record_response_invalid(self):
        confirmation = schedule_presence_confirmation(self.appointment)

        with self.assertRaises(ValidationError):
            record_presence_response(confirmation, 'invalid_response')

    def test_record_response_no_response(self):
        confirmation = schedule_presence_confirmation(self.appointment)

        record_presence_response(
            confirmation, PresenceConfirmation.Response.NO_RESPONSE
        )

        confirmation.refresh_from_db()
        self.assertEqual(
            confirmation.response, PresenceConfirmation.Response.NO_RESPONSE
        )
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.RESPONDED)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.Status.SCHEDULED)


class ChatbotIntentTests(TestCase):
    def test_greeting_oi(self):
        self.assertEqual(
            parse_intent('oi', ChatSession.State.IDLE), 'greeting'
        )

    def test_greeting_ola(self):
        self.assertEqual(
            parse_intent('olá', ChatSession.State.IDLE), 'greeting'
        )

    def test_greeting_bom_dia(self):
        self.assertEqual(
            parse_intent('bom dia', ChatSession.State.IDLE), 'greeting'
        )

    def test_greeting_hello(self):
        self.assertEqual(
            parse_intent('hello', ChatSession.State.IDLE), 'greeting'
        )

    def test_greeting_tudo_bem(self):
        self.assertEqual(
            parse_intent('tudo bem', ChatSession.State.IDLE), 'greeting'
        )

    def test_prices(self):
        self.assertEqual(
            parse_intent('preço', ChatSession.State.IDLE), 'prices'
        )

    def test_prices_valor(self):
        self.assertEqual(
            parse_intent('valor', ChatSession.State.IDLE), 'prices'
        )

    def test_prices_quanto_custa(self):
        self.assertEqual(
            parse_intent('quanto custa', ChatSession.State.IDLE), 'prices'
        )

    def test_protocols(self):
        self.assertEqual(
            parse_intent('protocolo', ChatSession.State.IDLE), 'protocols'
        )

    def test_protocols_preparo(self):
        self.assertEqual(
            parse_intent('preparo exame', ChatSession.State.IDLE), 'protocols'
        )

    def test_availability(self):
        self.assertEqual(
            parse_intent('horário', ChatSession.State.IDLE), 'availability'
        )

    def test_availability_vagas(self):
        self.assertEqual(
            parse_intent('vagas', ChatSession.State.IDLE), 'availability'
        )

    def test_booking(self):
        self.assertEqual(
            parse_intent('agendar', ChatSession.State.IDLE), 'booking_start'
        )

    def test_booking_marcar(self):
        self.assertEqual(
            parse_intent('quero marcar consulta', ChatSession.State.IDLE),
            'booking_start',
        )

    def test_help(self):
        self.assertEqual(
            parse_intent('ajuda', ChatSession.State.IDLE), 'help'
        )

    def test_help_opcao(self):
        self.assertEqual(
            parse_intent('opção', ChatSession.State.IDLE), 'help'
        )

    def test_cancel(self):
        self.assertEqual(
            parse_intent('cancelar', ChatSession.State.AWAITING_SPECIALTY),
            'cancel',
        )

    def test_cancel_nao(self):
        self.assertEqual(
            parse_intent('não', ChatSession.State.AWAITING_SLOT), 'cancel'
        )

    def test_unknown(self):
        self.assertEqual(
            parse_intent('xyzabc123', ChatSession.State.IDLE), 'unknown'
        )

    def test_awaiting_specialty_returns_select_specialty(self):
        self.assertEqual(
            parse_intent('1', ChatSession.State.AWAITING_SPECIALTY),
            'select_specialty',
        )

    def test_awaiting_specialty_cancel(self):
        self.assertEqual(
            parse_intent('cancelar', ChatSession.State.AWAITING_SPECIALTY),
            'cancel',
        )

    def test_awaiting_slot_returns_select_slot(self):
        self.assertEqual(
            parse_intent('2', ChatSession.State.AWAITING_SLOT),
            'select_slot',
        )

    def test_awaiting_slot_cancel(self):
        self.assertEqual(
            parse_intent('voltar', ChatSession.State.AWAITING_SLOT),
            'cancel',
        )

    def test_awaiting_confirm_sim(self):
        self.assertEqual(
            parse_intent('sim', ChatSession.State.AWAITING_CONFIRM),
            'confirm_booking',
        )

    def test_awaiting_confirm_confirmo(self):
        self.assertEqual(
            parse_intent('confirmo', ChatSession.State.AWAITING_CONFIRM),
            'confirm_booking',
        )

    def test_awaiting_confirm_cancel(self):
        self.assertEqual(
            parse_intent('não', ChatSession.State.AWAITING_CONFIRM),
            'cancel',
        )

    def test_awaiting_confirm_other_returns_awaiting_confirm(self):
        self.assertEqual(
            parse_intent('talvez', ChatSession.State.AWAITING_CONFIRM),
            'awaiting_confirm',
        )


class WebhookViewTests(TestCase):
    def test_post_valid_payload(self):
        from unittest.mock import patch as umock

        payload = {
            'entry': [
                {
                    'changes': [
                        {
                            'value': {
                                'messages': [
                                    {
                                        'from': '5511999990000',
                                        'text': {'body': 'oi'},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        with umock('messaging.views.handle_incoming') as mock_handle:
            mock_handle.return_value = 'response'
            response = self.client.post(
                '/messaging/webhook/whatsapp/',
                data=payload,
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 200)
            mock_handle.assert_called_once_with('5511999990000', 'oi')

    def test_post_invalid_json(self):
        response = self.client.post(
            '/messaging/webhook/whatsapp/',
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_post_missing_message_fields(self):
        payload = {'entry': []}
        response = self.client.post(
            '/messaging/webhook/whatsapp/',
            data=payload,
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_post_valid_evolution_payload(self):
        from unittest.mock import patch as umock

        payload = {
            'event': 'messages.upsert',
            'instance': 'test_instance',
            'data': {
                'key': {
                    'remoteJid': '5511999990000@s.whatsapp.net',
                    'fromMe': False,
                    'id': 'some-msg-id'
                },
                'message': {
                    'conversation': 'oi'
                }
            }
        }
        with umock('messaging.views.handle_incoming') as mock_handle:
            mock_handle.return_value = 'response'
            response = self.client.post(
                '/messaging/webhook/whatsapp/',
                data=payload,
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 200)
            mock_handle.assert_called_once_with('5511999990000', 'oi')

    def test_post_evolution_payload_from_me_ignored(self):
        from unittest.mock import patch as umock

        payload = {
            'event': 'messages.upsert',
            'instance': 'test_instance',
            'data': {
                'key': {
                    'remoteJid': '5511999990000@s.whatsapp.net',
                    'fromMe': True,
                    'id': 'some-msg-id'
                },
                'message': {
                    'conversation': 'oi'
                }
            }
        }
        with umock('messaging.views.handle_incoming') as mock_handle:
            response = self.client.post(
                '/messaging/webhook/whatsapp/',
                data=payload,
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 200)
            mock_handle.assert_not_called()

    def test_post_evolution_extended_text_payload(self):
        from unittest.mock import patch as umock

        payload = {
            'event': 'messages.upsert',
            'instance': 'test_instance',
            'data': {
                'key': {
                    'remoteJid': '5511999990000@s.whatsapp.net',
                    'fromMe': False,
                    'id': 'some-msg-id'
                },
                'message': {
                    'extendedTextMessage': {
                        'text': 'agendar'
                    }
                }
            }
        }
        with umock('messaging.views.handle_incoming') as mock_handle:
            mock_handle.return_value = 'response'
            response = self.client.post(
                '/messaging/webhook/whatsapp/',
                data=payload,
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 200)
            mock_handle.assert_called_once_with('5511999990000', 'agendar')

    @override_settings(WHATSAPP_VERIFY_TOKEN='test-token')
    def test_get_verification_subscribe(self):
        from django.test import RequestFactory

        from .views import WhatsAppWebhookView

        factory = RequestFactory()
        request = factory.get(
            '/messaging/webhook/whatsapp/',
            {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'test-token',
                'hub.challenge': 'challenge-code',
            },
        )
        view = WhatsAppWebhookView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'challenge-code')

    @override_settings(WHATSAPP_VERIFY_TOKEN='test-token')
    def test_get_verification_wrong_token(self):
        from django.test import RequestFactory

        from .views import WhatsAppWebhookView

        factory = RequestFactory()
        request = factory.get(
            '/messaging/webhook/whatsapp/',
            {
                'hub.mode': 'subscribe',
                'hub.verify_token': 'wrong-token',
                'hub.challenge': 'challenge-code',
            },
        )
        view = WhatsAppWebhookView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 403)

    @override_settings(WHATSAPP_VERIFY_TOKEN='test-token')
    def test_get_verification_missing_params(self):
        from django.test import RequestFactory

        from .views import WhatsAppWebhookView

        request = RequestFactory().get('/messaging/webhook/whatsapp/')
        view = WhatsAppWebhookView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 403)


@override_settings(OTP_CODE_TTL_MINUTES=10, OTP_MAX_ATTEMPTS=3, OTP_LOCK_MINUTES=15)
class OtpFlowTests(TestCase):
    '''End-to-end OTP flow: request -> send -> validate -> user returned.'''

    @patch('messaging.services.WhatsAppGateway')
    def test_full_otp_flow(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        patient = make_patient(whatsapp_number='5511999990000')

        otp = request_otp('5511999990000')
        self.assertFalse(otp.is_used)
        self.assertEqual(len(mock_gateway.sent_otp), 1)

        user = validate_otp('5511999990000', otp.code)
        self.assertEqual(user, patient.user)

        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    @patch('messaging.services.WhatsAppGateway')
    def test_otp_request_invalidates_previous_codes(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        make_patient(whatsapp_number='5511999990000')

        otp1 = request_otp('5511999990000')
        otp2 = request_otp('5511999990000')

        otp1.refresh_from_db()
        self.assertTrue(otp1.is_used)
        self.assertFalse(otp2.is_used)

        with self.assertRaises(ValidationError):
            validate_otp('5511999990000', otp1.code)

    @patch('messaging.services.WhatsAppGateway')
    def test_otp_wrong_code_three_times_locks(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        make_patient(whatsapp_number='5511999990000')
        otp = request_otp('5511999990000')

        for _ in range(3):
            with self.assertRaises(ValidationError):
                validate_otp('5511999990000', '000000')

        with self.assertRaises(ValidationError) as ctx:
            validate_otp('5511999990000', otp.code)
        self.assertIn('bloqueado', str(ctx.exception))

    @patch('messaging.services.WhatsAppGateway')
    def test_otp_view_request_and_verify(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        make_patient(whatsapp_number='5511999990000')

        response = self.client.post(
            reverse('messaging:otp_request'),
            data={'whatsapp_number': '5511999990000'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('otp/verificar/', response.url)

        otp = OtpCode.objects.filter(whatsapp_number='5511999990000', is_used=False).first()
        self.assertIsNotNone(otp)

        response = self.client.post(
            reverse('messaging:otp_verify'),
            data={
                'whatsapp_number': '5511999990000',
                'code': otp.code,
            },
        )
        self.assertEqual(response.status_code, 302)

        otp.refresh_from_db()
        self.assertTrue(otp.is_used)


class AppointmentFlowTests(TestCase):
    '''End-to-end scheduling flow: slot -> reserve -> appointment + confirmation signal.'''

    def test_full_appointment_flow(self):
        patient = make_patient()
        professional = make_professional()
        slot = make_slot(professional=professional)

        from scheduling.services import reserve_slot

        appointment = reserve_slot(
            patient=patient,
            availability_slot=slot,
            reason='Consulta de rotina',
            health_plan_used='Unimed',
        )

        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)
        self.assertEqual(appointment.patient, patient)
        self.assertEqual(appointment.professional, professional)
        self.assertEqual(appointment.reason, 'Consulta de rotina')
        self.assertEqual(appointment.health_plan_used, 'Unimed')

        slot.refresh_from_db()
        self.assertEqual(slot.status, AvailabilitySlot.Status.RESERVED)

        confirmation = PresenceConfirmation.objects.filter(appointment=appointment).first()
        self.assertIsNotNone(confirmation)
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.PENDING)
        expected_scheduled = appointment.scheduled_at - timedelta(hours=24)
        self.assertEqual(confirmation.scheduled_for, expected_scheduled)

    def test_appointment_via_staff_view(self):
        staff = User.objects.create_user(email='staff@test.com', password='pass', is_staff=True)
        patient = make_patient()
        professional = make_professional()
        slot = make_slot(professional=professional)

        self.client.force_login(staff)
        response = self.client.post(
            reverse('scheduling:appointment_create'),
            data={
                'patient': patient.pk,
                'availability_slot': slot.pk,
                'reason': 'Dor de cabeça',
                'health_plan_used': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Appointment.objects.count(), 1)

        appointment = Appointment.objects.first()
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)

        slot.refresh_from_db()
        self.assertEqual(slot.status, AvailabilitySlot.Status.RESERVED)

        confirmation = PresenceConfirmation.objects.filter(appointment=appointment).first()
        self.assertIsNotNone(confirmation)


@override_settings(OTP_CODE_TTL_MINUTES=10, OTP_MAX_ATTEMPTS=3, OTP_LOCK_MINUTES=15)
class PresenceConfirmationFlowTests(TestCase):
    '''End-to-end confirmation flow: schedule -> send -> respond -> status update.'''

    @patch('messaging.services.WhatsAppGateway')
    def test_full_confirmation_flow_whatsapp(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        patient = make_patient()
        professional = make_professional()
        slot = make_slot(professional=professional)

        from scheduling.services import reserve_slot

        appointment = reserve_slot(patient=patient, availability_slot=slot)

        confirmation = appointment.presence_confirmation
        self.assertIsNotNone(confirmation)
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.PENDING)

        confirmation.scheduled_for = timezone.now() - timedelta(hours=1)
        confirmation.save(update_fields=['scheduled_for'])

        result = send_presence_confirmation(confirmation)
        self.assertEqual(result.status, PresenceConfirmation.Status.SENT)
        self.assertIsNotNone(result.sent_at)

        record_presence_response(result, PresenceConfirmation.Response.CONFIRMED)

        confirmation.refresh_from_db()
        appointment.refresh_from_db()
        self.assertEqual(confirmation.status, PresenceConfirmation.Status.RESPONDED)
        self.assertEqual(
            confirmation.response, PresenceConfirmation.Response.CONFIRMED
        )
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

    @patch('messaging.services.WhatsAppGateway')
    def test_confirmation_not_confirmed_updates_appointment(self, mock_gateway_cls):
        mock_gateway_cls.return_value = MockGateway()
        patient = make_patient()
        professional = make_professional()
        slot = make_slot(professional=professional)

        from scheduling.services import reserve_slot

        appointment = reserve_slot(patient=patient, availability_slot=slot)
        confirmation = appointment.presence_confirmation
        confirmation.scheduled_for = timezone.now() - timedelta(hours=1)
        confirmation.save(update_fields=['scheduled_for'])

        send_presence_confirmation(confirmation)
        record_presence_response(confirmation, PresenceConfirmation.Response.NOT_CONFIRMED)

        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.NOT_CONFIRMED)

    @patch('messaging.services.WhatsAppGateway')
    def test_send_due_confirmations_batch(self, mock_gateway_cls):
        mock_gateway = MockGateway()
        mock_gateway_cls.return_value = mock_gateway
        patient = make_patient()
        professional = make_professional()

        from scheduling.services import reserve_slot

        for i in range(3):
            slot = make_slot(
                professional=professional,
                starts_at=timezone.now() + timedelta(days=i + 2),
            )
            appointment = reserve_slot(patient=patient, availability_slot=slot)
            confirmation = appointment.presence_confirmation
            confirmation.scheduled_for = timezone.now() - timedelta(hours=1)
            confirmation.save(update_fields=['scheduled_for'])

        counts = send_due_presence_confirmations(now=timezone.now())
        self.assertEqual(counts['sent'], 3)
        self.assertEqual(counts['failed'], 0)
        self.assertEqual(len(mock_gateway.sent_confirmations), 3)
