from django import forms
from django.contrib.auth.forms import AuthenticationForm

INPUT_CLASSES = (
    'block w-full rounded-xl border border-slate-700 bg-slate-900 '
    'px-3.5 py-2.5 text-slate-100 placeholder-slate-500 transition '
    'focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/40'
)


class EmailLoginForm(AuthenticationForm):
    '''Email + password login form. Messages do not reveal which field failed.'''

    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'voce@exemplo.com',
            'autofocus': True,
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'autocomplete': 'current-password',
        }),
    )

    error_messages = {
        'invalid_login': 'E-mail ou senha inválidos.',
        'inactive': 'Esta conta está inativa.',
    }
