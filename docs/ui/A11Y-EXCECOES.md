# Exceções de acessibilidade (axe-core) — marcação interna do Dash 4.5

**Escopo:** só estados **abertos** (menu de acessibilidade e `dcc.Dropdown`). Estados fechados: **0 violações**
com `wcag2a/aa/aaa`, `wcag21a/aa`, `wcag22aa` e `best-practice` (`tests/test_a11y_axe.py`).

| Regra axe | Onde | Por quê não corrigimos | Mitigação nossa |
|---|---|---|---|
| `aria-allowed-role` (≤40) | `<label role="option">` no `dcc.Checklist` e opções do `dcc.Dropdown` | Marcação gerada pelo Dash 4.5; trocar o papel quebraria o teclado do componente | Foco/teclado verificados (setas, Enter, Esc); rótulos visíveis e acessíveis |
| `nested-interactive` (≤40) | opção contém `<input>`/botão (checkbox, remover) | Idem | Alvos de 44px; estados anunciados pelo próprio `aria-selected`/`checked` |
| `aria-dialog-name` (≤2) | popover (Radix) do dropdown sem nome | Elemento criado em runtime pela biblioteca | O gatilho tem `aria-labelledby`; o popover só existe enquanto aberto |
| `aria-input-field-name` (≤3) | listbox/`#a11y-opts` sem nome | Props de ARIA não são expostas pelo `dcc.Checklist`/`Dropdown` | O grupo é introduzido por `#a11y-pop-title` visível |

**Regra do teste:** o conjunto é **fechado** — regra nova, ou ocorrências acima do teto, falha
`test_axe_menus_abertos_so_tem_as_excecoes_do_dash`. Ao atualizar o Dash, reavalie: se o upstream corrigir, **reduza o teto/remova a linha**.
O axe vendorizado (`tests/vendor/axe.min.js`, v4.10.2, MPL-2.0) é só de teste; não entra na imagem (`.dockerignore` exclui `tests/`).
