# Deploy — Agenda Clínica

Guia de deploy e configuração do sistema de agendamento para clínica médica.

---

## Variáveis de Ambiente

### Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `DJANGO_SECRET_KEY` | Chave secreta do Django (gerar com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) | `abc123...` |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula | `agendamed.tonicoimbra.com,localhost` |
| `DEBUG` | Modo debug (`True`/`False`) | `False` |
| `EVOLUTION_API_BASE_URL` | URL base da Evolution API | `https://evoapi.tonicoimbra.com` |
| `EVOLUTION_API_API_KEY` | API key da Evolution API | `G0Ea13Q4...` |
| `EVOLUTION_API_INSTANCE_NAME` | Nome da instância WhatsApp | `CLINICA` |

### Opcionais

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_PATH` | Caminho absoluto do SQLite | `<BASE_DIR>/db.sqlite3` |
| `OPENCODE_GO_API_KEY` | API key do OpenCode Go (DeepSeek) para chatbot IA | `""` (desativado) |
| `OPENCODE_GO_BASE_URL` | URL base do OpenCode Go | `https://opencode.ai/zen/go/v1` |
| `OPENCODE_GO_MODEL` | Modelo do DeepSeek | `deepseek-v4-flash` |
| `GUNICORN_WORKERS` | Workers do gunicorn | `2` |
| `GUNICORN_TIMEOUT` | Timeout do gunicorn (segundos) | `120` |

---

## Deploy com Docker Compose (Desenvolvimento Local)

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais

# 2. Subir os containers
docker-compose up --build

# 3. Acessar em http://localhost:8000
```

---

## Deploy no Easypanel (Produção)

### Pré-requisitos

- Projeto no Easypanel com serviço do tipo `app`
- Repositório GitHub conectado
- Dockerfile na raiz do repositório

### Configuração do Serviço

1. **Criar serviço** `agenda-med` no projeto desejado
2. **Fonte**: GitHub → `elvertoni/agenda-med`, branch `main`, build via Dockerfile
3. **Domínio**: Adicionar domínio customizado (ex: `agendamed.tonicoimbra.com`) com HTTPS
4. **Porta**: `8000` (TCP)
5. **Variáveis de ambiente**: Configurar todas as variáveis obrigatórias listadas acima
6. **Volume**: Bind mount `/var/lib/agenda-med/data` → `/app/data` para persistir o SQLite
7. **DATABASE_PATH**: Definir como `/app/data/db.sqlite3`

### O Entrypoint Automático

O `entrypoint.sh` executa automaticamente a cada deploy:
1. `python manage.py migrate --noinput` — aplica migrações pendentes
2. `python manage.py collectstatic --noinput` — coleta arquivos estáticos
3. Inicia o gunicorn na porta 8000

---

## Integração com Evolution API

### Visão Geral

A Evolution API é usada para:
- **Envio de mensagens**: OTP, confirmação de presença, chatbot
- **Recebimento de mensagens**: Webhook para chatbot WhatsApp

### Configurar Webhook na Evolution API

O webhook deve ser configurado na instância WhatsApp para enviar mensagens recebidas ao chatbot:

```bash
curl -X POST "https://evoapi.tonicoimbra.com/webhook/set/CLINICA" \
  -H "apikey: SUA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "enabled": true,
      "url": "https://agendamed.tonicoimbra.com/messaging/webhook/whatsapp/",
      "webhookByEvents": false,
      "webhookBase64": false,
      "events": [
        "MESSAGES_UPSERT"
      ]
    }
  }'
```

### Endpoints do Sistema

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/messaging/webhook/whatsapp/` | POST | Webhook para receber mensagens WhatsApp |
| `/messaging/otp/` | GET/POST | Solicitar código OTP por WhatsApp |
| `/messaging/otp/verificar/` | GET/POST | Verificar código OTP |

### Funcionalidades do Chatbot

O chatbot responde automaticamente a mensagens recebidas via WhatsApp:

- **Preços**: Consulta tabela de preços da clínica
- **Protocolos**: Instruções de preparo para exames
- **Horários**: Agenda disponível de profissionais
- **Agendamento**: Fluxo completo de marcação de consulta
- **IA (DeepSeek)**: Respostas inteligentes quando a API key está configurada

---

## Comandos de Gerenciamento

```bash
# Enviar confirmações de presença pendentes (24h antes da consulta)
python manage.py send_presence_confirmations

# Criar superusuário
python manage.py createsuperuser
```

---

## Estrutura de Arquivos Relevante

```
clinica-agenda/
├── Dockerfile              # Imagem de produção
├── entrypoint.sh           # Script de inicialização (migrate + gunicorn)
├── docker-compose.yml      # Desenvolvimento local
├── .env.example            # Template de variáveis de ambiente
├── config/
│   ├── settings.py         # Configurações Django
│   ├── urls.py             # URLs raiz
│   └── wsgi.py             # WSGI application
├── messaging/
│   ├── whatsapp.py         # Gateway Evolution API
│   ├── chatbot.py          # Lógica do chatbot WhatsApp
│   ├── views.py            # Webhook + OTP views
│   └── services.py         # OTP + confirmação de presença
└── docs/
    └── deploy.md           # Este documento
```
