# Arquitetura

Resumo operacional da arquitetura. Detalhamento completo: [PRD §8](../PRD.md#8-arquitetura-técnica).

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| Framework | Django 5.x (full-stack) |
| Frontend | Django Template Language (DTL) — **sem SPA / sem framework JS** |
| Estilo | TailwindCSS 3.x (via `django-tailwind` ou CLI standalone) |
| Banco | SQLite padrão do Django — **nenhum outro SGBD** |
| Autenticação | `django.contrib.auth` nativo, custom user logando por e-mail |
| E-mail | `django.core.mail` |
| WhatsApp | Provedor externo encapsulado na app `messaging` |
| Servidor (dev) | `runserver` (Docker fica para a Sprint 10) |

## Apps Django

Cada domínio em uma app isolada, com baixo acoplamento.

| App | Responsabilidade | Models principais |
|---|---|---|
| `core` | `TimeStampedModel`, mixins, `base.html`, componentes do design system | `TimeStampedModel` (abstrata) |
| `accounts` | Custom user por e-mail, perfil do paciente | `User`, `PatientProfile` |
| `professionals` | Especialidades e profissionais | `Specialty`, `Professional` |
| `scheduling` | Disponibilidade e consultas | `AvailabilitySlot`, `Appointment` |
| `clinic_content` | Conteúdo cadastrável pela equipe | `PriceItem`, `ServiceProtocol`, `ExamProtocol` |
| `messaging` | OTP, integração WhatsApp, confirmação de presença | `OtpCode`, `PresenceConfirmation` |

## Modelagem de dados

- Todo model concreto **herda de `core.TimeStampedModel`**, garantindo `created_at` e `updated_at` em todas as tabelas.
- O diagrama ER completo (FKs, tipos e cardinalidades) está em [PRD §8 — Estrutura de dados](../PRD.md#estrutura-de-dados-diagrama-er). Use-o como contrato ao escrever models e migrações.
- Campos do cadastro de consulta (mínimos do RF13 + propostos de domínio em RF14) estão em [PRD §8 — Campos do cadastro de consulta](../PRD.md#campos-do-cadastro-de-consulta--conhecimento-de-domínio).

## Integração WhatsApp

A app `messaging` é a única fronteira com o provedor externo de WhatsApp. Mantenha a interface trocável — o provedor concreto pode mudar; o resto do sistema não deve saber qual é.
