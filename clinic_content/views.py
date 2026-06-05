from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import StaffRequiredMixin

from .forms import ExamProtocolForm, PriceItemForm, ServiceProtocolForm
from .models import ExamProtocol, PriceItem, ServiceProtocol

# --- PriceItem ---------------------------------------------------------------

class PriceItemListView(StaffRequiredMixin, ListView):
    model = PriceItem
    template_name = 'clinic_content/price_list.html'
    context_object_name = 'items'
    queryset = PriceItem.objects.select_related('specialty')


class PriceItemCreateView(StaffRequiredMixin, CreateView):
    model = PriceItem
    form_class = PriceItemForm
    template_name = 'clinic_content/price_form.html'
    success_url = reverse_lazy('clinic_content:price_list')


class PriceItemUpdateView(StaffRequiredMixin, UpdateView):
    model = PriceItem
    form_class = PriceItemForm
    template_name = 'clinic_content/price_form.html'
    success_url = reverse_lazy('clinic_content:price_list')


class PriceItemDeleteView(StaffRequiredMixin, DeleteView):
    model = PriceItem
    template_name = 'clinic_content/price_confirm_delete.html'
    success_url = reverse_lazy('clinic_content:price_list')


# --- ServiceProtocol ---------------------------------------------------------

class ServiceProtocolListView(StaffRequiredMixin, ListView):
    model = ServiceProtocol
    template_name = 'clinic_content/service_protocol_list.html'
    context_object_name = 'protocols'


class ServiceProtocolCreateView(StaffRequiredMixin, CreateView):
    model = ServiceProtocol
    form_class = ServiceProtocolForm
    template_name = 'clinic_content/service_protocol_form.html'
    success_url = reverse_lazy('clinic_content:service_protocol_list')


class ServiceProtocolUpdateView(StaffRequiredMixin, UpdateView):
    model = ServiceProtocol
    form_class = ServiceProtocolForm
    template_name = 'clinic_content/service_protocol_form.html'
    success_url = reverse_lazy('clinic_content:service_protocol_list')


class ServiceProtocolDeleteView(StaffRequiredMixin, DeleteView):
    model = ServiceProtocol
    template_name = 'clinic_content/service_protocol_confirm_delete.html'
    success_url = reverse_lazy('clinic_content:service_protocol_list')


# --- ExamProtocol ------------------------------------------------------------

class ExamProtocolListView(StaffRequiredMixin, ListView):
    model = ExamProtocol
    template_name = 'clinic_content/exam_protocol_list.html'
    context_object_name = 'protocols'
    queryset = ExamProtocol.objects.select_related('specialty')


class ExamProtocolCreateView(StaffRequiredMixin, CreateView):
    model = ExamProtocol
    form_class = ExamProtocolForm
    template_name = 'clinic_content/exam_protocol_form.html'
    success_url = reverse_lazy('clinic_content:exam_protocol_list')


class ExamProtocolUpdateView(StaffRequiredMixin, UpdateView):
    model = ExamProtocol
    form_class = ExamProtocolForm
    template_name = 'clinic_content/exam_protocol_form.html'
    success_url = reverse_lazy('clinic_content:exam_protocol_list')


class ExamProtocolDeleteView(StaffRequiredMixin, DeleteView):
    model = ExamProtocol
    template_name = 'clinic_content/exam_protocol_confirm_delete.html'
    success_url = reverse_lazy('clinic_content:exam_protocol_list')


# --- Public pages (RF12) -----------------------------------------------------

class PublicPricesView(ListView):
    model = PriceItem
    template_name = 'clinic_content/public_prices.html'
    context_object_name = 'items'
    queryset = PriceItem.objects.filter(is_active=True).select_related('specialty')


class PublicServiceProtocolsView(ListView):
    model = ServiceProtocol
    template_name = 'clinic_content/public_service_protocols.html'
    context_object_name = 'protocols'
    queryset = ServiceProtocol.objects.filter(is_active=True)


class PublicExamProtocolsView(ListView):
    model = ExamProtocol
    template_name = 'clinic_content/public_exam_protocols.html'
    context_object_name = 'protocols'
    queryset = ExamProtocol.objects.filter(is_active=True).select_related('specialty')
