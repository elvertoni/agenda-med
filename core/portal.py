from django.utils import timezone
from django.views.generic import ListView, TemplateView

from core.mixins import PatientRequiredMixin
from scheduling.models import Appointment, AvailabilitySlot


class PortalHomeView(PatientRequiredMixin, TemplateView):
    '''Patient portal shell home for authenticated patient users.'''

    template_name = 'core/portal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.request.user.patient_profile
        now = timezone.now()
        upcoming_appointments = (
            Appointment.objects.filter(patient=patient, scheduled_at__gte=now)
            .exclude(status__in=[Appointment.Status.CANCELLED, Appointment.Status.COMPLETED])
            .select_related('professional', 'professional__specialty')
            .order_by('scheduled_at')[:3]
        )
        available_slots = (
            AvailabilitySlot.objects.filter(
                starts_at__gte=now,
                status=AvailabilitySlot.Status.AVAILABLE,
                professional__is_active=True,
            )
            .select_related('professional', 'professional__specialty')
            .order_by('starts_at')[:4]
        )

        context.update(
            {
                'patient': patient,
                'upcoming_appointments': upcoming_appointments,
                'available_slots': available_slots,
            }
        )
        return context


class PortalAppointmentsView(PatientRequiredMixin, ListView):
    '''List appointments that belong to the authenticated patient.'''

    template_name = 'core/portal_appointments.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return (
            Appointment.objects.filter(patient=self.request.user.patient_profile)
            .select_related('professional', 'professional__specialty')
            .order_by('-scheduled_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.request.user.patient_profile
        return context


class PortalAvailabilityView(PatientRequiredMixin, ListView):
    '''List available appointment slots for active professionals.'''

    template_name = 'core/portal_availability.html'
    context_object_name = 'availability_slots'

    def get_queryset(self):
        return (
            AvailabilitySlot.objects.filter(
                starts_at__gte=timezone.now(),
                status=AvailabilitySlot.Status.AVAILABLE,
                professional__is_active=True,
            )
            .select_related('professional', 'professional__specialty')
            .order_by('starts_at')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.request.user.patient_profile
        return context
