# Fluxo de trabalho

## Princípio do enxuto

Não implemente nada além do escrito no PRD. Em qualquer ambiguidade, escolha a interpretação **mais simples e mais enxuta**. Origem: [PRD §1](../PRD.md#1-visão-geral) e RNF11 em [§7](../PRD.md#7-requisitos-não-funcionais).

Consequências práticas:

- Sem features "preventivas" ou "para o futuro".
- Sem bibliotecas externas quando o Django nativo resolve.
- Sem abstrações antes do terceiro caso de uso.

## Ordem das sprints

A ordem em [PRD §13](../PRD.md#13-lista-de-tarefas) é deliberada — não pule etapas, não antecipe sprints finais.

| Sprint | Entrega | Apps tocadas |
|---|---|---|
| 1 | Fundação (projeto, Tailwind, `core`, `TimeStampedModel`, `base.html`) | `core` |
| 2 | Custom user por e-mail, login da equipe, `PatientProfile` | `accounts` |
| 3 | CRUD de profissionais, especialidades e conteúdo informativo | `professionals`, `clinic_content` |
| 4 | Site público, dashboard administrativo, esqueleto do portal | (templates) |
| 5 | Disponibilidade e consultas, reserva transacional | `scheduling` |
| 6 | Acesso passwordless por OTP | `messaging` |
| 7 | Confirmação de presença 24h antes | `messaging`, signal em `scheduling` |
| 8 | Integração do chatbot WhatsApp | `messaging` |
| **9 (final)** | **Testes** | todas |
| **10 (final)** | **Docker** | infra |

**Testes e Docker são deliberadamente Sprints 9 e 10.** Não os antecipe sem decisão de produto explícita (RNF11).

## Critérios de "pronto" por funcionalidade

Cada user story em [PRD §10](../PRD.md#10-user-stories) tem checklist de critérios de aceite. Antes de marcar uma sprint como concluída, verifique que **todos os critérios** das stories cobertas estão atendidos.

## Atualização da documentação

Quando uma sprint terminar:

1. Atualize o checklist em [PRD §13](../PRD.md#13-lista-de-tarefas).
2. Se algum guideline mudou (ex.: provedor de WhatsApp definido), atualize o arquivo correspondente em `docs/`.
3. Atualize `CLAUDE.md` se a base de comandos do projeto mudou (ex.: surgiu `manage.py`, build do Tailwind, etc.).
