from django import forms

from core.forms import StyledFormMixin


class OtpRequestForm(StyledFormMixin, forms.Form):
    whatsapp_number = forms.CharField(
        label='Número de WhatsApp',
        max_length=20,
        help_text='Informe o número cadastrado no perfil do paciente.',
    )


class OtpVerifyForm(StyledFormMixin, forms.Form):
    whatsapp_number = forms.CharField(widget=forms.HiddenInput)
    code = forms.CharField(
        label='Código recebido',
        min_length=6,
        max_length=6,
        help_text='Digite o código de 6 dígitos enviado pelo WhatsApp.',
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit():
            raise forms.ValidationError('Informe apenas números.')
        return code
