from django import forms

from core.forms import StyledFormMixin

from .models import ExamProtocol, PriceItem, ServiceProtocol


class PriceItemForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = PriceItem
        fields = ('specialty', 'name', 'description', 'price', 'is_active')
        labels = {
            'specialty': 'Especialidade',
            'name': 'Nome',
            'description': 'Descrição',
            'price': 'Preço',
            'is_active': 'Ativo',
        }


class ServiceProtocolForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceProtocol
        fields = ('title', 'content', 'is_active')
        labels = {
            'title': 'Título',
            'content': 'Conteúdo',
            'is_active': 'Ativo',
        }


class ExamProtocolForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ExamProtocol
        fields = ('specialty', 'exam_name', 'preparation_instructions', 'is_active')
        labels = {
            'specialty': 'Especialidade',
            'exam_name': 'Nome do exame',
            'preparation_instructions': 'Instruções de preparo',
            'is_active': 'Ativo',
        }
