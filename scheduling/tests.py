from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import PatientProfile
from professionals.models import Professional, Specialty

from .forms import AvailabilitySlotForm
from .models import Appointment, AvailabilitySlot
from .services import reserve_slot

User = get_user_model()


def make_staff_user(email='staff@example.com', password='testpass123'):
    return User.objects.create_user(email=email, password=password, is_staff=True)


def make_non_staff_user(email='patient@example.com', password='testpass123'):
    return User.objects.create_user(email=email, password=password, is_staff=False)


def make_specialty(name='Clínica Geral'):
    return Specialty.objects.create(name=name)


def make_professional(specialty=None, full_name='Dr. House'):
    if specialty is None:
        specialty = make_specialty()
    return Professional.objects.create(
        specialty=specialty,
        full_name=full_name,
        registration_number='CRM-12345',
    )


def make_patient(user=None, full_name='Maria Silva', birth_date=None):
    if user is None:
        user = make_non_staff_user(
            email=f'{full_name.lower().replace(" ", ".")}@example.com',
        )
    if birth_date is None:
        birth_date = (timezone.localdate() - timedelta(days=30 * 365))
    return PatientProfile.objects.create(
        user=user,
        full_name=full_name,
        birth_date=birth_date,
        sex='F',
        address='Rua Teste, 123',
        phone='(11) 99999-0000',
        whatsapp_number='(11) 99999-0000',
        email=user.email,
        cpf=f'{PatientProfile.objects.count():014d}',
    )


def make_slot(professional=None, starts_at=None, ends_at=None, status=None):
    if professional is None:
        professional = make_professional()
    now = timezone.now()
    if starts_at is None:
        starts_at = now + timedelta(days=1)
    if ends_at is None:
        ends_at = starts_at + timedelta(minutes=30)
    defaults = {
        'professional': professional,
        'starts_at': starts_at,
        'ends_at': ends_at,
    }
    if status is not None:
        defaults['status'] = status
    return AvailabilitySlot.objects.create(**defaults)


class AvailabilitySlotModelTests(TestCase):
    def test_create_slot(self):
        professional = make_professional()
        starts = timezone.now() + timedelta(days=1)
        ends = starts + timedelta(minutes=30)
        slot = AvailabilitySlot.objects.create(
            professional=professional,
            starts_at=starts,
            ends_at=ends,
        )
        self.assertEqual(slot.professional, professional)
        self.assertEqual(slot.starts_at, starts)
        self.assertEqual(slot.ends_at, ends)

    def test_str(self):
        professional = make_professional(full_name='Dra. Ana')
        starts = timezone.now().replace(
            year=2026, month=6, day=5, hour=10, minute=0, second=0, microsecond=0
        )
        slot = make_slot(professional=professional, starts_at=starts)
        self.assertIn('Dra. Ana', str(slot))
        self.assertIn('05/06/2026', str(slot))

    def test_default_status_is_available(self):
        slot = make_slot()
        self.assertEqual(slot.status, AvailabilitySlot.Status.AVAILABLE)

    def test_ordering_by_starts_at(self):
        professional = make_professional()
        now = timezone.now()
        slot_c = make_slot(professional=professional, starts_at=now + timedelta(days=3))
        slot_a = make_slot(professional=professional, starts_at=now + timedelta(days=1))
        slot_b = make_slot(professional=professional, starts_at=now + timedelta(days=2))
        slots = list(AvailabilitySlot.objects.all())
        self.assertEqual(slots, [slot_a, slot_b, slot_c])


class AppointmentModelTests(TestCase):
    def test_create_appointment(self):
        patient = make_patient()
        professional = make_professional()
        slot = make_slot(professional=professional)
        appointment = Appointment.objects.create(
            patient=patient,
            professional=professional,
            availability_slot=slot,
            scheduled_at=slot.starts_at,
        )
        self.assertEqual(appointment.patient, patient)
        self.assertEqual(appointment.professional, professional)
        self.assertEqual(appointment.availability_slot, slot)

    def test_str(self):
        patient = make_patient(full_name='João Lima')
        professional = make_professional(full_name='Dr. Paulo')
        starts = timezone.now().replace(
            year=2026, month=6, day=5, hour=14, minute=30, second=0, microsecond=0
        )
        slot = make_slot(professional=professional, starts_at=starts)
        appointment = Appointment.objects.create(
            patient=patient,
            professional=professional,
            availability_slot=slot,
            scheduled_at=starts,
        )
        result = str(appointment)
        self.assertIn('João Lima', result)
        self.assertIn('Dr. Paulo', result)
        self.assertIn('05/06/2026', result)

    def test_default_status_is_scheduled(self):
        appointment = Appointment.objects.create(
            patient=make_patient(),
            professional=make_professional(),
            scheduled_at=timezone.now(),
        )
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)

    def test_patient_age(self):
        today = timezone.localdate()
        birth_date = today.replace(year=today.year - 35)
        patient = make_patient(birth_date=birth_date)
        appointment = Appointment.objects.create(
            patient=patient,
            professional=make_professional(),
            scheduled_at=timezone.now(),
        )
        self.assertEqual(appointment.patient_age, 35)

    def test_patient_age_birthday_not_yet_this_year(self):
        today = timezone.localdate()
        birth_date = today.replace(year=today.year - 40) + timedelta(days=1)
        patient = make_patient(birth_date=birth_date)
        appointment = Appointment.objects.create(
            patient=patient,
            professional=make_professional(),
            scheduled_at=timezone.now(),
        )
        self.assertEqual(appointment.patient_age, 39)

    def test_optional_fields_blank(self):
        appointment = Appointment.objects.create(
            patient=make_patient(),
            professional=make_professional(),
            scheduled_at=timezone.now(),
        )
        self.assertEqual(appointment.reason, '')
        self.assertEqual(appointment.health_plan_used, '')
        self.assertIsNone(appointment.availability_slot)


class ReserveSlotServiceTests(TestCase):
    def test_successful_reservation(self):
        patient = make_patient()
        professional = make_professional()
        slot = make_slot(professional=professional)
        appointment = reserve_slot(
            patient=patient,
            availability_slot=slot,
            reason='Checkup',
            health_plan_used='Unimed',
        )
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.patient, patient)
        self.assertEqual(appointment.professional, professional)
        self.assertEqual(appointment.availability_slot, slot)
        self.assertEqual(appointment.status, Appointment.Status.SCHEDULED)
        self.assertEqual(appointment.reason, 'Checkup')
        self.assertEqual(appointment.health_plan_used, 'Unimed')
        self.assertEqual(appointment.scheduled_at, slot.starts_at)

    def test_slot_marked_reserved(self):
        patient = make_patient()
        slot = make_slot()
        reserve_slot(patient=patient, availability_slot=slot)
        slot.refresh_from_db()
        self.assertEqual(slot.status, AvailabilitySlot.Status.RESERVED)

    def test_reject_reserved_slot(self):
        patient = make_patient()
        slot = make_slot(status=AvailabilitySlot.Status.RESERVED)
        with self.assertRaises(ValidationError):
            reserve_slot(patient=patient, availability_slot=slot)

    def test_reject_cancelled_slot(self):
        patient = make_patient()
        slot = make_slot(status=AvailabilitySlot.Status.CANCELLED)
        with self.assertRaises(ValidationError):
            reserve_slot(patient=patient, availability_slot=slot)

    def test_appointment_count_increases(self):
        patient = make_patient()
        slot = make_slot()
        self.assertEqual(Appointment.objects.count(), 0)
        reserve_slot(patient=patient, availability_slot=slot)
        self.assertEqual(Appointment.objects.count(), 1)


class AvailabilitySlotViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.non_staff = make_non_staff_user(email='nondstaff@example.com')

    def test_list_staff_access(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('scheduling:availability_slot_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_non_staff_denied(self):
        self.client.force_login(self.non_staff)
        response = self.client.get(reverse('scheduling:availability_slot_list'))
        self.assertEqual(response.status_code, 403)

    def test_create_staff_access(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('scheduling:availability_slot_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_non_staff_denied(self):
        self.client.force_login(self.non_staff)
        response = self.client.get(reverse('scheduling:availability_slot_create'))
        self.assertEqual(response.status_code, 403)

    def test_create_slot(self):
        professional = make_professional()
        starts = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        ends = (timezone.now() + timedelta(days=1, minutes=30)).strftime('%Y-%m-%dT%H:%M')
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('scheduling:availability_slot_create'),
            data={
                'professional': professional.pk,
                'starts_at': starts,
                'ends_at': ends,
                'status': AvailabilitySlot.Status.AVAILABLE,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(AvailabilitySlot.objects.count(), 1)

    def test_update_staff_access(self):
        slot = make_slot()
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse('scheduling:availability_slot_update', kwargs={'pk': slot.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_update_non_staff_denied(self):
        slot = make_slot()
        self.client.force_login(self.non_staff)
        response = self.client.get(
            reverse('scheduling:availability_slot_update', kwargs={'pk': slot.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_staff_access(self):
        slot = make_slot()
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse('scheduling:availability_slot_delete', kwargs={'pk': slot.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_non_staff_denied(self):
        slot = make_slot()
        self.client.force_login(self.non_staff)
        response = self.client.get(
            reverse('scheduling:availability_slot_delete', kwargs={'pk': slot.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_slot(self):
        slot = make_slot()
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('scheduling:availability_slot_delete', kwargs={'pk': slot.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(AvailabilitySlot.objects.count(), 0)

    def test_list_anonymous_redirects_to_login(self):
        response = self.client.get(reverse('scheduling:availability_slot_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class AppointmentViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.non_staff = make_non_staff_user(email='nonstaffappt@example.com')

    def test_list_staff_access(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('scheduling:appointment_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_non_staff_denied(self):
        self.client.force_login(self.non_staff)
        response = self.client.get(reverse('scheduling:appointment_list'))
        self.assertEqual(response.status_code, 403)

    def test_create_staff_access(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('scheduling:appointment_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_non_staff_denied(self):
        self.client.force_login(self.non_staff)
        response = self.client.get(reverse('scheduling:appointment_create'))
        self.assertEqual(response.status_code, 403)

    def test_create_appointment_via_reserve_slot(self):
        patient = make_patient()
        slot = make_slot()
        self.client.force_login(self.staff)
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
        slot.refresh_from_db()
        self.assertEqual(slot.status, AvailabilitySlot.Status.RESERVED)

    def test_create_appointment_double_booking_fails(self):
        patient = make_patient()
        slot = make_slot()
        self.client.force_login(self.staff)
        self.client.post(
            reverse('scheduling:appointment_create'),
            data={
                'patient': patient.pk,
                'availability_slot': slot.pk,
                'reason': '',
                'health_plan_used': '',
            },
        )
        patient2 = make_patient(full_name='Pedro Souza')
        response = self.client.post(
            reverse('scheduling:appointment_create'),
            data={
                'patient': patient2.pk,
                'availability_slot': slot.pk,
                'reason': '',
                'health_plan_used': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_update_staff_access(self):
        patient = make_patient()
        professional = make_professional()
        appointment = Appointment.objects.create(
            patient=patient,
            professional=professional,
            scheduled_at=timezone.now(),
        )
        self.client.force_login(self.staff)
        response = self.client.get(
            reverse('scheduling:appointment_update', kwargs={'pk': appointment.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_update_non_staff_denied(self):
        patient = make_patient()
        professional = make_professional()
        appointment = Appointment.objects.create(
            patient=patient,
            professional=professional,
            scheduled_at=timezone.now(),
        )
        self.client.force_login(self.non_staff)
        response = self.client.get(
            reverse('scheduling:appointment_update', kwargs={'pk': appointment.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_update_appointment_status(self):
        patient = make_patient()
        professional = make_professional()
        appointment = Appointment.objects.create(
            patient=patient,
            professional=professional,
            scheduled_at=timezone.now(),
        )
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('scheduling:appointment_update', kwargs={'pk': appointment.pk}),
            data={
                'status': Appointment.Status.CONFIRMED,
                'reason': '',
                'health_plan_used': '',
            },
        )
        self.assertEqual(response.status_code, 302)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

    def test_list_anonymous_redirects_to_login(self):
        response = self.client.get(reverse('scheduling:appointment_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class SchedulingFormTests(TestCase):
    def test_availability_slot_form_valid(self):
        professional = make_professional()
        starts = timezone.now() + timedelta(days=1)
        ends = starts + timedelta(minutes=30)
        form = AvailabilitySlotForm(data={
            'professional': professional.pk,
            'starts_at': starts.strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': ends.strftime('%Y-%m-%d %H:%M:%S'),
            'status': AvailabilitySlot.Status.AVAILABLE,
        })
        self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_availability_slot_form_end_before_start_invalid(self):
        professional = make_professional()
        starts = timezone.now() + timedelta(days=1)
        ends = starts - timedelta(minutes=30)
        form = AvailabilitySlotForm(data={
            'professional': professional.pk,
            'starts_at': starts.strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': ends.strftime('%Y-%m-%d %H:%M:%S'),
            'status': AvailabilitySlot.Status.AVAILABLE,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('O fim deve ser posterior ao início.', form.non_field_errors())

    def test_availability_slot_form_end_equal_start_invalid(self):
        professional = make_professional()
        dt = timezone.now() + timedelta(days=1)
        form = AvailabilitySlotForm(data={
            'professional': professional.pk,
            'starts_at': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'ends_at': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'status': AvailabilitySlot.Status.AVAILABLE,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('O fim deve ser posterior ao início.', form.non_field_errors())
