# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado atual

O repositório ainda **não contém código**. Há apenas dois artefatos de planejamento:

- `PRD_agendamento_clinica.md` — PRD canônico (v1.0, baseline para desenvolvimento). É a **fonte única de verdade** para escopo, modelagem, design system e ordem de implementação por sprint.
- `inicial/prompt-prd-clinica.md` e `inicial/prompt_inicial.txt` — prompt original e versão refinada que geraram o PRD. Restrições do prompt foram absorvidas pelo PRD; em conflito, **o PRD prevalece**.

Antes de codar, abra o PRD e use a Sprint correspondente (seção 13) como roteiro. Sprints 1–8 entregam funcionalidade; **Sprint 9 (testes) e Sprint 10 (Docker) só ao final** — não antecipe nenhuma das duas.

## Stack obrigatória (não substitua)

- Python 3.12+ / Django 5.x full-stack, **sem SPA / sem framework JS de frontend**.
- Frontend em **Django Template Language (DTL)** estilizado com **TailwindCSS 3.x** (via `django-tailwind` ou CLI standalone).
- **SQLite** padrão do Django — nenhum outro SGBD.
- Autenticação **nativa do Django** (`django.contrib.auth`) com **custom user logando por e-mail** (sem `username`).
- Integração WhatsApp encapsulada na app `messaging` (interface trocável; provedor a definir).

## Regras de código inegociáveis

- **PEP 8** + **aspas simples sempre que possível**.
- **Código em inglês** (nomes, variáveis, comentários técnicos). **Interface em português brasileiro** — toda string visível ao usuário.
- **Class Based Views por padrão**; recursos nativos do Django antes de bibliotecas externas.
- **Todo model concreto herda de `core.TimeStampedModel`** (abstrata com `created_at`/`updated_at`). Não duplicar esses campos em subclasses.
- **Signals**, quando usados, ficam em `signals.py` **dentro da app correspondente** (ex.: agendamento da confirmação 24h vive em `scheduling/signals.py`).
- **Princípio do enxuto**: não implementar nada fora do escrito no PRD. Em ambiguidade, escolher a interpretação mais simples.

## Arquitetura por apps (domínios isolados)

| App | Responsabilidade | Models |
|---|---|---|
| `core` | `TimeStampedModel`, mixins, `base.html`, componentes do design system | `TimeStampedModel` (abstrata) |
| `accounts` | Custom user por e-mail, perfil do paciente, papéis | `User`, `PatientProfile` |
| `professionals` | Especialidades e profissionais | `Specialty`, `Professional` |
| `scheduling` | Disponibilidade e consultas | `AvailabilitySlot`, `Appointment` |
| `clinic_content` | Conteúdo cadastrável (preços, protocolos) | `PriceItem`, `ServiceProtocol`, `ExamProtocol` |
| `messaging` | OTP, integração WhatsApp, confirmação de presença | `OtpCode`, `PresenceConfirmation` |

O ER completo (FKs e campos) está na seção 8 do PRD; use-o como contrato ao gerar models e migrações.

## Decisão de produto que muda código

O PRD resolve a tensão entre "login por e-mail" e "OTP no WhatsApp" assim:

- **Equipe e profissionais** → e-mail + senha → **dashboard administrativo**.
- **Pacientes** → passwordless via **OTP no WhatsApp** → **portal do paciente** (só consulta).

Cadastro de paciente é majoritariamente originado pelo chatbot, não pelo portal. Não construa fluxo de cadastro web de paciente sem confirmação explícita do usuário.

## Design system (resumo operacional)

Tema **escuro com gradientes** — paleta definida em tokens na seção 9 do PRD. Pontos que recorrem em revisões:

- Fundo: `bg-slate-950` (página) / `bg-slate-900` (superfície). Acento primário: `emerald-500/400`. Gradiente de marca: `from-emerald-500 via-teal-500 to-sky-600`.
- Componentes reutilizáveis vivem em `core/templates/components/`. Não duplique markup de botão/input/card — extraia para componente.
- Foco visível obrigatório (`focus:ring-2`) em todo elemento interativo.
- Mensagens do Django renderizadas como banners com `border-l-4` colorida por nível.

## Comandos

Ambiente virtual em `.venv/`. No Windows use `.venv/Scripts/python`; em POSIX use `.venv/bin/python`.

- **Setup inicial**: `python -m venv .venv && .venv/Scripts/python -m pip install -e .[dev]`
- **Dev server**: `.venv/Scripts/python manage.py runserver`
- **Migrações**: `.venv/Scripts/python manage.py makemigrations` / `migrate`
- **Lint**: `.venv/Scripts/ruff check .` (auto-fix: `--fix`)
- **Tailwind (one-shot)**: `./tailwindcss.exe -i ./static/css/input.css -o ./static/css/output.css`
- **Tailwind (watch)**: acrescente `--watch` ao comando acima

O binário `tailwindcss.exe` é o CLI standalone (v3.4) — não está versionado. Baixe de [tailwindlabs/tailwindcss releases](https://github.com/tailwindlabs/tailwindcss/releases) na primeira clonagem.

Testes virão na Sprint 9; o comando será `.venv/Scripts/python manage.py test`.
