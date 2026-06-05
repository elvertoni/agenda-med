from django.contrib.auth.views import LoginView

from .forms import EmailLoginForm


class EmailLoginView(LoginView):
    '''Native Django login backed by the email-based form.'''

    template_name = 'accounts/login.html'
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True
