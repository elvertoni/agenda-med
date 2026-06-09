import json
import logging
import re
import urllib.error
import urllib.request

from django.conf import settings
from django.utils import timezone

from clinic_content.models import ExamProtocol, PriceItem, ServiceProtocol
from scheduling.models import AvailabilitySlot

from .models import ChatSession
from .services import find_patient_by_whatsapp, normalize_whatsapp_number
from .whatsapp import WhatsAppGateway

logger = logging.getLogger(__name__)

GREETING_WORDS = (
    'oi', 'ola', 'olá', 'bom dia', 'boa tarde', 'boa noite',
    'hello', 'hi', 'hey', 'eai', 'e ai', 'tudo bem',
)
PRICE_WORDS = (
    'preco', 'preço', 'valor', 'custo', 'quanto custa', 'valores',
    'precos', 'valores', 'tabela',
)
PROTOCOL_WORDS = (
    'protocolo', 'preparo', 'instrucao', 'instrução', 'exame',
    'protocolos', 'preparos',
)
AVAILABILITY_WORDS = (
    'horario', 'horário', 'horarios', 'horários', 'agenda',
    'disponibilidade', 'vaga', 'vagas', 'consultar',
)
BOOKING_WORDS = (
    'agendar', 'marcar', 'consulta', 'agendamento',
    'marcar consulta', 'quero agendar',
)
CONFIRM_WORDS = ('sim', 'confirmo', 'confirmar', 'quero', 'isso', 'esse', 'este')
CANCEL_WORDS = (
    'nao', 'não', 'cancelar', 'cancela', 'desistir', 'voltar',
    'menu', 'inicio', 'início', 'cancela',
)
HELP_WORDS = (
    'ajuda', 'help', 'opcao', 'opção', 'opcoes', 'opções',
    'comandos', 'o que posso', 'oq posso',
)


def _normalize(text):
    return re.sub(r'\s+', ' ', text.lower().strip())


def _match_any(text, words):
    norm = _normalize(text)
    for w in words:
        if w in norm:
            return True
    return False


def parse_intent(text, session_state):
    norm = _normalize(text)

    if session_state == ChatSession.State.AWAITING_SPECIALTY:
        if _match_any(norm, CANCEL_WORDS):
            return 'cancel'
        return 'select_specialty'

    if session_state == ChatSession.State.AWAITING_SLOT:
        if _match_any(norm, CANCEL_WORDS):
            return 'cancel'
        return 'select_slot'

    if session_state == ChatSession.State.AWAITING_CONFIRM:
        if _match_any(norm, CONFIRM_WORDS):
            return 'confirm_booking'
        if _match_any(norm, CANCEL_WORDS):
            return 'cancel'
        return 'awaiting_confirm'

    if _match_any(norm, HELP_WORDS):
        return 'help'
    if _match_any(norm, BOOKING_WORDS):
        return 'booking_start'
    if _match_any(norm, AVAILABILITY_WORDS):
        return 'availability'
    if _match_any(norm, PRICE_WORDS):
        return 'prices'
    if _match_any(norm, PROTOCOL_WORDS):
        return 'protocols'
    if _match_any(norm, GREETING_WORDS):
        return 'greeting'

    return 'unknown'


def _get_or_create_session(phone_number):
    from datetime import timedelta
    normalized = normalize_whatsapp_number(phone_number)
    session, created = ChatSession.objects.get_or_create(
        phone_number=normalized,
        defaults={'state': ChatSession.State.IDLE, 'context': {}},
    )
    if not created and session.state != ChatSession.State.IDLE:
        SESSION_TTL_MINUTES = 15
        if timezone.now() - session.updated_at > timedelta(minutes=SESSION_TTL_MINUTES):
            session.state = ChatSession.State.IDLE
            session.context = {}
            session.save(update_fields=['state', 'context', 'updated_at'])
    return session


def _send_reply(phone_number, message):
    gateway = WhatsAppGateway()
    gateway.send_message(whatsapp_number=phone_number, message=message)


def call_deepseek_v4_flash(message_text, system_prompt):
    api_key = getattr(settings, 'OPENCODE_GO_API_KEY', '')
    if not api_key:
        logger.warning('OPENCODE_GO_API_KEY not configured. Falling back to default responses.')
        return None

    base_url = getattr(settings, 'OPENCODE_GO_BASE_URL', 'https://opencode.ai/zen/go/v1')
    model = getattr(settings, 'OPENCODE_GO_MODEL', 'deepseek-v4-flash')
    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'agenda-clinica/1.0',
    }

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': message_text}
        ]
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error('Failed to query DeepSeek-v4-flash via OpenCode Go: %s', e)
        return None


def _get_ai_response(message_text):
    # Fetch price items
    prices = PriceItem.objects.filter(is_active=True).select_related('specialty')
    prices_list = []
    current_spec = None
    for item in prices:
        if item.specialty.name != current_spec:
            current_spec = item.specialty.name
            prices_list.append(f'\n🏥 {current_spec}:')
        desc = f' — {item.description}' if item.description else ''
        prices_list.append(f'  • {item.name}{desc}: R$ {item.price:.2f}')
    prices_text = '\n'.join(prices_list) if prices_list else 'Nenhum preço cadastrado no momento.'

    # Fetch protocols
    service_protocols = ServiceProtocol.objects.filter(is_active=True)
    exam_protocols = ExamProtocol.objects.filter(is_active=True).select_related('specialty')
    protocols_list = []
    if exam_protocols.exists():
        protocols_list.append('Protocolos de exames:')
        for ep in exam_protocols:
            protocols_list.append(f'🔬 {ep.exam_name} ({ep.specialty.name}): {ep.preparation_instructions}')
    if service_protocols.exists():
        protocols_list.append('\nProtocolos de atendimento:')
        for sp in service_protocols:
            protocols_list.append(f'📋 {sp.title}: {sp.content}')
    protocols_text = '\n'.join(protocols_list) if protocols_list else 'Nenhum protocolo cadastrado no momento.'

    system_prompt = (
        'Você é o assistente virtual inteligente de atendimento da Clínica Médica.\n'
        'Seu objetivo é ajudar os pacientes com dúvidas sobre preços, exames, atendimentos e agendamento.\n\n'
        'Aqui estão as informações oficiais e atualizadas da clínica. Use apenas estas informações para responder a dúvidas de preços e protocolos:\n\n'
        '[TABELA DE PREÇOS]\n'
        f'{prices_text}\n\n'
        '[PROTOCOLOS DE ATENDIMENTO E EXAME]\n'
        f'{protocols_text}\n\n'
        '[DIRETRIZES DE AGENDAMENTO]\n'
        '- Para agendar uma consulta ou ver os horários disponíveis, o paciente deve iniciar o fluxo escrevendo a palavra "agendar" ou "marcar consulta".\n'
        '- Se o paciente demonstrar interesse em agendar, oriente-o de forma curta e direta a digitar "agendar".\n\n'
        '[DIRETRIZES DE RESPOSTA]\n'
        '- Responda sempre em português brasileiro de forma educada, prestativa, simpática e muito objetiva (evite textos excessivamente longos).\n'
        '- Nunca invente informações de preços ou protocolos que não estejam listados acima. Se não souber ou não encontrar a informação nas listas acima, responda educadamente que não possui essa informação e oriente o paciente a solicitar falar com a recepção humana.'
    )

    return call_deepseek_v4_flash(message_text, system_prompt)


def handle_incoming(phone_number, message_text):
    session = _get_or_create_session(phone_number)

    # Verifica resposta de confirmação de presença
    patient = find_patient_by_whatsapp(phone_number)
    if patient:
        from .models import PresenceConfirmation
        from .services import record_presence_response
        confirmation = PresenceConfirmation.objects.filter(
            status=PresenceConfirmation.Status.SENT,
            channel=PresenceConfirmation.Channel.WHATSAPP,
            appointment__patient=patient
        ).order_by('-sent_at').first()

        if confirmation:
            norm_msg = _normalize(message_text)
            is_yes = any(word in norm_msg for word in ('sim', 'confirmo', 'confirmar', 'vou', 'quero'))
            is_no = any(word in norm_msg for word in ('não', 'nao', 'cancelar', 'desmarcar', 'desisto', 'não vou', 'nao vou'))

            if is_yes and not is_no:
                record_presence_response(confirmation, PresenceConfirmation.Response.CONFIRMED)
                response = 'Obrigado! Sua presença foi confirmada com sucesso.'
                _send_reply(phone_number, response)
                return response
            elif is_no:
                record_presence_response(confirmation, PresenceConfirmation.Response.NOT_CONFIRMED)
                response = 'Entendido. Sua consulta foi desmarcada. Se precisar reagendar, digite *agendar*.'
                _send_reply(phone_number, response)
                return response

    intent = parse_intent(message_text, session.state)
    logger.info(
        'Chatbot incoming: phone=%s state=%s intent=%s',
        phone_number,
        session.state,
        intent,
    )

    # Se a sessão não estiver IDLE, ela está no meio de um fluxo de agendamento guiado
    if session.state != ChatSession.State.IDLE:
        handler = {
            'select_specialty': _handle_select_specialty,
            'select_slot': _handle_select_slot,
            'confirm_booking': _handle_confirm_booking,
            'awaiting_confirm': _handle_awaiting_confirm,
            'cancel': _handle_cancel,
        }.get(intent, _handle_unknown)
        response = handler(session, message_text)
        _send_reply(phone_number, response)
        return response

    # Se a intenção for iniciar agendamento, ver horários ou cancelar explicitamente
    if intent in ('booking_start', 'availability', 'cancel'):
        handler = {
            'booking_start': _handle_booking_start,
            'availability': _handle_availability,
            'cancel': _handle_cancel,
        }[intent]
        response = handler(session, message_text)
        _send_reply(phone_number, response)
        return response

    # Para conversas gerais, preços, protocolos, ajuda ou desconhecidos, usamos o DeepSeek
    ai_response = None
    if getattr(settings, 'OPENCODE_GO_API_KEY', ''):
        ai_response = _get_ai_response(message_text)

    if ai_response:
        response = ai_response
    else:
        # Fallback para handlers estáticos originais
        handler = {
            'greeting': _handle_greeting,
            'prices': _handle_prices,
            'protocols': _handle_protocols,
            'help': _handle_help,
            'unknown': _handle_unknown,
        }.get(intent, _handle_unknown)
        response = handler(session, message_text)

    _send_reply(phone_number, response)
    return response


def _handle_greeting(session, text):
    return (
        'Olá! Sou o assistente virtual da clínica. '
        'Posso ajudar com:\n\n'
        '1️⃣ *Preços* — valores de consultas e procedimentos\n'
        '2️⃣ *Protocolos* — instruções de preparo para exames\n'
        '3️⃣ *Horários* — ver agenda disponível\n'
        '4️⃣ *Agendar* — marcar uma consulta\n\n'
        'Digite o que deseja ou envie *ajuda* para mais opções.'
    )


def _handle_help(session, text):
    return (
        '*Comandos disponíveis:*\n\n'
        '• *preços* — consultar valores\n'
        '• *protocolos* — instruções de exames\n'
        '• *horários* — ver agenda disponível\n'
        '• *agendar* — iniciar agendamento\n'
        '• *cancelar* — voltar ao menu principal\n'
        '• *ajuda* — mostrar esta mensagem\n\n'
        'A qualquer momento, digite *cancelar* para voltar ao menu.'
    )


def _handle_prices(session, text):
    items = PriceItem.objects.filter(is_active=True).select_related('specialty')
    if not items:
        return 'No momento não há preços cadastrados. Entre em contato com a clínica.'

    lines = ['*Tabela de preços:*\n']
    current_specialty = None
    for item in items:
        if item.specialty.name != current_specialty:
            current_specialty = item.specialty.name
            lines.append(f'\n🏥 *{current_specialty}*')
        desc = f' — {item.description}' if item.description else ''
        lines.append(f'  • {item.name}{desc}: R$ {item.price:.2f}')

    return '\n'.join(lines)


def _handle_protocols(session, text):
    query = _normalize(text)
    for word in PROTOCOL_WORDS:
        query = query.replace(word, '', 1).strip()

    service_protocols = ServiceProtocol.objects.filter(is_active=True)
    exam_protocols = ExamProtocol.objects.filter(is_active=True).select_related(
        'specialty',
    )

    if query and len(query) > 2:
        exam_protocols = exam_protocols.filter(
            exam_name__icontains=query,
        ) | exam_protocols.filter(
            specialty__name__icontains=query,
        )
        service_protocols = service_protocols.filter(
            title__icontains=query,
        ) | service_protocols.filter(
            content__icontains=query,
        )

    lines = []
    if exam_protocols.exists():
        lines.append('*Protocolos de exames:*\n')
        for ep in exam_protocols:
            lines.append(f'🔬 *{ep.exam_name}* ({ep.specialty.name})')
            lines.append(f'  {ep.preparation_instructions}')
            lines.append('')

    if service_protocols.exists():
        lines.append('*Protocolos de atendimento:*\n')
        for sp in service_protocols:
            lines.append(f'📋 *{sp.title}*')
            content_preview = sp.content[:300] + ('...' if len(sp.content) > 300 else '')
            lines.append(f'  {content_preview}')
            lines.append('')

    if not lines:
        return (
            'Nenhum protocolo encontrado. '
            'Tente especificar o nome do exame ou especialidade.'
        )

    return '\n'.join(lines)


def _handle_availability(session, text):
    now = timezone.now()
    slots = (
        AvailabilitySlot.objects.filter(
            status=AvailabilitySlot.Status.AVAILABLE,
            starts_at__gte=now,
        )
        .select_related('professional', 'professional__specialty')
        .order_by('starts_at')[:20]
    )

    if not slots.exists():
        return 'No momento não há horários disponíveis. Tente novamente mais tarde.'

    lines = ['*Horários disponíveis:*\n']
    for slot in slots:
        dt = timezone.localtime(slot.starts_at)
        lines.append(
            f'🕐 {dt:%d/%m/%Y às %H:%M} — '
            f'{slot.professional.full_name} ({slot.professional.specialty.name})'
        )

    lines.append('\nDeseja agendar? Digite *agendar* para iniciar.')
    return '\n'.join(lines)


def _handle_booking_start(session, text):
    patient = find_patient_by_whatsapp(session.phone_number)
    if patient is None:
        return (
            'Para agendar, seu WhatsApp precisa estar cadastrado na clínica. '
            'Entre em contato com a recepção para cadastrar seu perfil.'
        )

    from professionals.models import Specialty

    specialties = Specialty.objects.all().order_by('name')
    if not specialties.exists():
        return 'Nenhuma especialidade cadastrada no momento.'

    lines = [
        '*Agendamento — Escolha a especialidade:*\n',
    ]
    for idx, spec in enumerate(specialties, 1):
        lines.append(f'{idx}️⃣ {spec.name}')

    lines.append('\nDigite o *número* da especialidade desejada ou *cancelar* para voltar.')

    specialty_map = {str(idx): spec.pk for idx, spec in enumerate(specialties, 1)}
    specialty_name_map = {str(idx): spec.name for idx, spec in enumerate(specialties, 1)}

    session.state = ChatSession.State.AWAITING_SPECIALTY
    session.context = {
        'patient_pk': patient.pk,
        'specialty_map': specialty_map,
        'specialty_name_map': specialty_name_map,
    }
    session.save(update_fields=['state', 'context', 'updated_at'])

    return '\n'.join(lines)


def _handle_select_specialty(session, text):
    choice = _normalize(text).strip()
    specialty_map = session.context.get('specialty_map', {})
    specialty_name_map = session.context.get('specialty_name_map', {})

    if choice not in specialty_map:
        valid = ', '.join(specialty_map.keys())
        return (
            f'Opção inválida. Digite o número da especialidade ({valid}) '
            f'ou *cancelar* para voltar.'
        )

    specialty_pk = specialty_map[choice]
    specialty_name = specialty_name_map.get(choice, '')

    now = timezone.now()
    slots = (
        AvailabilitySlot.objects.filter(
            status=AvailabilitySlot.Status.AVAILABLE,
            starts_at__gte=now,
            professional__specialty_id=specialty_pk,
            professional__is_active=True,
        )
        .select_related('professional')
        .order_by('starts_at')[:15]
    )

    if not slots.exists():
        return (
            f'Não há horários disponíveis para *{specialty_name}* no momento. '
            f'Digite *agendar* para tentar outra especialidade ou *cancelar* para voltar.'
        )

    lines = [f'*Horários para {specialty_name}:*\n']
    slot_map = {}
    for idx, slot in enumerate(slots, 1):
        dt = timezone.localtime(slot.starts_at)
        lines.append(
            f'{idx}️⃣ {dt:%d/%m/%Y às %H:%M} — {slot.professional.full_name}'
        )
        slot_map[str(idx)] = slot.pk

    lines.append('\nDigite o *número* do horário desejado ou *cancelar* para voltar.')

    session.state = ChatSession.State.AWAITING_SLOT
    session.context['slot_map'] = slot_map
    session.context['specialty_name'] = specialty_name
    session.save(update_fields=['state', 'context', 'updated_at'])

    return '\n'.join(lines)


def _handle_select_slot(session, text):
    choice = _normalize(text).strip()
    slot_map = session.context.get('slot_map', {})

    if choice not in slot_map:
        valid = ', '.join(slot_map.keys())
        return (
            f'Opção inválida. Digite o número do horário ({valid}) '
            f'ou *cancelar* para voltar.'
        )

    slot_pk = slot_map[choice]
    slot = (
        AvailabilitySlot.objects.filter(
            pk=slot_pk,
            status=AvailabilitySlot.Status.AVAILABLE,
        )
        .select_related('professional', 'professional__specialty')
        .first()
    )

    if slot is None:
        session.state = ChatSession.State.IDLE
        session.context = {}
        session.save(update_fields=['state', 'context', 'updated_at'])
        return (
            'Este horário não está mais disponível. '
            'Digite *agendar* para recomeçar.'
        )

    dt = timezone.localtime(slot.starts_at)
    specialty_name = session.context.get('specialty_name', slot.professional.specialty.name)
    confirm_text = (
        f'*Confirmar agendamento:*\n\n'
        f'📅 Data: {dt:%d/%m/%Y}\n'
        f'🕐 Horário: {dt:%H:%M}\n'
        f'👨‍⚕️ Profissional: {slot.professional.full_name}\n'
        f'🏥 Especialidade: {specialty_name}\n\n'
        f'Digite *sim* para confirmar ou *cancelar* para voltar.'
    )

    session.state = ChatSession.State.AWAITING_CONFIRM
    session.context['selected_slot_pk'] = slot_pk
    session.save(update_fields=['state', 'context', 'updated_at'])

    return confirm_text


def _handle_confirm_booking(session, text):
    slot_pk = session.context.get('selected_slot_pk')
    patient_pk = session.context.get('patient_pk')

    if not slot_pk or not patient_pk:
        session.state = ChatSession.State.IDLE
        session.context = {}
        session.save(update_fields=['state', 'context', 'updated_at'])
        return 'Sessão expirada. Digite *agendar* para recomeçar.'

    from accounts.models import PatientProfile
    from scheduling.services import reserve_slot

    patient = PatientProfile.objects.filter(pk=patient_pk).first()
    slot = (
        AvailabilitySlot.objects.filter(
            pk=slot_pk,
            status=AvailabilitySlot.Status.AVAILABLE,
        )
        .select_related('professional')
        .first()
    )

    if patient is None:
        session.state = ChatSession.State.IDLE
        session.context = {}
        session.save(update_fields=['state', 'context', 'updated_at'])
        return 'Paciente não encontrado. Digite *agendar* para recomeçar.'

    if slot is None:
        session.state = ChatSession.State.IDLE
        session.context = {}
        session.save(update_fields=['state', 'context', 'updated_at'])
        return 'Horário não está mais disponível. Digite *agendar* para recomeçar.'

    try:
        appointment = reserve_slot(
            patient=patient,
            availability_slot=slot,
            reason='Agendado via WhatsApp',
        )
    except Exception as e:
        logger.error('Chatbot booking failed: %s', e)
        session.state = ChatSession.State.IDLE
        session.context = {}
        session.save(update_fields=['state', 'context', 'updated_at'])
        return (
            'Não foi possível concluir o agendamento. '
            'Por favor, entre em contato com a clínica.'
        )

    dt = timezone.localtime(appointment.scheduled_at)
    session.state = ChatSession.State.IDLE
    session.context = {}
    session.save(update_fields=['state', 'context', 'updated_at'])

    return (
        f'✅ *Agendamento confirmado!*\n\n'
        f'📅 Data: {dt:%d/%m/%Y}\n'
        f'🕐 Horário: {dt:%H:%M}\n'
        f'👨‍⚕️ Profissional: {slot.professional.full_name}\n\n'
        f'Você receberá um lembrete 24h antes da consulta. '
        f'Digite *ajuda* para mais opções.'
    )


def _handle_awaiting_confirm(session, text):
    return (
        'Por favor, responda *sim* para confirmar o agendamento '
        'ou *cancelar* para voltar.'
    )


def _handle_cancel(session, text):
    session.state = ChatSession.State.IDLE
    session.context = {}
    session.save(update_fields=['state', 'context', 'updated_at'])
    return (
        'Operação cancelada. Digite *ajuda* para ver as opções disponíveis.'
    )


def _handle_unknown(session, text):
    return (
        'Não entendi sua mensagem. Digite *ajuda* para ver as opções disponíveis.'
    )
