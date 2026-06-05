import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import EmailLoginForm
from .models import PatientProfile

User = get_user_model()


def _make_user(email='user@example.com', password='segredo123', **kwargs):
    return User.objects.create_user(email=email, password=password, **kwargs)


def _make_patient(user=None, cpf='123.456.789-00', **kwargs):
    if user is None:
        user = _make_user()
    defaults = dict(
        user=user,
        full_name=kwargs.pop('full_name', 'Maria Silva'),
        birth_date=kwargs.pop('birth_date', datetime.date(1990, 1, 15)),
        sex=kwargs.pop('sex', 'F'),
        address=kwargs.pop('address', 'Rua das Flores, 10'),
        phone=kwargs.pop('phone', '(11) 99999-0000'),
        whatsapp_number=kwargs.pop('whatsapp_number', '(11) 99999-0000'),
        email=kwargs.pop('email', user.email),
        cpf=cpf,
    )
    defaults.update(kwargs)
    return PatientProfile.objects.create(**defaults)


class UserModelTests(TestCase):
    def test_create_user(self):
        user = _make_user()
        self.assertEqual(user.email, 'user@example.com')
        self.assertTrue(user.check_password('segredo123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com', password='admin123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_str_returns_email(self):
        user = _make_user()
        self.assertEqual(str(user), 'user@example.com')

    def test_email_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='segredo123')

    def test_create_superuser_must_be_staff(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com', password='admin123', is_staff=False
            )

    def test_create_superuser_must_be_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com', password='admin123', is_superuser=False
            )

    def test_is_staff_defaults_false(self):
        user = _make_user()
        self.assertFalse(user.is_staff)

    def test_email_is_unique(self):
        _make_user(email='dup@example.com')
        with self.assertRaises(Exception):
            _make_user(email='dup@example.com')

    def test_get_full_name_returns_name_or_email(self):
        user = _make_user(full_name='João Lima')
        self.assertEqual(user.get_full_name(), 'João Lima')
        user_no_name = _make_user(email='noname@example.com', full_name='')
        self.assertEqual(user_no_name.get_full_name(), 'noname@example.com')

    def test_get_short_name(self):
        user = _make_user(full_name='João Lima')
        self.assertEqual(user.get_short_name(), 'João')
        user_no_name = _make_user(email='short@example.com', full_name='')
        self.assertEqual(user_no_name.get_short_name(), 'short@example.com')

    def test_normalize_email(self):
        user = _make_user(email='UPPER@Example.COM')
        self.assertEqual(user.email, 'UPPER@example.com')


class PatientProfileModelTests(TestCase):
    def test_create_patient_profile(self):
        user = _make_user()
        patient = _make_patient(user=user)
        self.assertEqual(patient.user, user)
        self.assertEqual(patient.full_name, 'Maria Silva')
        self.assertEqual(patient.sex, 'F')
        self.assertEqual(patient.cpf, '123.456.789-00')
        self.assertIsNotNone(patient.pk)

    def test_str_returns_full_name(self):
        patient = _make_patient(full_name='Carlos Souza')
        self.assertEqual(str(patient), 'Carlos Souza')

    def test_one_to_one_relationship(self):
        user = _make_user()
        _make_patient(user=user)
        self.assertEqual(user.patient_profile, PatientProfile.objects.get(user=user))

    def test_cascade_delete(self):
        user = _make_user()
        _make_patient(user=user)
        user.delete()
        self.assertEqual(PatientProfile.objects.count(), 0)

    def test_cpf_is_unique(self):
        _make_patient(cpf='111.111.111-11')
        with self.assertRaises(Exception):
            _make_patient(cpf='111.111.111-11')

    def test_sex_choices(self):
        for sex_val in ('F', 'M', 'O'):
            user = _make_user(email=f'{sex_val.lower()}@example.com')
            patient = _make_patient(user=user, sex=sex_val, cpf=f'000.000.00{sex_val}-0')
            self.assertEqual(patient.sex, sex_val)

    def test_blank_optional_fields(self):
        user = _make_user()
        patient = _make_patient(
            user=user,
            health_plan='',
            health_plan_card='',
            emergency_contact='',
            clinical_notes='',
        )
        self.assertEqual(patient.health_plan, '')
        self.assertEqual(patient.clinical_notes, '')


class EmailLoginFormTests(TestCase):
    def test_form_has_username_email_field(self):
        form = EmailLoginForm()
        self.assertIsInstance(form.fields['username'], type(
            form.fields['username']
        ))
        self.assertEqual(form.fields['username'].label, 'E-mail')

    def test_form_has_password_field(self):
        form = EmailLoginForm()
        self.assertIn('password', form.fields)
        self.assertEqual(form.fields['password'].label, 'Senha')

    def test_invalid_login_error_portuguese(self):
        self.assertIn(
            'E-mail ou senha inválidos.',
            EmailLoginForm.error_messages['invalid_login'],
        )

    def test_inactive_error_portuguese(self):
        self.assertEqual(
            EmailLoginForm.error_messages['inactive'],
            'Esta conta está inativa.',
        )

    def test_username_field_is_email_type(self):
        form = EmailLoginForm()
        widget = form.fields['username'].widget
        self.assertEqual(widget.input_type, 'email')

    def test_password_field_is_password_type(self):
        form = EmailLoginForm()
        widget = form.fields['password'].widget
        self.assertEqual(widget.input_type, 'password')

    def test_form_invalid_with_empty_data(self):
        form = EmailLoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)


class LoginViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user(
            email='login@example.com', password='senha-forte-123', is_staff=True
        )
        cls.login_url = reverse('accounts:login')

    def test_get_login_page(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertIsInstance(response.context['form'], EmailLoginForm)

    def test_post_valid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'login@example.com',
            'password': 'senha-forte-123',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_post_invalid_password(self):
        response = self.client.post(self.login_url, {
            'username': 'login@example.com',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )
        self.assertContains(response, 'E-mail ou senha inválidos.')

    def test_post_nonexistent_email(self):
        response = self.client.post(self.login_url, {
            'username': 'noone@example.com',
            'password': 'anything',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_post_inactive_user(self):
        _make_user(
            email='inactive@example.com', password='senha-forte-123', is_active=False
        )
        response = self.client.post(self.login_url, {
            'username': 'inactive@example.com',
            'password': 'senha-forte-123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_redirect_authenticated_user(self):
        self.client.login(username='login@example.com', password='senha-forte-123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('dashboard'))

    def test_post_empty_fields(self):
        response = self.client.post(self.login_url, {
            'username': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
