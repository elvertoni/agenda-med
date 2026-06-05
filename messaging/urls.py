from django.urls import path

from .views import OtpRequestView, OtpVerifyView, WhatsAppWebhookView

app_name = 'messaging'

urlpatterns = [
    path('webhook/whatsapp/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('otp/', OtpRequestView.as_view(), name='otp_request'),
    path('otp/verificar/', OtpVerifyView.as_view(), name='otp_verify'),
]
