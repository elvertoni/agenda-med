# Autenticação e acesso

Origem: [PRD §1 — Interpretação de escopo](../PRD.md#interpretação-de-escopo-adotada-decisão-explícita) e [§6 — RF01–RF04](../PRD.md#rf--autenticação-e-acesso).

## Dois caminhos, um único modelo de usuário

O projeto tem **um único `User`** (custom, login por e-mail), mas **dois fluxos de acesso distintos**:

| Quem | Como autentica | Para onde vai |
|---|---|---|
| Equipe da clínica e profissionais | **E-mail + senha** (auth nativo do Django) | Dashboard administrativo |
| Pacientes | **Passwordless via OTP no WhatsApp** | Portal do paciente (consulta) |

O OTP **não substitui** o sistema de auth do Django — ele é um mecanismo de verificação passwordless do paciente sobre o mesmo `User`.

## Fluxo da equipe

1. Login com e-mail e senha em formulário nativo do Django.
2. Mensagens de erro em português, **sem revelar qual campo falhou**.
3. Redirecionamento pós-login para o dashboard administrativo.

## Fluxo do paciente (OTP)

1. Paciente informa o **número de WhatsApp cadastrado**.
2. Sistema envia código OTP por WhatsApp (via app `messaging`).
3. Paciente insere o código.
4. Validação: código válido abre sessão no portal do paciente; inválido retorna erro e contabiliza tentativa.
5. Após N tentativas falhas, acesso é bloqueado temporariamente.

### Regras do código OTP (RF03 / RNF07)

- **Uso único** (`is_used` no `OtpCode`).
- **Expiração curta** (`expires_at`).
- **Limite de tentativas** (`attempts`).
- Proteção contra força bruta no envio e na validação.

## Origem do cadastro do paciente

O cadastro do paciente é **majoritariamente originado pelo fluxo do chatbot no WhatsApp**, não pelo portal web. O portal apenas consulta. Não construa fluxo de cadastro web de paciente sem decisão de produto explícita.

## Diagrama de fluxo

O flowchart completo (canais, agendamento, OTP, confirmação 24h) está em [PRD §6 — Fluxos de UX](../PRD.md#fluxos-de-ux-flowchart).
