from django.views.generic import ListView, TemplateView

from clinic_content.models import ExamProtocol, PriceItem, ServiceProtocol
from professionals.models import Professional


class LandingView(TemplateView):
    # Public landing page (Sprint 4.1.1).
    template_name = 'core/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        professionals = Professional.objects.filter(is_active=True).select_related('specialty')
        prices = PriceItem.objects.filter(is_active=True).select_related('specialty')
        service_protocols = ServiceProtocol.objects.filter(is_active=True)
        exam_protocols = ExamProtocol.objects.filter(is_active=True).select_related('specialty')

        context.update(
            {
                'featured_professionals': professionals[:3],
                'featured_prices': prices[:3],
                'featured_service_protocols': service_protocols[:2],
                'featured_exam_protocols': exam_protocols[:2],
                'professional_count': professionals.count(),
                'price_count': prices.count(),
                'service_protocol_count': service_protocols.count(),
                'exam_protocol_count': exam_protocols.count(),
            }
        )
        return context


class PublicProfessionalsView(ListView):
    # Public listing of active professionals (Sprint 4.1.2).
    template_name = 'core/public_professionals.html'
    context_object_name = 'professionals'
    queryset = Professional.objects.filter(is_active=True).select_related('specialty')
