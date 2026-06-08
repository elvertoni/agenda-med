from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

from .models import User

INPUT_CLASSES = (
    'block w-full rounded-xl border border-slate-300 bg-white '
    'px-3.5 py-2.5 text-slate-900 placeholder-slate-400 transition '
    'focus:border-health-500 focus:outline-none focus:ring-2 focus:ring-health-400/40 '
    'dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500 '
    'dark:focus:border-health-400'
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


class UserRegistrationForm(forms.ModelForm):
    '''Form for registering a new clinic team member (staff user).'''

    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        }),
    )
    confirm_password = forms.CharField(
        label='Confirmar Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': '••••••••',
        }),
    )

    class Meta:
        model = User
        fields = ['email', 'full_name']
        labels = {
            'full_name': 'Nome Completo',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'voce@exemplo.com',
                'autocomplete': 'email',
            }),
            'full_name': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nome Completo',
                'autocomplete': 'name',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'As senhas não coincidem.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = True  # Registered clinic team members have staff privileges by default
        if commit:
            user.save()
        return user


class StyledPasswordResetForm(PasswordResetForm):
    '''Subclass of PasswordResetForm with styled Tailwind inputs.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'voce@exemplo.com',
            'autocomplete': 'email',
        })


class StyledSetPasswordForm(SetPasswordForm):
    '''Subclass of SetPasswordForm with styled Tailwind inputs.'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': INPUT_CLASSES,
                'placeholder': '••••••••',
            })

