from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import StaffRequiredMixin

from .forms import ProfessionalForm, SpecialtyForm
from .models import Professional, Specialty


class SpecialtyListView(StaffRequiredMixin, ListView):
    model = Specialty
    template_name = 'professionals/specialty_list.html'
    context_object_name = 'specialties'


class SpecialtyCreateView(StaffRequiredMixin, CreateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'professionals/specialty_form.html'
    success_url = reverse_lazy('professionals:specialty_list')


class SpecialtyUpdateView(StaffRequiredMixin, UpdateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = 'professionals/specialty_form.html'
    success_url = reverse_lazy('professionals:specialty_list')


class SpecialtyDeleteView(StaffRequiredMixin, DeleteView):
    model = Specialty
    template_name = 'professionals/specialty_confirm_delete.html'
    success_url = reverse_lazy('professionals:specialty_list')


class ProfessionalListView(StaffRequiredMixin, ListView):
    model = Professional
    template_name = 'professionals/professional_list.html'
    context_object_name = 'professionals'
    queryset = Professional.objects.select_related('specialty')


class ProfessionalCreateView(StaffRequiredMixin, CreateView):
    model = Professional
    form_class = ProfessionalForm
    template_name = 'professionals/professional_form.html'
    success_url = reverse_lazy('professionals:professional_list')


class ProfessionalUpdateView(StaffRequiredMixin, UpdateView):
    model = Professional
    form_class = ProfessionalForm
    template_name = 'professionals/professional_form.html'
    success_url = reverse_lazy('professionals:professional_list')


class ProfessionalDeleteView(StaffRequiredMixin, DeleteView):
    model = Professional
    template_name = 'professionals/professional_confirm_delete.html'
    success_url = reverse_lazy('professionals:professional_list')
