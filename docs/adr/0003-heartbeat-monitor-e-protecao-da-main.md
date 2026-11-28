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
4. **Ruleset da `main` (Q.2): pendente de confirmação.** Quando ativado (exigir PR e checks, bloquear
   force-push), o `github-actions[bot]` precisa de *bypass* para o heartbeat, e o commit de arquivos de dados
   opcionais em `main` (1.4c) passa a exigir PR.

## Consequências
Agendamentos permanecem ativos sem commit semanal; a ausência do monitor externo é um risco consciente
(detecção só por e-mail do GitHub e issue).
