from django import forms

from core.forms import StyledFormMixin

from .models import Professional, Specialty


class SpecialtyForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ('name', 'description')
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
        }


class ProfessionalForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Professional
        fields = ('specialty', 'full_name', 'registration_number', 'bio', 'is_active')
        labels = {
            'specialty': 'Especialidade',
            'full_name': 'Nome completo',
            'registration_number': 'Número de registro',
            'bio': 'Biografia',
            'is_active': 'Ativo',
        }
