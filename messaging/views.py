import json
import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import FormView

from .chatbot import handle_incoming
from .forms import OtpRequestForm, OtpVerifyForm
from .services import request_otp, validate_otp
from .whatsapp import WhatsAppGateway

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    '''Webhook endpoint for incoming WhatsApp messages.'''

    def get(self, request):
        from django.conf import settings
        verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
        mode = request.GET.get('hub.mode', '')
        token = request.GET.get('hub.verify_token', '')
        challenge = request.GET.get('hub.challenge', '')

        if mode == 'subscribe' and token == verify_token:
            return HttpResponse(challenge, status=200)
        return HttpResponse(status=403)

    def post(self, request):
        from django.conf import settings
        webhook_token = getattr(settings, 'EVOLUTION_WEBHOOK_TOKEN', '')
        if webhook_token:
            token = request.headers.get('apikey') or request.headers.get('Authorization', '')
            if token != webhook_token:
                return JsonResponse({'error': 'unauthorized'}, status=401)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid payload'}, status=400)

        gateway = WhatsAppGateway()
        phone_number, message_text = gateway.parse_incoming(payload)

        if phone_number and message_text:
            def run_chatbot():
                try:
                    handle_incoming(phone_number, message_text)
                except Exception:
                    logger.exception(
                        'Error processing chatbot message from %s',
                        phone_number,
                    )
            
            import threading
            thread = threading.Thread(target=run_chatbot)
            thread.start()

        return JsonResponse({'status': 'ok'}, status=200)


class OtpRequestView(FormView):
    template_name = 'messaging/request_otp.html'
    form_class = OtpRequestForm

    def form_valid(self, form):
        whatsapp_number = form.cleaned_data['whatsapp_number']

        try:
            otp = request_otp(whatsapp_number)
        except ValidationError as error:
            form.add_error('whatsapp_number', error)
            return self.form_invalid(form)

        messages.success(self.request, 'Enviamos um código para o WhatsApp informado.')
        query_string = urlencode({'whatsapp_number': otp.whatsapp_number})
        return redirect(f'{reverse("messaging:otp_verify")}?{query_string}')


class OtpVerifyView(FormView):
    template_name = 'messaging/verify_otp.html'
    form_class = OtpVerifyForm

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET' and not request.GET.get('whatsapp_number'):
            messages.error(request, 'Informe o WhatsApp para receber um código de acesso.')
            return redirect('messaging:otp_request')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['whatsapp_number'] = self.request.GET.get('whatsapp_number', '')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['whatsapp_number'] = (
            self.request.POST.get('whatsapp_number')
            or self.request.GET.get('whatsapp_number')
            or ''
        )
        return context

    def form_valid(self, form):
        whatsapp_number = form.cleaned_data['whatsapp_number']
        code = form.cleaned_data['code']

        try:
            user = validate_otp(whatsapp_number, code)
        except ValidationError as error:
            form.add_error('code', error)
            return self.form_invalid(form)

        login(self.request, user)
        messages.success(self.request, 'Acesso confirmado. Você entrou no portal do paciente.')
        return redirect('portal_home')
