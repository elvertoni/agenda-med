# Design system

Resumo operacional. Especificação canônica (com todos os blocos HTML de referência): [PRD §9](../PRD.md#9-design-system).

## Princípios

- **Identidade única** aplicada a todas as telas. Mesma paleta, mesmos componentes, mesma marcação.
- **Tema escuro** com gradientes harmônicos.
- **Mobile-first responsivo**.
- Estilização **exclusivamente via classes Tailwind** em templates DTL — sem CSS solto, sem `<style>` inline.
- Componentes reutilizáveis vivem em **`core/templates/components/`**.

## Paleta (tokens Tailwind)

| Uso | Classe |
|---|---|
| Fundo principal | `bg-slate-950` |
| Superfície (cards, painéis) | `bg-slate-900` |
| Borda sutil | `border-slate-800` |
| Texto primário | `text-slate-100` |
| Texto secundário | `text-slate-400` |
| Acento primário | `text-emerald-400` / `bg-emerald-500` |
| Acento secundário | `text-sky-400` |
| Gradiente de marca | `bg-gradient-to-br from-emerald-500 via-teal-500 to-sky-600` |
| Erro / validação | `text-rose-400` / `border-rose-500` |

## Tipografia

- Fonte: stack `font-sans` do Tailwind (Inter recomendada via `@font-face`).
- Títulos: `text-2xl md:text-3xl font-semibold tracking-tight text-slate-100`.
- Corpo: `text-base leading-relaxed text-slate-300`.
- Legenda: `text-sm text-slate-400`.

## Layout

- Container padrão: `mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8`.
- Grid de cards: `grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3`.
- Dashboard: `grid grid-cols-1 lg:grid-cols-[16rem_1fr] gap-6` (sidebar + conteúdo).

## Regras de qualidade de UI

- **Foco visível obrigatório** (`focus:ring-2`) em todo elemento interativo.
- **Não duplique markup** de botão, input, card ou nav — extraia para componente em `core/templates/components/`.
- Mensagens do Django (`messages`) renderizadas como banners com `border-l-4` colorida por nível:
  - Sucesso: `border-emerald-500`
  - Erro: `border-rose-500`
  - Info: `border-sky-500`
- Formulários do Django: classes Tailwind injetadas via `widget attrs` ou template tags (não escreva HTML solto para campos de form).

Os snippets HTML completos de botões, inputs, cards e nav estão em [PRD §9](../PRD.md#9-design-system) — copie de lá.
