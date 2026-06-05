from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from core.mixins import StaffRequiredMixin

from .forms import AppointmentCreateForm, AppointmentUpdateForm, AvailabilitySlotForm
from .models import Appointment, AvailabilitySlot
from .services import reserve_slot

DATETIME_LOCAL_FORMAT = '%Y-%m-%dT%H:%M'


class AvailabilitySlotFormViewMixin:
    model = AvailabilitySlot
    form_class = AvailabilitySlotForm
    template_name = 'scheduling/availability_slot_form.html'
    success_url = reverse_lazy('scheduling:availability_slot_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name in ('starts_at', 'ends_at'):
            field = form.fields[field_name]
            field.input_formats = [DATETIME_LOCAL_FORMAT]
            field.widget.format = DATETIME_LOCAL_FORMAT
        return form


class AvailabilitySlotListView(StaffRequiredMixin, ListView):
    model = AvailabilitySlot
    template_name = 'scheduling/availability_slot_list.html'
    context_object_name = 'slots'
    queryset = AvailabilitySlot.objects.select_related(
        'professional',
        'professional__specialty',
    )


class AvailabilitySlotCreateView(StaffRequiredMixin, AvailabilitySlotFormViewMixin, CreateView):
    pass


class AvailabilitySlotUpdateView(StaffRequiredMixin, AvailabilitySlotFormViewMixin, UpdateView):
    queryset = AvailabilitySlot.objects.select_related('professional')


class AvailabilitySlotDeleteView(StaffRequiredMixin, DeleteView):
    model = AvailabilitySlot
    template_name = 'scheduling/availability_slot_confirm_delete.html'
    success_url = reverse_lazy('scheduling:availability_slot_list')

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                'Este horário já está vinculado a uma consulta e não pode ser excluído.',
            )
            return redirect(self.get_success_url())


class AppointmentListView(StaffRequiredMixin, ListView):
    model = Appointment
    template_name = 'scheduling/appointment_list.html'
    context_object_name = 'appointments'
    queryset = Appointment.objects.select_related(
        'patient',
        'professional',
        'professional__specialty',
        'availability_slot',
    )


class AppointmentCreateView(StaffRequiredMixin, FormView):
    form_class = AppointmentCreateForm
    template_name = 'scheduling/appointment_form.html'
    success_url = reverse_lazy('scheduling:appointment_list')
    page_title = 'Nova consulta'

    def form_valid(self, form):
        try:
            self.object = reserve_slot(
                patient=form.cleaned_data['patient'],
                availability_slot=form.cleaned_data['availability_slot'],
                reason=form.cleaned_data.get('reason', ''),
                health_plan_used=form.cleaned_data.get('health_plan_used', ''),
            )
        except ValidationError as error:
            form.add_error('availability_slot', error)
            return self.form_invalid(form)

        messages.success(self.request, 'Consulta agendada com sucesso.')
        return super().form_valid(form)


class AppointmentUpdateView(StaffRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentUpdateForm
    template_name = 'scheduling/appointment_form.html'
    success_url = reverse_lazy('scheduling:appointment_list')
    page_title = 'Editar consulta'
    queryset = Appointment.objects.select_related('patient', 'professional', 'availability_slot')
