# Contexto do projeto (webapp) — atualizado em 2026-11-28

Resumo para retomar o trabalho sem reexplorar o código. Detalhes: memória automática do projeto e `project-report/temp/HANDOFF-ui-refino.md`.

## Estado
- Refino de UI/UX em 8 fases concluído na branch `fix/a11y-ui-remediation`; PR #11 aberto (aguarda 1º CI e merge). Não abrir novo PR sem OK explícito.
- Plano 21 (dados atuais + honestidade): Fases 0, Q, 1 e 2 mergeadas. Fase 2B (metodologia, download CSV, "o que mudou"), Fase 3 (`avaliar.py` + Tabela 3 de desempenho realizado) e Fase 4 (README) na branch `feat/produto-2b`. Arquivos opcionais do run: `limite_treino.csv`, `previsoes_anterior.csv`, `desempenho.json` (ausente/divergente = só o recurso some).
- North Star: "O Periódico Vivo". Refino, não redesign (identidade verde-terrosa, casca JBCS, AAA, trilíngue).

## Toolchain dos dados
Toolchain **canônico**: CI (Py 3.12 + TF 2.18, `pipeline/requirements-ci.txt`) gera os dados publicados. Dev local (Py 3.14 + TF rc) é só para teste/smoke; não commitar dados gerados por ele. Proveniência (`_meta.json` v2) grava as versões.

## Gate de qualidade
`pytest tests/ -q` verde + axe 0 nos dois temas (wcag2aaa; esperar ~1 s após trocar o tema). App sem hot-reload (porta 8050); CSS é relido, `.py` só ao reiniciar.

## Armadilhas
- `font-weight:600` em classe mono carrega o Mono 500 e o teste dos 3 woff2 trava.
- Dash não aceita `translate=` em `html.*`: usar `className="notranslate"`.
- `pkill -f "python app.py"` mata o shell (exit 144): rode sozinho e suba o app em outra chamada.

## Decisões fixas
- KPIs: faixa plana, sem sombra; terracota só no excepcional. Mono só no cabeçalho corrido.
