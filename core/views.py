from django.apps import apps
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import PatientProfile
from clinic_content.models import ExamProtocol, PriceItem, ServiceProtocol
from core.mixins import StaffRequiredMixin
from professionals.models import Professional, Specialty


class DashboardView(StaffRequiredMixin, TemplateView):
    '''Staff dashboard landing with operational views per domain.'''

    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_professionals = Professional.objects.filter(is_active=True)
        active_price_items = PriceItem.objects.filter(is_active=True)
        active_service_protocols = ServiceProtocol.objects.filter(is_active=True)
        active_exam_protocols = ExamProtocol.objects.filter(is_active=True)

        total_active_professionals = active_professionals.count()
        total_professionals = Professional.objects.count()
        total_specialties = Specialty.objects.count()
        total_active_price_items = active_price_items.count()
        total_price_items = PriceItem.objects.count()
        total_active_service_protocols = active_service_protocols.count()
        total_service_protocols = ServiceProtocol.objects.count()
        total_active_exam_protocols = active_exam_protocols.count()
        total_exam_protocols = ExamProtocol.objects.count()
        total_patients = PatientProfile.objects.count()
        total_active_content_items = (
            total_active_price_items + total_active_service_protocols + total_active_exam_protocols
        )

        content_updates = self._get_recent_content_updates()
        presence_confirmation_model = self._get_presence_confirmation_model()
        presence_counts = self._get_presence_confirmation_counts(presence_confirmation_model)
        recent_presence_confirmations = self._get_recent_presence_confirmations(
            presence_confirmation_model,
        )

        context.update(
            {
                'total_active_professionals': total_active_professionals,
                'total_professionals': total_professionals,
                'total_specialties': total_specialties,
                'total_active_price_items': total_active_price_items,
                'total_price_items': total_price_items,
                'total_active_service_protocols': total_active_service_protocols,
                'total_service_protocols': total_service_protocols,
                'total_active_exam_protocols': total_active_exam_protocols,
                'total_exam_protocols': total_exam_protocols,
                'total_patients': total_patients,
                'total_active_content_items': total_active_content_items,
                'dashboard_cards': [
                    {
                        'label': 'Consultas',
                        'value': presence_counts['total'],
                        'description': (
                            'Confirmações de presença vinculadas às consultas.'
                            if presence_confirmation_model is not None
                            else 'Estrutura preparada para receber confirmações de presença.'
                        ),
                        'status': (
                            'Com confirmações'
                            if presence_confirmation_model is not None
                            else 'Sem confirmações'
                        ),
                    },
                    {
                        'label': 'Profissionais ativos',
                        'value': total_active_professionals,
                        'description': f'{total_professionals} cadastro(s) no total.',
                        'url': reverse('professionals:professional_list'),
                    },
                    {
                        'label': 'Conteúdo ativo',
                        'value': total_active_content_items,
                        'description': 'Preços e protocolos publicados para consulta.',
                        'url': reverse('clinic_content:price_list'),
                    },
                ],
                'appointment_view_cards': [
                    {
                        'label': 'Pendentes',
                        'value': presence_counts['pending'],
                        'description': 'Aguardam disparo ou processamento da confirmação.',
                    },
                    {
                        'label': 'Enviadas',
                        'value': presence_counts['sent'],
                        'description': 'Mensagens enviadas e ainda sem resposta final.',
                    },
                    {
                        'label': 'Confirmadas',
                        'value': presence_counts['confirmed'],
                        'description': 'Pacientes que confirmaram presença.',
                    },
                    {
                        'label': 'Não confirmadas',
                        'value': presence_counts['not_confirmed'],
                        'description': 'Pacientes que recusaram a presença.',
                    },
                ],
                'professional_view_cards': [
                    {
                        'label': 'Profissionais',
                        'value': total_active_professionals,
                        'description': 'Ativos para exibição e futuro agendamento.',
                        'url': reverse('professionals:professional_list'),
                    },
                    {
                        'label': 'Especialidades',
                        'value': total_specialties,
                        'description': 'Categorias clínicas para cadastros e preços.',
                        'url': reverse('professionals:specialty_list'),
                    },
                    {
                        'label': 'Pacientes',
                        'value': total_patients,
                        'description': 'Perfis cadastrados na base administrativa.',
                        'url': '/admin/accounts/patientprofile/',
                    },
                ],
                'content_view_cards': [
                    {
                        'label': 'Preços',
                        'value': total_active_price_items,
                        'description': f'{total_price_items} item(ns) cadastrado(s).',
                        'url': reverse('clinic_content:price_list'),
                    },
                    {
                        'label': 'Atendimento',
                        'value': total_active_service_protocols,
                        'description': f'{total_service_protocols} protocolo(s) no total.',
                        'url': reverse('clinic_content:service_protocol_list'),
                    },
                    {
                        'label': 'Exames',
                        'value': total_active_exam_protocols,
                        'description': f'{total_exam_protocols} protocolo(s) no total.',
                        'url': reverse('clinic_content:exam_protocol_list'),
                    },
                ],
                'recent_professionals': active_professionals.select_related(
                    'specialty',
                ).order_by('-updated_at')[:4],
                'recent_content_updates': content_updates,
                'presence_confirmation_available': presence_confirmation_model is not None,
                'recent_presence_confirmations': recent_presence_confirmations,
            },
        )
        return context

    def _get_presence_confirmation_model(self):
        try:
            return apps.get_model('messaging', 'PresenceConfirmation')
        except LookupError:
            return None

    def _get_presence_confirmation_counts(self, presence_confirmation_model):
        counts = {
            'total': 0,
            'pending': 0,
            'sent': 0,
            'confirmed': 0,
            'not_confirmed': 0,
        }
        if presence_confirmation_model is None:
            return counts

        queryset = presence_confirmation_model.objects.all()
        counts['total'] = queryset.count()
        counts['pending'] = queryset.filter(
            status=presence_confirmation_model.Status.PENDING,
        ).count()
        counts['sent'] = queryset.filter(
            status=presence_confirmation_model.Status.SENT,
        ).count()
        counts['confirmed'] = queryset.filter(
            response=presence_confirmation_model.Response.CONFIRMED,
        ).count()
        counts['not_confirmed'] = queryset.filter(
            response=presence_confirmation_model.Response.NOT_CONFIRMED,
        ).count()
        return counts

    def _get_recent_presence_confirmations(self, presence_confirmation_model):
        if presence_confirmation_model is None:
            return []

        now = timezone.now()
        upcoming = presence_confirmation_model.objects.select_related(
            'appointment',
            'appointment__patient',
            'appointment__professional',
        ).filter(
            status__in=[
                presence_confirmation_model.Status.PENDING,
                presence_confirmation_model.Status.SENT,
            ],
            appointment__scheduled_at__gte=now,
        ).order_by('appointment__scheduled_at')[:5]

        if upcoming:
            return upcoming

        return presence_confirmation_model.objects.select_related(
            'appointment',
            'appointment__patient',
            'appointment__professional',
        ).order_by('-updated_at')[:5]

    def _get_recent_content_updates(self):
        updates = []

        for item in PriceItem.objects.select_related('specialty').order_by('-updated_at')[:3]:
            updates.append(
                {
                    'title': item.name,
                    'type': 'Preço',
                    'status': 'Ativo' if item.is_active else 'Inativo',
                    'updated_at': item.updated_at,
                    'url': reverse('clinic_content:price_list'),
                },
            )

        for protocol in ServiceProtocol.objects.order_by('-updated_at')[:3]:
            updates.append(
                {
                    'title': protocol.title,
                    'type': 'Atendimento',
                    'status': 'Ativo' if protocol.is_active else 'Inativo',
                    'updated_at': protocol.updated_at,
                    'url': reverse('clinic_content:service_protocol_list'),
                },
            )

        for protocol in ExamProtocol.objects.select_related('specialty').order_by(
            '-updated_at',
        )[:3]:
            updates.append(
                {
                    'title': protocol.exam_name,
                    'type': 'Exame',
                    'status': 'Ativo' if protocol.is_active else 'Inativo',
                    'updated_at': protocol.updated_at,
                    'url': reverse('clinic_content:exam_protocol_list'),
                },
            )

        return sorted(updates, key=lambda item: item['updated_at'], reverse=True)[:5]
