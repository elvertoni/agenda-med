import json
import logging
import re
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppGateway:
    '''WhatsApp integration boundary for the chatbot.

    In production, replace the stub methods with calls to a real provider
    (e.g. Twilio, Z-API, Evolution API, Meta Cloud API).
    '''

    def send_otp(self, *, whatsapp_number, code):
        ttl = getattr(settings, 'OTP_CODE_TTL_MINUTES', 10)
        message = (
            f'Seu código de acesso para o portal do paciente é: *{code}*.\n'
            f'Ele expira em {ttl} minutos.'
        )
        return self.send_message(whatsapp_number=whatsapp_number, message=message)

    def send_presence_confirmation(self, *, whatsapp_number, appointment):
        from django.utils import timezone
        dt = timezone.localtime(appointment.scheduled_at)
        message = (
            f'Confirme sua presença na consulta com {appointment.professional.full_name} '
            f'em {dt:%d/%m/%Y às %H:%M}.\n\n'
            f'Por favor, responda *Sim* para confirmar ou *Não* para desmarcar.'
        )
        return self.send_message(whatsapp_number=whatsapp_number, message=message)

    def send_message(self, *, whatsapp_number, message):
        clean_number = re.sub(r'\D', '', whatsapp_number)

        base_url = settings.EVOLUTION_API_BASE_URL
        instance = settings.EVOLUTION_API_INSTANCE_NAME
        url = f'{base_url}/message/sendText/{instance}'

        headers = {
            'Content-Type': 'application/json',
            'apikey': settings.EVOLUTION_API_API_KEY
        }
        payload = {
            'number': clean_number,
            'text': message
        }

        logger.info(
            'Sending WhatsApp message to %s via Evolution API: %s',
            clean_number,
            url
        )

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
                logger.info('Message successfully sent to %s via Evolution API', clean_number)
                return True
        except Exception as e:
            logger.error(
                'Failed to send WhatsApp message to %s via Evolution API: %s',
                clean_number,
                e,
            )
            return False

    def parse_incoming(self, payload):
        '''Extract phone_number and message_text from the webhook payload.

        Override this method to match your provider's payload format.
        Returns (phone_number, message_text) or (None, None).
        '''
        # 1. Try Evolution API v2 format
        if isinstance(payload, dict) and 'event' in payload:
            try:
                data = payload.get('data', {})
                
                # Evolution API sometimes nests the payload inside data.message
                if 'key' not in data and 'message' in data and isinstance(data['message'], dict) and 'key' in data['message']:
                    data = data['message']
                
                key = data.get('key', {})
                # If message is fromMe, ignore it to avoid infinite loop
                if key.get('fromMe') is True:
                    logger.info('Ignoring incoming message where fromMe is True')
                    return None, None

                remote_jid = key.get('remoteJid', '')
                # extract number from remoteJid (e.g. 5511999990000@s.whatsapp.net)
                phone_number = remote_jid.split('@')[0] if '@' in remote_jid else remote_jid

                message = data.get('message', {})
                message_text = None

                if 'conversation' in message:
                    message_text = message['conversation']
                elif 'extendedTextMessage' in message:
                    message_text = message['extendedTextMessage'].get('text')

                if phone_number and message_text:
                    return phone_number, message_text
            except Exception as e:
                logger.warning('Failed to parse Evolution API payload: %s', e)

        # 2. Fallback to Meta format (for compatibility and testing)
        try:
            entry = payload['entry'][0]['changes'][0]['value']
            message_info = entry['messages'][0]
            phone_number = message_info['from']
            message_text = message_info['text']['body']
            return phone_number, message_text
        except (KeyError, IndexError, TypeError):
            logger.warning('Failed to parse incoming webhook payload')
            return None, None
