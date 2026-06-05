from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from professionals.models import Specialty

from .models import ExamProtocol, PriceItem, ServiceProtocol

User = get_user_model()


def make_staff_user(**overrides):
    defaults = {
        'email': 'staff@clinic.com',
        'password': 'testpass123',
        'is_staff': True,
    }
    defaults.update(overrides)
    return User.objects.create_user(**defaults)


def make_non_staff_user(**overrides):
    defaults = {
        'email': 'patient@clinic.com',
        'password': 'testpass123',
        'is_staff': False,
    }
    defaults.update(overrides)
    return User.objects.create_user(**defaults)


def make_specialty(**overrides):
    defaults = {'name': 'Cardiologia'}
    defaults.update(overrides)
    return Specialty.objects.create(**defaults)


class PriceItemModelTests(TestCase):
    def setUp(self):
        self.specialty = make_specialty()

    def test_create_price_item(self):
        item = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta',
            price=Decimal('200.00'),
        )
        self.assertEqual(item.specialty, self.specialty)
        self.assertEqual(item.name, 'Consulta')
        self.assertEqual(item.description, '')
        self.assertEqual(item.price, Decimal('200.00'))
        self.assertTrue(item.is_active)

    def test_create_price_item_with_description(self):
        item = PriceItem.objects.create(
            specialty=self.specialty,
            name='ECG',
            description='Eletrocardiograma completo',
            price=Decimal('150.00'),
        )
        self.assertEqual(item.description, 'Eletrocardiograma completo')

    def test_str_returns_name(self):
        item = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta',
            price=Decimal('200.00'),
        )
        self.assertEqual(str(item), 'Consulta')

    def test_is_active_default_true(self):
        item = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta',
            price=Decimal('200.00'),
        )
        self.assertTrue(item.is_active)

    def test_is_active_can_be_false(self):
        item = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta',
            price=Decimal('200.00'),
            is_active=False,
        )
        self.assertFalse(item.is_active)

    def test_ordering_by_specialty_name_then_name(self):
        PriceItem.objects.all().delete()
        Specialty.objects.all().delete()
        spec_a = make_specialty(name='Anestesiologia')
        spec_b = make_specialty(name='Dermatologia')
        PriceItem.objects.create(specialty=spec_b, name='Beta', price=Decimal('100.00'))
        PriceItem.objects.create(specialty=spec_a, name='Alpha', price=Decimal('100.00'))
        PriceItem.objects.create(specialty=spec_a, name='Gamma', price=Decimal('100.00'))
        items = list(PriceItem.objects.all())
        self.assertEqual(items[0].name, 'Alpha')
        self.assertEqual(items[1].name, 'Gamma')
        self.assertEqual(items[2].name, 'Beta')


class ServiceProtocolModelTests(TestCase):
    def test_create_service_protocol(self):
        protocol = ServiceProtocol.objects.create(
            title='Atendimento Urgência',
            content='Passos para atendimento de urgência...',
        )
        self.assertEqual(protocol.title, 'Atendimento Urgência')
        self.assertEqual(protocol.content, 'Passos para atendimento de urgência...')
        self.assertTrue(protocol.is_active)

    def test_str_returns_title(self):
        protocol = ServiceProtocol.objects.create(
            title='Atendimento Urgência',
            content='conteúdo',
        )
        self.assertEqual(str(protocol), 'Atendimento Urgência')

    def test_is_active_default_true(self):
        protocol = ServiceProtocol.objects.create(
            title='Protocolo A',
            content='conteúdo',
        )
        self.assertTrue(protocol.is_active)

    def test_is_active_can_be_false(self):
        protocol = ServiceProtocol.objects.create(
            title='Protocolo A',
            content='conteúdo',
            is_active=False,
        )
        self.assertFalse(protocol.is_active)

    def test_ordering_by_title(self):
        ServiceProtocol.objects.create(title='Beta', content='c')
        ServiceProtocol.objects.create(title='Alpha', content='c')
        ServiceProtocol.objects.create(title='Gamma', content='c')
        titles = list(ServiceProtocol.objects.values_list('title', flat=True))
        self.assertEqual(titles, ['Alpha', 'Beta', 'Gamma'])


class ExamProtocolModelTests(TestCase):
    def setUp(self):
        self.specialty = make_specialty()

    def test_create_exam_protocol(self):
        protocol = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='Eletrocardiograma',
            preparation_instructions='Jejum de 4 horas.',
        )
        self.assertEqual(protocol.specialty, self.specialty)
        self.assertEqual(protocol.exam_name, 'Eletrocardiograma')
        self.assertEqual(protocol.preparation_instructions, 'Jejum de 4 horas.')
        self.assertTrue(protocol.is_active)

    def test_str_returns_exam_name(self):
        protocol = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='Eletrocardiograma',
            preparation_instructions='instruções',
        )
        self.assertEqual(str(protocol), 'Eletrocardiograma')

    def test_is_active_default_true(self):
        protocol = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='Raio-X',
            preparation_instructions='nenhuma',
        )
        self.assertTrue(protocol.is_active)

    def test_is_active_can_be_false(self):
        protocol = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='Raio-X',
            preparation_instructions='nenhuma',
            is_active=False,
        )
        self.assertFalse(protocol.is_active)

    def test_ordering_by_specialty_name_then_exam_name(self):
        ExamProtocol.objects.all().delete()
        Specialty.objects.all().delete()
        spec_a = make_specialty(name='Anestesiologia')
        spec_b = make_specialty(name='Dermatologia')
        ExamProtocol.objects.create(
            specialty=spec_b, exam_name='Biopsia', preparation_instructions='x'
        )
        ExamProtocol.objects.create(
            specialty=spec_a, exam_name='ECG', preparation_instructions='y'
        )
        ExamProtocol.objects.create(
            specialty=spec_a, exam_name='Holter', preparation_instructions='z'
        )
        protocols = list(ExamProtocol.objects.all())
        self.assertEqual(protocols[0].exam_name, 'ECG')
        self.assertEqual(protocols[1].exam_name, 'Holter')
        self.assertEqual(protocols[2].exam_name, 'Biopsia')


class StaffPriceItemViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.specialty = make_specialty()
        self.item = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta',
            price=Decimal('200.00'),
        )

    # --- list ---
    def test_list_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('clinic_content:price_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.item, resp.context['items'])

    def test_list_redirects_anonymous(self):
        resp = self.client.get(reverse('clinic_content:price_list'))
        expected = f'/accounts/login/?next={reverse("clinic_content:price_list")}'
        self.assertRedirects(resp, expected)

    def test_list_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(reverse('clinic_content:price_list'))
        self.assertEqual(resp.status_code, 403)

    # --- create ---
    def test_create_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('clinic_content:price_create'))
        self.assertEqual(resp.status_code, 200)

    def test_create_post(self):
        self.client.force_login(self.staff)
        data = {
            'specialty': self.specialty.pk,
            'name': 'Retorno',
            'description': '',
            'price': '150.00',
            'is_active': True,
        }
        resp = self.client.post(reverse('clinic_content:price_create'), data)
        self.assertRedirects(resp, reverse('clinic_content:price_list'))
        self.assertTrue(PriceItem.objects.filter(name='Retorno').exists())

    def test_create_redirects_anonymous(self):
        resp = self.client.get(reverse('clinic_content:price_create'))
        expected = f'/accounts/login/?next={reverse("clinic_content:price_create")}'
        self.assertRedirects(resp, expected)

    def test_create_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(reverse('clinic_content:price_create'))
        self.assertEqual(resp.status_code, 403)

    # --- update ---
    def test_update_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('clinic_content:price_update', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_update_post(self):
        self.client.force_login(self.staff)
        data = {
            'specialty': self.specialty.pk,
            'name': 'Consulta Atualizada',
            'description': 'nova descrição',
            'price': '250.00',
            'is_active': True,
        }
        resp = self.client.post(
            reverse('clinic_content:price_update', kwargs={'pk': self.item.pk}),
            data,
        )
        self.assertRedirects(resp, reverse('clinic_content:price_list'))
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Consulta Atualizada')
        self.assertEqual(self.item.price, Decimal('250.00'))

    def test_update_redirects_anonymous(self):
        resp = self.client.get(
            reverse('clinic_content:price_update', kwargs={'pk': self.item.pk})
        )
        url = reverse('clinic_content:price_update', kwargs={'pk': self.item.pk})
        expected = f'/accounts/login/?next={url}'
        self.assertRedirects(resp, expected)

    # --- delete ---
    def test_delete_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse('clinic_content:price_delete', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_post(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse('clinic_content:price_delete', kwargs={'pk': self.item.pk})
        )
        self.assertRedirects(resp, reverse('clinic_content:price_list'))
        self.assertFalse(PriceItem.objects.filter(pk=self.item.pk).exists())

    def test_delete_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(
            reverse('clinic_content:price_delete', kwargs={'pk': self.item.pk})
        )
        self.assertEqual(resp.status_code, 403)


class StaffServiceProtocolViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.protocol = ServiceProtocol.objects.create(
            title='Atendimento Padrão',
            content='Conteúdo do protocolo.',
        )

    # --- list ---
    def test_list_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('clinic_content:service_protocol_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.protocol, resp.context['protocols'])

    def test_list_redirects_anonymous(self):
        resp = self.client.get(reverse('clinic_content:service_protocol_list'))
        expected = (
            f'/accounts/login/?next={reverse("clinic_content:service_protocol_list")}'
        )
        self.assertRedirects(resp, expected)

    def test_list_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(reverse('clinic_content:service_protocol_list'))
        self.assertEqual(resp.status_code, 403)

    # --- create ---
    def test_create_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('clinic_content:service_protocol_create'))
        self.assertEqual(resp.status_code, 200)

    def test_create_post(self):
        self.client.force_login(self.staff)
        data = {
            'title': 'Novo Protocolo',
            'content': 'Instruções...',
            'is_active': True,
        }
        resp = self.client.post(
            reverse('clinic_content:service_protocol_create'), data
        )
        self.assertRedirects(resp, reverse('clinic_content:service_protocol_list'))
        self.assertTrue(ServiceProtocol.objects.filter(title='Novo Protocolo').exists())

    def test_create_redirects_anonymous(self):
        resp = self.client.get(reverse('clinic_content:service_protocol_create'))
        expected = (
            f'/accounts/login/?next={reverse("clinic_content:service_protocol_create")}'
        )
        self.assertRedirects(resp, expected)

    def test_create_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(reverse('clinic_content:service_protocol_create'))
        self.assertEqual(resp.status_code, 403)

    # --- update ---
    def test_update_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse(
                'clinic_content:service_protocol_update',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 200)

    def test_update_post(self):
        self.client.force_login(self.staff)
        data = {
            'title': 'Protocolo Editado',
            'content': 'Conteúdo editado.',
            'is_active': True,
        }
        resp = self.client.post(
            reverse(
                'clinic_content:service_protocol_update',
                kwargs={'pk': self.protocol.pk},
            ),
            data,
        )
        self.assertRedirects(resp, reverse('clinic_content:service_protocol_list'))
        self.protocol.refresh_from_db()
        self.assertEqual(self.protocol.title, 'Protocolo Editado')

    def test_update_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(
            reverse(
                'clinic_content:service_protocol_update',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 403)

    # --- delete ---
    def test_delete_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse(
                'clinic_content:service_protocol_delete',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_post(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse(
                'clinic_content:service_protocol_delete',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertRedirects(resp, reverse('clinic_content:service_protocol_list'))
        self.assertFalse(
            ServiceProtocol.objects.filter(pk=self.protocol.pk).exists()
        )

    def test_delete_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(
            reverse(
                'clinic_content:service_protocol_delete',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 403)


class StaffExamProtocolViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.specialty = make_specialty()
        self.protocol = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='Eletrocardiograma',
            preparation_instructions='Jejum de 4 horas.',
        )

    # --- list ---
    def test_list_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('clinic_content:exam_protocol_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.protocol, resp.context['protocols'])

    def test_list_redirects_anonymous(self):
        resp = self.client.get(reverse('clinic_content:exam_protocol_list'))
        expected = (
            f'/accounts/login/?next={reverse("clinic_content:exam_protocol_list")}'
        )
        self.assertRedirects(resp, expected)

    def test_list_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(reverse('clinic_content:exam_protocol_list'))
        self.assertEqual(resp.status_code, 403)

    # --- create ---
    def test_create_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('clinic_content:exam_protocol_create'))
        self.assertEqual(resp.status_code, 200)

    def test_create_post(self):
        self.client.force_login(self.staff)
        data = {
            'specialty': self.specialty.pk,
            'exam_name': 'Holter 24h',
            'preparation_instructions': 'Sem restrições.',
            'is_active': True,
        }
        resp = self.client.post(
            reverse('clinic_content:exam_protocol_create'), data
        )
        self.assertRedirects(resp, reverse('clinic_content:exam_protocol_list'))
        self.assertTrue(ExamProtocol.objects.filter(exam_name='Holter 24h').exists())

    def test_create_redirects_anonymous(self):
        resp = self.client.get(reverse('clinic_content:exam_protocol_create'))
        expected = (
            f'/accounts/login/?next={reverse("clinic_content:exam_protocol_create")}'
        )
        self.assertRedirects(resp, expected)

    def test_create_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(reverse('clinic_content:exam_protocol_create'))
        self.assertEqual(resp.status_code, 403)

    # --- update ---
    def test_update_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse(
                'clinic_content:exam_protocol_update',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 200)

    def test_update_post(self):
        self.client.force_login(self.staff)
        data = {
            'specialty': self.specialty.pk,
            'exam_name': 'ECG Atualizado',
            'preparation_instructions': 'Jejum de 6 horas.',
            'is_active': True,
        }
        resp = self.client.post(
            reverse(
                'clinic_content:exam_protocol_update',
                kwargs={'pk': self.protocol.pk},
            ),
            data,
        )
        self.assertRedirects(resp, reverse('clinic_content:exam_protocol_list'))
        self.protocol.refresh_from_db()
        self.assertEqual(self.protocol.exam_name, 'ECG Atualizado')

    def test_update_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(
            reverse(
                'clinic_content:exam_protocol_update',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 403)

    # --- delete ---
    def test_delete_ok_for_staff(self):
        self.client.force_login(self.staff)
        resp = self.client.get(
            reverse(
                'clinic_content:exam_protocol_delete',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 200)

    def test_delete_post(self):
        self.client.force_login(self.staff)
        resp = self.client.post(
            reverse(
                'clinic_content:exam_protocol_delete',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertRedirects(resp, reverse('clinic_content:exam_protocol_list'))
        self.assertFalse(ExamProtocol.objects.filter(pk=self.protocol.pk).exists())

    def test_delete_denied_non_staff(self):
        user = make_non_staff_user()
        self.client.force_login(user)
        resp = self.client.get(
            reverse(
                'clinic_content:exam_protocol_delete',
                kwargs={'pk': self.protocol.pk},
            )
        )
        self.assertEqual(resp.status_code, 403)


class PublicContentViewTests(TestCase):
    def setUp(self):
        self.specialty = make_specialty()
        self.active_price = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta',
            price=Decimal('200.00'),
            is_active=True,
        )
        self.inactive_price = PriceItem.objects.create(
            specialty=self.specialty,
            name='Consulta Premium',
            price=Decimal('500.00'),
            is_active=False,
        )
        self.active_service = ServiceProtocol.objects.create(
            title='Atendimento Padrão',
            content='Conteúdo ativo.',
            is_active=True,
        )
        self.inactive_service = ServiceProtocol.objects.create(
            title='Protocolo Antigo',
            content='Conteúdo inativo.',
            is_active=False,
        )
        self.active_exam = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='ECG',
            preparation_instructions='Jejum 4h.',
            is_active=True,
        )
        self.inactive_exam = ExamProtocol.objects.create(
            specialty=self.specialty,
            exam_name='ECG Especial',
            preparation_instructions='Jejum 8h.',
            is_active=False,
        )

    # --- public prices ---
    def test_public_prices_accessible_without_auth(self):
        resp = self.client.get('/precos/')
        self.assertEqual(resp.status_code, 200)

    def test_public_prices_shows_active_items(self):
        resp = self.client.get('/precos/')
        items = list(resp.context['items'])
        self.assertIn(self.active_price, items)

    def test_public_prices_hides_inactive_items(self):
        resp = self.client.get('/precos/')
        items = list(resp.context['items'])
        self.assertNotIn(self.inactive_price, items)

    # --- public service protocols ---
    def test_public_service_protocols_accessible_without_auth(self):
        resp = self.client.get('/protocolos-de-atendimento/')
        self.assertEqual(resp.status_code, 200)

    def test_public_service_protocols_shows_active(self):
        resp = self.client.get('/protocolos-de-atendimento/')
        protocols = list(resp.context['protocols'])
        self.assertIn(self.active_service, protocols)

    def test_public_service_protocols_hides_inactive(self):
        resp = self.client.get('/protocolos-de-atendimento/')
        protocols = list(resp.context['protocols'])
        self.assertNotIn(self.inactive_service, protocols)

    # --- public exam protocols ---
    def test_public_exam_protocols_accessible_without_auth(self):
        resp = self.client.get('/protocolos-de-exames/')
        self.assertEqual(resp.status_code, 200)

    def test_public_exam_protocols_shows_active(self):
        resp = self.client.get('/protocolos-de-exames/')
        protocols = list(resp.context['protocols'])
        self.assertIn(self.active_exam, protocols)

    def test_public_exam_protocols_hides_inactive(self):
        resp = self.client.get('/protocolos-de-exames/')
        protocols = list(resp.context['protocols'])
        self.assertNotIn(self.inactive_exam, protocols)
