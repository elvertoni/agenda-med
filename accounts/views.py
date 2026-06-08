from django.contrib import messages
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import (
    EmailLoginForm,
    StyledPasswordResetForm,
    StyledSetPasswordForm,
    UserRegistrationForm,
)


class EmailLoginView(LoginView):
    '''Native Django login backed by the email-based form.'''

    template_name = 'accounts/login.html'
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True


class UserRegistrationView(CreateView):
    '''View for team member self-registration.'''

    form_class = UserRegistrationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Cadastro realizado com sucesso! Faça login com suas credenciais.',
        )
        return response


class EmailPasswordResetView(PasswordResetView):
    '''View to request a password reset email link.'''

    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    form_class = StyledPasswordResetForm


class EmailPasswordResetDoneView(PasswordResetDoneView):
    '''Confirmation view that reset email has been sent.'''

    template_name = 'accounts/password_reset_done.html'


class EmailPasswordResetConfirmView(PasswordResetConfirmView):
    '''Form view to change password after clicking the reset link.'''

    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')
    form_class = StyledSetPasswordForm


class EmailPasswordResetCompleteView(PasswordResetCompleteView):
    '''Confirmation view that password reset was completed successfully.'''

    template_name = 'accounts/password_reset_complete.html'

