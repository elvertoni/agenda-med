from django.urls import reverse
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
                        'value': '--',
                        'description': 'Estrutura preparada para receber a agenda da Sprint 5.',
                        'status': 'Sem scheduling',
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
                        'label': 'Hoje',
                        'value': '--',
                        'description': 'Grade diária aguardando a app de agendamento.',
                    },
                    {
                        'label': 'Solicitações',
                        'value': '--',
                        'description': 'Fila operacional prevista para a Sprint 5.',
                    },
                    {
                        'label': 'Confirmações',
                        'value': '--',
                        'description': 'Status de presença entra na Sprint 7.',
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
            },
        )
        return context

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
