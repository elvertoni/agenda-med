# Ajustes do Chatbot WhatsApp

Mapa de tudo que precisa ser corrigido/implementado na integração WhatsApp da Agenda Clínica.

Arquivos envolvidos:
- `messaging/views.py` — webhook (entrada)
- `messaging/whatsapp.py` — gateway Evolution API (saída) + parser
- `messaging/chatbot.py` — máquina de estados + IA
- `messaging/services.py` — OTP + confirmação de presença
- `messaging/models.py` — `ChatSession`, `OtpCode`, `PresenceConfirmation`
- `config/settings.py` — variáveis de ambiente

---

## Como funciona hoje

**Fluxo de entrada:** Evolution API → `POST /messaging/webhook/` → `WhatsAppWebhookView.post` → `parse_incoming` → `handle_incoming(phone, text)`.

**Máquina de estados (agendamento guiado):**
```
IDLE → AWAITING_SPECIALTY → AWAITING_SLOT → AWAITING_CONFIRM → IDLE (reserva feita)
```

**IA (DeepSeek-v4-flash via OpenCode Go):** para mensagens gerais (preços, protocolos, ajuda, desconhecido) em estado `IDLE`. Contexto injetado: tabela de preços + protocolos. Fallback para respostas estáticas se `OPENCODE_GO_API_KEY` vazia.

**OTP:** código de 6 dígitos enviado por WhatsApp, com lock e expiração. Funciona.

**Confirmação de presença 24h:** comando `send_presence_confirmations` + `scheduling/signals.py` agendam o envio. Envio funciona; **resposta do paciente não é processada** (ver P3).

---

## Prioridade ALTA (bugs / segurança)

### P1 — Webhook GET sempre retorna 403 (verificação Meta quebrada)
**Arquivo:** `messaging/views.py:29`

```python
verify_token = getattr(request, 'whatsapp_verify_token', '')
```

`request.whatsapp_verify_token` não existe (nenhum middleware define) e não há `WHATSAPP_VERIFY_TOKEN` em settings. Resultado: token sempre `''`, verificação de webhook Meta sempre falha.

**Correção:**
- Adicionar em `config/settings.py`:
  ```python
  WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', '')
  ```
- Em `views.py`, ler de settings:
  ```python
  from django.conf import settings
  verify_token = settings.WHATSAPP_VERIFY_TOKEN
  ```
- Definir `WHATSAPP_VERIFY_TOKEN` no EasyPanel.

> Nota: Evolution API não usa o handshake GET (é do Meta Cloud API). Se o provedor for só Evolution, o GET é dispensável — mas mantê-lo correto evita 403 confuso.

---

### P2 — Webhook sem autenticação (qualquer um posta mensagem falsa)
**Arquivo:** `messaging/views.py:38` (`post`)

Endpoint `csrf_exempt` e público. Qualquer requisição POST com payload válido dispara `handle_incoming` → pode agendar consultas, disparar mensagens, gastar créditos de IA.

**Correção:** validar segredo compartilhado no header. Evolution API permite configurar header/token customizado no webhook.
```python
# settings.py
EVOLUTION_WEBHOOK_TOKEN = os.environ.get('EVOLUTION_WEBHOOK_TOKEN', '')

# views.py post()
token = request.headers.get('apikey') or request.headers.get('Authorization', '')
if settings.EVOLUTION_WEBHOOK_TOKEN and token != settings.EVOLUTION_WEBHOOK_TOKEN:
    return JsonResponse({'error': 'unauthorized'}, status=401)
```

---

### P3 — Resposta "Sim/Não" da confirmação de presença é ignorada
**Arquivos:** `messaging/chatbot.py` (`handle_incoming`) + `messaging/services.py` (`record_presence_response` já existe, mas nunca é chamada na entrada)

`send_presence_confirmation` envia "responda *Sim* para confirmar ou *Não* para desmarcar". Mas quando o paciente responde, a sessão está `IDLE` → `parse_intent` classifica como `unknown`/IA. A função `record_presence_response` existe mas **não está conectada** ao fluxo de entrada. Consulta nunca muda para `CONFIRMED`/`NOT_CONFIRMED` via WhatsApp.

**Correção:** em `handle_incoming`, antes da lógica de IA, checar se existe `PresenceConfirmation` pendente (status `SENT`, sem resposta) para o telefone. Se houver e a mensagem casar com Sim/Não, chamar `record_presence_response` e responder.

---

## Prioridade MÉDIA (UX / robustez)

### P4 — Sessão de chat nunca expira
**Arquivo:** `messaging/chatbot.py` (`_get_or_create_session`) + `messaging/models.py` (`ChatSession`)

Se o paciente abandona no meio (`AWAITING_SLOT`), a sessão fica presa nesse estado para sempre. Próxima mensagem (ex.: "oi") é interpretada como seleção de horário inválida, não como saudação.

**Correção:** ao recuperar a sessão, se `updated_at` for mais antiga que N minutos (ex.: 15), resetar para `IDLE` + limpar `context` antes de processar a intenção.
```python
SESSION_TTL_MINUTES = 15
if session.state != ChatSession.State.IDLE:
    if timezone.now() - session.updated_at > timedelta(minutes=SESSION_TTL_MINUTES):
        session.state = ChatSession.State.IDLE
        session.context = {}
        session.save(update_fields=['state', 'context', 'updated_at'])
```

---

### P5 — Agendamento via chatbot não notifica a recepção
**Arquivo:** `messaging/chatbot.py:_handle_confirm_booking`

Após `reserve_slot`, o paciente recebe confirmação, mas a equipe não é avisada. Recepção só vê se abrir o dashboard.

**Correção:** decidir o canal de notificação (e-mail para a clínica, mensagem WhatsApp para número da recepção, ou apenas confiar no dashboard). Definir com o usuário antes de implementar.

---

### P6 — Sem trava contra mensagens concorrentes (race condition)
**Arquivo:** `messaging/chatbot.py`

Duas mensagens rápidas do mesmo número podem ser processadas em paralelo, lendo o mesmo estado de sessão antes de salvar. O slot tem `select_for_update` (protegido), mas o estado da sessão não. Pode gerar respostas duplicadas/confusas.

**Correção:** `select_for_update` na sessão dentro de uma transação, ou debounce simples. Baixo risco em volume pequeno — avaliar necessidade.

---

### P7 — Timeout de rede pode travar o webhook
**Arquivos:** `messaging/whatsapp.py` (`send_message` timeout=10) + `chatbot.py:_get_ai_response` (chamada IA timeout=15)

O webhook processa de forma síncrona: recebe → chama IA (até 15s) → envia resposta (até 10s). Evolution API pode reenviar o webhook se demorar, gerando mensagens duplicadas.

**Correção:** processar `handle_incoming` de forma assíncrona (fila/thread) e responder `200` imediatamente. Solução mínima: thread em background. Solução robusta: Celery/RQ (provavelmente além do escopo atual).

---

## Prioridade BAIXA (polimento)

### P8 — `parse_intent` por substring gera falsos positivos
**Arquivo:** `messaging/chatbot.py` (`_match_any`)

"não quero agendar" contém "agendar" → dispara fluxo de agendamento. "consulta" está em `BOOKING_WORDS` e `AVAILABILITY_WORDS`. Casamento por substring é frágil.

**Correção:** casar por palavra-inteira (regex `\b`) e priorizar negações. Melhoria incremental.

### P9 — Lista de horários sem paginação
**Arquivo:** `chatbot.py:_handle_availability` (`[:20]`) e `_handle_select_specialty` (`[:15]`)

Trunca em 15-20 sem opção "ver mais". Aceitável por ora.

### P10 — Emojis de número quebram acima de 10
**Arquivo:** `chatbot.py` (`f'{idx}️⃣'`)

`11️⃣` não existe como emoji único — vira "11️⃣" malformado. Limitar a 9 opções ou usar formato `*1.*`.

### P11 — `User-Agent` de navegador na chamada de IA
**Arquivo:** `chatbot.py:call_deepseek_v4_flash`

Header `User-Agent: Mozilla/5.0...` numa chamada server-to-server é gambiarra. Limpar para algo honesto (`agenda-clinica/1.0`).

---

## Variáveis de ambiente (EasyPanel)

| Variável | Status hoje | Ação |
|---|---|---|
| `EVOLUTION_API_BASE_URL` | default `localhost:8080` | **definir** URL real |
| `EVOLUTION_API_API_KEY` | default `change-me-key` | **definir** chave real |
| `EVOLUTION_API_INSTANCE_NAME` | default `change-me-instance` | **definir** instância real |
| `OPENCODE_GO_API_KEY` | vazia (IA desligada) | definir p/ ativar IA |
| `OPENCODE_GO_BASE_URL` | `https://opencode.ai/zen/go/v1` | opcional |
| `OPENCODE_GO_MODEL` | `deepseek-v4-flash` | opcional |
| `WHATSAPP_VERIFY_TOKEN` | **não existe** (P1) | criar var + setting |
| `EVOLUTION_WEBHOOK_TOKEN` | **não existe** (P2) | criar var + setting |

---

## Ordem sugerida de execução

1. **P2** (segurança do webhook) — bloqueia abuso
2. **P3** (confirmação de presença) — feature prometida não funciona
3. **P4** (expiração de sessão) — UX quebrada comum
4. **P1** (GET webhook) — só se for usar Meta Cloud API
5. **P7** (async) — quando o volume crescer
6. **P5** (notificar recepção) — depende de decisão de produto
7. P6, P8–P11 — polimento conforme tempo
