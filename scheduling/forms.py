from django import forms

from core.forms import StyledFormMixin

from .models import Appointment, AvailabilitySlot


class AvailabilitySlotForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AvailabilitySlot
        fields = ('professional', 'starts_at', 'ends_at', 'status')
        labels = {
            'professional': 'Profissional',
            'starts_at': 'Início',
            'ends_at': 'Fim',
            'status': 'Status',
        }
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get('starts_at')
        ends_at = cleaned_data.get('ends_at')
        if starts_at and ends_at and ends_at <= starts_at:
            raise forms.ValidationError('O fim deve ser posterior ao início.')
        return cleaned_data


class AppointmentCreateForm(StyledFormMixin, forms.Form):
    patient = forms.ModelChoiceField(
        label='Paciente',
        queryset=None,
    )
    availability_slot = forms.ModelChoiceField(
        label='Horário disponível',
        queryset=None,
    )
    reason = forms.CharField(
        label='Motivo da consulta',
        required=False,
        widget=forms.Textarea,
    )
    health_plan_used = forms.CharField(
        label='Plano usado',
        required=False,
        max_length=100,
    )

    def __init__(self, *args, **kwargs):
        from accounts.models import PatientProfile

        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = PatientProfile.objects.order_by('full_name')
        self.fields['availability_slot'].queryset = (
            AvailabilitySlot.objects.filter(status=AvailabilitySlot.Status.AVAILABLE)
            .select_related('professional')
            .order_by('starts_at')
        )


class AppointmentUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ('status', 'reason', 'health_plan_used')
        labels = {
            'status': 'Status',
            'reason': 'Motivo da consulta',
            'health_plan_used': 'Plano usado',
        }
