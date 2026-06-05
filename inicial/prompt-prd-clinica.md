# Prompt — Geração de PRD: Sistema de Agendamento para Clínica Médica

<role>
Você é um Arquiteto de Software Sênior e Product Manager técnico, especialista em Django full-stack, design de produto e documentação de requisitos. Você produz PRDs (Product Requirement Documents) rigorosos, completos e diretamente acionáveis por uma equipe de desenvolvimento. Você NÃO escreve código neste momento — sua ÚNICA entrega é o documento especificado em `<output_format>`.
</role>

<task>
Produza um PRD (Product Requirement Document) completo, em **arquivo Markdown único**, para o projeto descrito em `<project_context>`, seguindo OBRIGATORIAMENTE a estrutura definida em `<output_format>`. Respeite SEM EXCEÇÃO todas as regras de `<mandatory_constraints>`.
</task>

<project_context>
## Produto
Sistema web de agendamento para clínica médica com múltiplos profissionais. O canal primário de atendimento é o WhatsApp, via chatbot, com um site complementar de consulta.

## Funcionalidades centrais
- Chatbot no WhatsApp que consulta uma base de dados e as agendas dos profissionais, interage com o cliente e responde dúvidas.
- O chatbot informa: preços, protocolos de atendimento e protocolos de exames (jejum, abstinência de medicamentos ou alimentos). **Todo esse conteúdo informativo será cadastrado posteriormente pela equipe da clínica** — o sistema deve apenas prover a estrutura para armazená-lo e exibi-lo.
- Site público de apresentação com opções de **Cadastre-se** e **Login**.
- Após login, o usuário é direcionado ao **dashboard principal**.

## Requisito 1 — Consulta via site com verificação por código
O atendimento é primordialmente pelo WhatsApp, mas o cliente também pode acessar o site para verificar disponibilidade de agenda e de profissionais e conferir a consulta que marcou. O acesso é confirmado por código de uso único (OTP): o cliente digita o número de WhatsApp cadastrado, recebe um código nesse número e o insere para concluir o acesso à plataforma.

## Requisito 2 — Dados do cadastro de consulta
No agendamento, devem ser solicitados e registrados, no mínimo: nome completo, idade, sexo, endereço, número de celular, e-mail, plano de saúde, e quaisquer outros campos que você, pelo seu conhecimento de domínio, julgar relevantes para agendamentos médicos (proponha-os explicitamente).

## Requisito 3 — Confirmação de presença
Confirmação de presença com 24 horas de antecedência, a ser respondida pelo paciente via WhatsApp e/ou e-mail.
</project_context>

<mandatory_constraints>
Estas regras são INEGOCIÁVEIS. Trate cada uma como um requisito de aceite do PRD. O PRD que você gerar DEVE refletir e impor todas elas.

## Stack e arquitetura
- DEVE usar Django full-stack. O frontend DEVE ser construído com Django Template Language (DTL) — proibido SPA/framework JS de frontend.
- DEVE usar TailwindCSS para toda a estilização.
- DEVE usar exclusivamente o banco de dados SQLite padrão do Django.
- DEVE separar as entidades/domínios do sistema em **apps Django distintas**, isolando responsabilidades.
- DEVE priorizar Class Based Views, classes, funções e recursos nativos do Django sempre que possível.
- Se usar signals, eles DEVEM residir em um arquivo `signals.py` dentro da app correspondente.

## Autenticação
- DEVE usar o sistema nativo de usuários e autenticação do Django.
- O login DEVE ser feito por **e-mail**, não por username.

## Modelagem de dados
- TODA tabela/model DEVE conter os campos `created_at` e `updated_at`.

## Padrões de código
- O código DEVE seguir a PEP 8.
- O código DEVE usar **aspas simples** sempre que possível.
- O código do projeto (nomes, variáveis, comentários técnicos) DEVE ser em **inglês**.
- Toda informação exibida na interface do usuário DEVE ser em **português brasileiro**.

## Design
- O design DEVE ser moderno, responsivo, com **fundo escuro**, gradientes e paletas harmônicas.
- DEVE existir um **design system único** aplicado a TODAS as telas: mesmos componentes, mesma identidade visual, consistência total.

## Escopo (princípio do enxuto)
- NÃO adicione NADA além do que está solicitado. O projeto DEVE ser simples e enxuto.
- NÃO implemente Docker inicialmente — aloque para as sprints finais.
- NÃO implemente testes inicialmente — aloque para as sprints finais.
</mandatory_constraints>

<output_format>
Entregue **um único arquivo Markdown** com a estrutura enumerada abaixo. Use cabeçalhos Markdown (`#`, `##`, `###`), tabelas onde fizer sentido, e blocos de código com a linguagem correta. NÃO omita nenhuma seção.

1. **Visão geral**
2. **Sobre o produto**
3. **Propósito**
4. **Público-alvo**
5. **Objetivos**
6. **Requisitos funcionais**
   - Inclua um **flowchart Mermaid** (```mermaid```) representando os fluxos de UX (atendimento via WhatsApp, acesso ao site com OTP, agendamento, confirmação de presença).
7. **Requisitos não-funcionais**
8. **Arquitetura técnica**
   - **Stack** (detalhe versões/bibliotecas).
   - **Estrutura de dados** com schemas em **diagrama Mermaid** (```mermaid``` — use `erDiagram`), refletindo a separação em apps e os campos `created_at`/`updated_at` em todos os models.
9. **Design system**
   - Cores primárias e de fundo, padrão de botões, inputs, forms, grids, menus, fontes — TUDO especificado em classes/utilitários **TailwindCSS** aplicados via Django Template Language.
10. **User stories**
    - Organizadas por **Épico**.
    - Cada user story com seus **critérios de aceite**.
11. **Métricas de sucesso**
    - KPIs de produto, de usuário e de negócio.
12. **Riscos e mitigações**
13. **Lista de tarefas**
    - Organizada **em sprints**.
    - Tarefas e subtarefas **enumeradas**, com descrição e detalhamento de escopo e implementação.
    - Em formato de **checklist** com caixas marcáveis (`- [ ]`) para acompanhamento.
    - Quebre em implementações pequenas, específicas e detalhadas — priorize **alta granularidade** (mais tarefas e subtarefas, cada uma bem delimitada).
    - Docker e testes DEVEM aparecer apenas nas sprints finais.
</output_format>

<execution_rules>
- Trabalhe APENAS dentro do escopo descrito. Em caso de dúvida sobre escopo, escolha a interpretação MAIS ENXUTA.
- Onde o conhecimento de domínio for solicitado (ex.: campos adicionais de agendamento médico), proponha de forma explícita e justifique brevemente.
- Garanta consistência total entre as seções: o design system citado nos requisitos DEVE ser o mesmo detalhado na seção 9; os models do diagrama ER DEVEM corresponder às apps descritas na arquitetura.
- Verifique, ao final, que CADA item de `<mandatory_constraints>` está refletido no PRD antes de concluir.
- A saída DEVE ser exclusivamente o arquivo Markdown do PRD. NÃO inclua comentários fora do documento nem explicações sobre como você o construiu.
</execution_rules>
