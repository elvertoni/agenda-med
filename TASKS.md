a# TASKS — Agenda Clínica

Checklist de execução das sprints. Extraído de [`PRD.md` §13](PRD.md#13-lista-de-tarefas). Esta é a lista operacional; em divergência, o PRD prevalece.

> Docker e testes aparecem apenas nas sprints finais (9 e 10).

## Sprint 1 — Fundação do projeto e `core` [x]
- [x] 1.1 Criar projeto Django e estrutura de pastas
  - [x] 1.1.1 Inicializar projeto e `settings` (idioma `pt-br`, timezone, `LANGUAGE_CODE`)
  - [x] 1.1.2 Configurar SQLite padrão
  - [x] 1.1.3 Configurar PEP 8 / linter e convenção de aspas simples
- [x] 1.2 Configurar TailwindCSS
  - [x] 1.2.1 Integrar Tailwind (django-tailwind ou CLI standalone)
  - [x] 1.2.2 Configurar build de CSS e `static`
  - [x] 1.2.3 Definir tokens do design system no `tailwind.config`
- [x] 1.3 Criar app `core`
  - [x] 1.3.1 Implementar `TimeStampedModel` abstrata (`created_at`, `updated_at`)
  - [x] 1.3.2 Criar `base.html` com nav, footer e tema escuro
  - [x] 1.3.3 Criar componentes de UI (botões, inputs, cards, alerts) em `components/`

## Sprint 2 — Contas e autenticação (`accounts`) [x]
- [x] 2.1 Custom user por e-mail
  - [x] 2.1.1 Implementar `User` (AbstractBaseUser/Manager) com `email` como `USERNAME_FIELD`
  - [x] 2.1.2 Remover `username`; herdar de `TimeStampedModel`
  - [x] 2.1.3 Configurar `AUTH_USER_MODEL` e migrar
- [x] 2.2 Autenticação da equipe (e-mail + senha)
  - [x] 2.2.1 LoginView/LogoutView nativas com template estilizado
  - [x] 2.2.2 Forms de login com validação em português
  - [x] 2.2.3 Redirecionamento pós-login ao dashboard administrativo
- [x] 2.3 Modelo de paciente
  - [x] 2.3.1 Implementar `PatientProfile` com campos RF13/RF14
  - [x] 2.3.2 Migrar e registrar no admin

## Sprint 3 — Profissionais e conteúdo (`professionals`, `clinic_content`) [x]
- [x] 3.1 App `professionals`
  - [x] 3.1.1 Models `Specialty` e `Professional` (com `TimeStampedModel`)
  - [x] 3.1.2 CRUD via Class Based Views (List/Create/Update/Delete)
  - [x] 3.1.3 Templates DTL no design system
- [x] 3.2 App `clinic_content`
  - [x] 3.2.1 Models `PriceItem`, `ServiceProtocol`, `ExamProtocol`
  - [x] 3.2.2 CRUD via CBVs para a equipe
  - [x] 3.2.3 Páginas públicas de exibição (preços/protocolos) em pt-BR

## Sprint 4 — Site público e dashboards [x]
- [x] 4.1 Site de apresentação
  - [x] 4.1.1 Landing com apresentação, Cadastre-se e Login
  - [x] 4.1.2 Seções de profissionais e informações públicas
- [x] 4.2 Dashboard administrativo (equipe)
  - [x] 4.2.1 Layout sidebar + conteúdo (grid do design system)
  - [x] 4.2.2 Visões de consultas, profissionais e conteúdo
- [x] 4.3 Portal do paciente (estrutura)
  - [x] 4.3.1 Layout do portal e navegação restrita

## Sprint 5 — Agendamento (`scheduling`) [x]
- [x] 5.1 Disponibilidade
  - [x] 5.1.1 Model `AvailabilitySlot` (status, FK profissional)
  - [x] 5.1.2 CBVs para gestão de disponibilidade pela equipe
- [x] 5.2 Consultas
  - [x] 5.2.1 Model `Appointment` (FKs, status, motivo, plano usado)
  - [x] 5.2.2 Fluxo de reserva transacional do slot
  - [x] 5.2.3 Derivação de idade a partir da data de nascimento
- [x] 5.3 Consulta no portal do paciente
  - [x] 5.3.1 Listagem das consultas do paciente
  - [x] 5.3.2 Visão de disponibilidade e profissionais

## Sprint 6 — Acesso por OTP (`messaging` — parte 1) [x]
- [x] 6.1 Estrutura do OTP
  - [x] 6.1.1 Model `OtpCode` (código, expiração, uso único, tentativas)
  - [x] 6.1.2 Serviço de geração/validação de código
- [x] 6.2 Fluxo de acesso passwordless
  - [x] 6.2.1 Tela: informar número de WhatsApp
  - [x] 6.2.2 Envio do código via integração de WhatsApp
  - [x] 6.2.3 Tela: inserir código + validação e bloqueio por tentativas
  - [x] 6.2.4 Sessão do paciente após validação

## Sprint 7 — Confirmação de presença (`messaging` — parte 2) [x]
- [x] 7.1 Modelagem
  - [x] 7.1.1 Model `PresenceConfirmation` (canal, envio, resposta, status)
- [x] 7.2 Disparo 24h antes
  - [x] 7.2.1 `signals.py` em `scheduling` para agendar a confirmação na criação da consulta
  - [x] 7.2.2 Rotina de disparo ~24h antes (comando de gestão)
  - [x] 7.2.3 Envio por WhatsApp e/ou e-mail
- [x] 7.3 Resposta e atualização
  - [x] 7.3.1 Registro de resposta (confirmado/não confirmado/sem resposta)
  - [x] 7.3.2 Atualização do status da consulta
  - [x] 7.3.3 Indicação no dashboard administrativo

## Sprint 8 — Chatbot WhatsApp (integração) [x]
- [x] 8.1 Camada de integração na app `messaging`
  - [x] 8.1.1 Webhook de entrada e roteamento de intenções
  - [x] 8.1.2 Consulta de preços e protocolos (conteúdo)
  - [x] 8.1.3 Consulta de agendas e oferta de horários
  - [x] 8.1.4 Registro de agendamento a partir da conversa

## Sprint 9 (final) — Testes [x]
- [x] 9.1 Testes unitários por app (`accounts`, `professionals`, `scheduling`, `clinic_content`, `messaging`)
- [x] 9.2 Testes de fluxo (OTP, agendamento, confirmação)
- [x] 9.3 Cobertura mínima e ajustes

## Sprint 10 (final) — Containerização
- [x] 10.1 `Dockerfile` da aplicação
- [x] 10.2 `docker-compose` para ambiente local
- [ ] 10.3 Documentação de execução e variáveis de ambiente
