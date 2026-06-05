from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Professional, Specialty

User = get_user_model()


def _make_staff(**overrides):
    defaults = {
        'email': 'staff@clinic.com',
        'password': 'pass1234',
        'is_staff': True,
    }
    defaults.update(overrides)
    return User.objects.create_user(**defaults)


def _make_non_staff(**overrides):
    defaults = {
        'email': 'patient@clinic.com',
        'password': 'pass1234',
        'is_staff': False,
    }
    defaults.update(overrides)
    return User.objects.create_user(**defaults)


def _make_specialty(**overrides):
    defaults = {
        'name': 'Dermatologia',
        'description': 'Skin care specialty',
    }
    defaults.update(overrides)
    return Specialty.objects.create(**defaults)


def _make_professional(specialty=None, **overrides):
    if specialty is None:
        specialty = _make_specialty()
    defaults = {
        'specialty': specialty,
        'full_name': 'Dr. João Silva',
        'registration_number': 'CRM-12345',
        'bio': 'Experienced dermatologist',
        'is_active': True,
    }
    defaults.update(overrides)
    return Professional.objects.create(**defaults)


class SpecialtyModelTests(TestCase):
    def test_create_specialty_with_required_fields(self):
        s = Specialty.objects.create(name='Cardiologia')
        self.assertEqual(s.name, 'Cardiologia')
        self.assertEqual(s.description, '')
        self.assertIsNotNone(s.pk)

    def test_create_specialty_with_all_fields(self):
        s = Specialty.objects.create(name='Cardiologia', description='Heart specialty')
        self.assertEqual(s.name, 'Cardiologia')
        self.assertEqual(s.description, 'Heart specialty')

    def test_str_returns_name(self):
        s = Specialty.objects.create(name='Cardiologia')
        self.assertEqual(str(s), 'Cardiologia')

    def test_unique_name_constraint(self):
        Specialty.objects.create(name='Cardiologia')
        with self.assertRaises(IntegrityError):
            Specialty.objects.create(name='Cardiologia')

    def test_ordering_by_name(self):
        Specialty.objects.create(name='Cardiologia')
        Specialty.objects.create(name='Dermatologia')
        Specialty.objects.create(name='Anestesiologia')
        names = list(Specialty.objects.values_list('name', flat=True))
        self.assertEqual(names, ['Anestesiologia', 'Cardiologia', 'Dermatologia'])


class ProfessionalModelTests(TestCase):
    def setUp(self):
        self.specialty = _make_specialty()

    def test_create_professional_with_required_fields(self):
        p = Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. João Silva',
            registration_number='CRM-12345',
        )
        self.assertEqual(p.specialty, self.specialty)
        self.assertEqual(p.full_name, 'Dr. João Silva')
        self.assertEqual(p.registration_number, 'CRM-12345')
        self.assertEqual(p.bio, '')
        self.assertTrue(p.is_active)
        self.assertIsNotNone(p.pk)

    def test_create_professional_with_all_fields(self):
        p = Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. João Silva',
            registration_number='CRM-12345',
            bio='Experienced doctor',
            is_active=False,
        )
        self.assertEqual(p.bio, 'Experienced doctor')
        self.assertFalse(p.is_active)

    def test_str_returns_full_name(self):
        p = Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. João Silva',
            registration_number='CRM-12345',
        )
        self.assertEqual(str(p), 'Dr. João Silva')

    def test_fk_to_specialty(self):
        p = Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. João Silva',
            registration_number='CRM-12345',
        )
        self.assertEqual(p.specialty, self.specialty)
        self.assertIn(p, self.specialty.professionals.all())

    def test_protect_on_specialty_delete(self):
        Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. João Silva',
            registration_number='CRM-12345',
        )
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.specialty.delete()

    def test_ordering_by_full_name(self):
        Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. Carlos Lima',
            registration_number='CRM-001',
        )
        Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. Ana Souza',
            registration_number='CRM-002',
        )
        names = list(Professional.objects.values_list('full_name', flat=True))
        self.assertEqual(names, ['Dr. Ana Souza', 'Dr. Carlos Lima'])

    def test_is_active_default_true(self):
        p = Professional.objects.create(
            specialty=self.specialty,
            full_name='Dr. Test',
            registration_number='CRM-999',
        )
        self.assertTrue(p.is_active)

    def test_cascade_specialty_does_not_delete_when_no_professionals(self):
        pk = self.specialty.pk
        self.specialty.delete()
        self.assertFalse(Specialty.objects.filter(pk=pk).exists())


class SpecialtyViewTests(TestCase):
    def setUp(self):
        self.staff = _make_staff()
        self.non_staff = _make_non_staff()
        self.specialty = _make_specialty()

    # --- Staff access ---

    def test_specialty_list_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('professionals:specialty_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('specialties', resp.context)

    def test_specialty_create_get_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('professionals:specialty_create'))
        self.assertEqual(resp.status_code, 200)

    def test_specialty_create_post_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('professionals:specialty_create'),
            {'name': 'Neurologia', 'description': 'Brain specialty'},
        )
        self.assertRedirects(resp, reverse('professionals:specialty_list'))
        self.assertTrue(Specialty.objects.filter(name='Neurologia').exists())

    def test_specialty_update_get_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('professionals:specialty_update', kwargs={'pk': self.specialty.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_specialty_update_post_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('professionals:specialty_update', kwargs={'pk': self.specialty.pk}),
            {'name': 'Cardiologia', 'description': 'Heart specialty'},
        )
        self.assertRedirects(resp, reverse('professionals:specialty_list'))
        self.specialty.refresh_from_db()
        self.assertEqual(self.specialty.name, 'Cardiologia')

    def test_specialty_delete_get_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('professionals:specialty_delete', kwargs={'pk': self.specialty.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_specialty_delete_post_staff(self):
        self.client.force_login(self.staff)
        pk = self.specialty.pk
        resp = self.client.post(
            reverse('professionals:specialty_delete', kwargs={'pk': pk})
        )
        self.assertRedirects(resp, reverse('professionals:specialty_list'))
        self.assertFalse(Specialty.objects.filter(pk=pk).exists())

    # --- Non-staff access (authenticated but not staff) -> 403 ---

    def test_specialty_list_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(reverse('professionals:specialty_list'))
        self.assertEqual(resp.status_code, 403)

    def test_specialty_create_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(reverse('professionals:specialty_create'))
        self.assertEqual(resp.status_code, 403)

    def test_specialty_update_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(
            reverse('professionals:specialty_update', kwargs={'pk': self.specialty.pk})
        )
        self.assertEqual(resp.status_code, 403)

    def test_specialty_delete_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(
            reverse('professionals:specialty_delete', kwargs={'pk': self.specialty.pk})
        )
        self.assertEqual(resp.status_code, 403)

    # --- Anonymous access -> redirect to login ---

    def test_specialty_list_anonymous_redirect(self):
        resp = self.client.get(reverse('professionals:specialty_list'))
        login_url = '/accounts/login/'
        self.assertRedirects(resp, f'{login_url}?next={reverse("professionals:specialty_list")}')

    def test_specialty_create_anonymous_redirect(self):
        resp = self.client.get(reverse('professionals:specialty_create'))
        login_url = '/accounts/login/'
        self.assertRedirects(resp, f'{login_url}?next={reverse("professionals:specialty_create")}')

    def test_specialty_update_anonymous_redirect(self):
        resp = self.client.get(
            reverse('professionals:specialty_update', kwargs={'pk': self.specialty.pk})
        )
        login_url = '/accounts/login/'
        next_url = reverse(
            'professionals:specialty_update',
            kwargs={'pk': self.specialty.pk},
        )
        expected = f'{login_url}?next={next_url}'
        self.assertRedirects(resp, expected)

    def test_specialty_delete_anonymous_redirect(self):
        resp = self.client.get(
            reverse('professionals:specialty_delete', kwargs={'pk': self.specialty.pk})
        )
        login_url = '/accounts/login/'
        next_url = reverse(
            'professionals:specialty_delete',
            kwargs={'pk': self.specialty.pk},
        )
        expected = f'{login_url}?next={next_url}'
        self.assertRedirects(resp, expected)


class ProfessionalViewTests(TestCase):
    def setUp(self):
        self.staff = _make_staff()
        self.non_staff = _make_non_staff()
        self.specialty = _make_specialty()
        self.professional = _make_professional(specialty=self.specialty)

    # --- Staff access ---

    def test_professional_list_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('professionals:professional_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('professionals', resp.context)

    def test_professional_create_get_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('professionals:professional_create'))
        self.assertEqual(resp.status_code, 200)

    def test_professional_create_post_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('professionals:professional_create'),
            {
                'specialty': self.specialty.pk,
                'full_name': 'Dr. Maria Santos',
                'registration_number': 'CRM-99887',
                'bio': '',
                'is_active': True,
            },
        )
        self.assertRedirects(resp, reverse('professionals:professional_list'))
        self.assertTrue(Professional.objects.filter(full_name='Dr. Maria Santos').exists())

    def test_professional_update_get_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('professionals:professional_update', kwargs={'pk': self.professional.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_professional_update_post_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('professionals:professional_update', kwargs={'pk': self.professional.pk}),
            {
                'specialty': self.specialty.pk,
                'full_name': 'Dr. João Silva Updated',
                'registration_number': 'CRM-12345',
                'bio': 'Updated bio',
                'is_active': False,
            },
        )
        self.assertRedirects(resp, reverse('professionals:professional_list'))
        self.professional.refresh_from_db()
        self.assertEqual(self.professional.full_name, 'Dr. João Silva Updated')
        self.assertFalse(self.professional.is_active)

    def test_professional_delete_get_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('professionals:professional_delete', kwargs={'pk': self.professional.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_professional_delete_post_staff(self):
        self.client.force_login(self.staff)
        pk = self.professional.pk
        resp = self.client.post(
            reverse('professionals:professional_delete', kwargs={'pk': pk})
        )
        self.assertRedirects(resp, reverse('professionals:professional_list'))
        self.assertFalse(Professional.objects.filter(pk=pk).exists())

    # --- Non-staff access (authenticated but not staff) -> 403 ---

    def test_professional_list_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(reverse('professionals:professional_list'))
        self.assertEqual(resp.status_code, 403)

    def test_professional_create_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(reverse('professionals:professional_create'))
        self.assertEqual(resp.status_code, 403)

    def test_professional_update_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(
            reverse('professionals:professional_update', kwargs={'pk': self.professional.pk})
        )
        self.assertEqual(resp.status_code, 403)

    def test_professional_delete_non_staff_forbidden(self):
        self.client.force_login(self.non_staff)
        resp = self.client.get(
            reverse('professionals:professional_delete', kwargs={'pk': self.professional.pk})
        )
        self.assertEqual(resp.status_code, 403)

    # --- Anonymous access -> redirect to login ---

    def test_professional_list_anonymous_redirect(self):
        resp = self.client.get(reverse('professionals:professional_list'))
        login_url = '/accounts/login/'
        self.assertRedirects(resp, f'{login_url}?next={reverse("professionals:professional_list")}')

    def test_professional_create_anonymous_redirect(self):
        resp = self.client.get(reverse('professionals:professional_create'))
        login_url = '/accounts/login/'
        self.assertRedirects(
            resp, f'{login_url}?next={reverse("professionals:professional_create")}'
        )

    def test_professional_update_anonymous_redirect(self):
        resp = self.client.get(
            reverse('professionals:professional_update', kwargs={'pk': self.professional.pk})
        )
        login_url = '/accounts/login/'
        expected = (
            f'{login_url}?next='
            f'{reverse("professionals:professional_update", kwargs={"pk": self.professional.pk})}'
        )
        self.assertRedirects(resp, expected)

    def test_professional_delete_anonymous_redirect(self):
        resp = self.client.get(
            reverse('professionals:professional_delete', kwargs={'pk': self.professional.pk})
        )
        login_url = '/accounts/login/'
        expected = (
            f'{login_url}?next='
            f'{reverse("professionals:professional_delete", kwargs={"pk": self.professional.pk})}'
        )
        self.assertRedirects(resp, expected)
