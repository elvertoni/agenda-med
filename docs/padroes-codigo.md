# Padrões de código

Regras inegociáveis. Origem: [PRD §7](../PRD.md#7-requisitos-não-funcionais) (RNF02, RNF09, RNF10) e [§8](../PRD.md#8-arquitetura-técnica).

## Linguagem do código vs linguagem da interface

- **Código em inglês**: nomes de variáveis, funções, classes, módulos, arquivos e comentários técnicos.
- **Interface em português brasileiro**: toda string visível ao usuário (labels, mensagens, erros de validação, e-mails, mensagens do WhatsApp).

## Estilo

- **PEP 8** em todo o código Python.
- **Aspas simples** sempre que possível. Use aspas duplas apenas quando a string contiver aspas simples.

## Padrões do Django

- **Class Based Views por padrão.** Use FBV apenas quando a CBV adicionar mais ruído que valor.
- **Recursos nativos primeiro.** Antes de adicionar uma biblioteca externa, verifique se o Django já resolve.
- **`AUTH_USER_MODEL` customizado** logando por e-mail (sem `username`), em `accounts`.
- **Signals**, quando usados, ficam em `signals.py` **dentro da app que dispara o evento**. Exemplo: o agendamento da confirmação 24h ao criar uma consulta vive em `scheduling/signals.py`.

## Models

- **Todo model concreto herda de `core.TimeStampedModel`** (abstrata com `created_at` e `updated_at`). Não redeclare esses campos.
- Use flags `is_active` para conteúdo curado (profissionais, preços, protocolos) — itens inativos não aparecem ao paciente.
- Idade do paciente é **derivada** de `birth_date`, nunca armazenada solta.

## Reserva de slot

Reserva de `AvailabilitySlot` deve ser **transacional** para evitar duplo agendamento no mesmo horário (mitigação do risco R4 em [PRD §12](../PRD.md#12-riscos-e-mitigações)).

## Segurança do OTP

Código de uso único, expiração curta, limite de tentativas, bloqueio temporário após N falhas. Detalhamento em RF03 / RNF07 do PRD.
