# 0003 — Heartbeat, monitor externo e proteção da `main`

**Status:** aceito em parte (2026-11-28): heartbeat feito; monitor externo e ruleset adiados.

## Contexto
Sem o commit semanal do refresh em `main`, o GitHub pode desativar agendamentos de repositórios públicos
após ~60 dias sem atividade (`refresh`, `security`). Além disso, falhas silenciosas (workflow desativado,
atraso da InfoDengue) não geram alerta por si.

## Decisão
1. **Heartbeat mensal** (`heartbeat.yml`): commit em `.github/heartbeat` na `main` e em `heartbeat` na `data`,
   com `[skip render]` (sem deploy). Commits do `GITHUB_TOKEN` não disparam outros workflows.
2. **Alerta de falha:** o `refresh.yml` abre/atualiza uma issue em falha; o push na `data` que falha 3 vezes
   derruba o job (PR de revisão independente).
3. **Monitor externo (dead man's switch): adiado.** O passo de ping existe e é ignorado sem o secret
   `HEALTHCHECK_URL`. Justificativa do autor: o app já faz **fallback** para o original quando a atualização
   falha ou fica defasada (`atual.py`: estados `defasado`/`indisponivel`), então a falha não degrada o usuário.
   Reavaliar se o dado atual virar o padrão. Runbook: `docs/operacao/agendamento.md`.
4. **Ruleset da `main` (Q.2): ativo desde 2026-11-28 em versão reduzida** (`protecao-main`, id 28279952): bloqueia
   **deleção** e **force-push**; administrador do repositório pode contornar. A versão completa (PR obrigatória +
   checks) foi **recusada pela API**: em repositório pessoal o app *GitHub Actions* não pode ser *bypass actor*
   (`Actor GitHub Actions integration must be part of the ruleset source or owner organization`), e o heartbeat
   precisa commitar direto em `main`. Alternativas descartadas por ora: PR obrigatória com heartbeat só na `data`
   (não é documentado se push em `data` conta como atividade) ou heartbeat com PAT do administrador (exige um
   secret de longa duração). Reavaliar se o repositório migrar para uma organização.

## Consequências
Agendamentos permanecem ativos sem commit semanal; a ausência do monitor externo é um risco consciente
(detecção só por e-mail do GitHub e issue).
