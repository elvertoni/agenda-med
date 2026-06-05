# Documentação — Agenda Clínica

Índice da documentação do projeto. Esta pasta resume e orienta; **o documento canônico é o [PRD](../PRD.md)**. Em qualquer divergência entre estes arquivos e o PRD, o PRD prevalece.

## Estado do projeto

O repositório contém, hoje, apenas:

- [`PRD.md`](../PRD.md) — Product Requirement Document, v1.0, baseline de desenvolvimento.
- [`inicial/`](../inicial/) — prompt original e prompt refinado que geraram o PRD.
- [`CLAUDE.md`](../CLAUDE.md) — orientação para o agente Claude Code.

Ainda **não há código Django implementado**. A documentação abaixo descreve os guidelines e padrões que valerão assim que a Sprint 1 começar.

## Conteúdo

| Arquivo | O que cobre |
|---|---|
| [`arquitetura.md`](arquitetura.md) | Stack, separação em apps Django, modelagem de dados |
| [`padroes-codigo.md`](padroes-codigo.md) | PEP 8, aspas simples, idioma do código vs interface, CBVs, signals, `TimeStampedModel` |
| [`design-system.md`](design-system.md) | Paleta, componentes Tailwind, regras de UI |
| [`autenticacao-e-acesso.md`](autenticacao-e-acesso.md) | Login da equipe (e-mail + senha) e acesso passwordless do paciente (OTP) |
| [`fluxo-de-trabalho.md`](fluxo-de-trabalho.md) | Princípio do enxuto e ordem das sprints |

## Como usar esta documentação

- Antes de codar uma funcionalidade, leia a seção correspondente no PRD e o arquivo desta pasta que cobre o assunto.
- Cada arquivo aponta para a seção exata do PRD com o detalhamento completo (tabelas, diagramas Mermaid, critérios de aceite).
- Se algo no PRD mudar, atualize **o PRD primeiro** e só depois reflita aqui.
