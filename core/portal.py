from django.views.generic import TemplateView

from core.mixins import PatientRequiredMixin


class PortalHomeView(PatientRequiredMixin, TemplateView):
    '''Patient portal shell home for authenticated patient users.'''

    template_name = 'core/portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.request.user.patient_profile
        return context
