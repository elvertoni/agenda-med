import logging
import re

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

SPECIALTY_MAP_CACHE = None


def _get_specialty_map():
    global SPECIALTY_MAP_CACHE
    if SPECIALTY_MAP_CACHE is None:
        from professionals.models import Specialty

        SPECIALTY_MAP_CACHE = {
            str(s.pk): s.name for s in Specialty.objects.all()
        }
    return SPECIALTY_MAP_CACHE


def _clear_specialty_cache():
    global SPECIALTY_MAP_CACHE
    SPECIALTY_MAP_CACHE = None


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
    normalized = normalize_whatsapp_number(phone_number)
    session, _ = ChatSession.objects.get_or_create(
        phone_number=normalized,
        defaults={'state': ChatSession.State.IDLE, 'context': {}},
    )
    return session


def _send_reply(phone_number, message):
    gateway = WhatsAppGateway()
    gateway.send_message(whatsapp_number=phone_number, message=message)


def handle_incoming(phone_number, message_text):
    session = _get_or_create_session(phone_number)
    intent = parse_intent(message_text, session.state)
    logger.info(
        'Chatbot incoming: phone=%s state=%s intent=%s',
        phone_number,
        session.state,
        intent,
    )

    handler = {
        'greeting': _handle_greeting,
        'prices': _handle_prices,
        'protocols': _handle_protocols,
        'availability': _handle_availability,
        'booking_start': _handle_booking_start,
        'select_specialty': _handle_select_specialty,
        'select_slot': _handle_select_slot,
        'confirm_booking': _handle_confirm_booking,
        'awaiting_confirm': _handle_awaiting_confirm,
        'cancel': _handle_cancel,
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

    _clear_specialty_cache()
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
