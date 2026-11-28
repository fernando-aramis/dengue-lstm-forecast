# Runbook — agendamento do refresh (plano 21, 1.4)

| Camada | O que cobre | Onde |
|---|---|---|
| Heartbeat mensal | GitHub desativa agendamentos após ~60 dias sem atividade | `.github/workflows/heartbeat.yml` (commit em `main` e `data`, `[skip render]`) |
| Issue em falha | Refresh que falha | passo `if: failure()` de `refresh.yml` (issue "Refresh das previsões falhou") |
| Dead man's switch | Falha, atraso **e** workflow desativado | ping ao final de um refresh que **publicou**; secret `HEALTHCHECK_URL` |
| Manual | Qualquer falha | `gh workflow run refresh.yml` (`-f forcar=true` ignora o probe) |

## Configurar o monitor externo (1.4d) — uma vez
1. Criar um check em um serviço de dead man's switch (ex.: healthchecks.io; conferir os limites do plano gratuito) com período de 7 dias e tolerância de ~2 dias (o cron roda seg/qui; o probe pula se nada mudou, então o ping só sai quando há publicação — se a InfoDengue atrasar, o alerta é esperado).
2. Salvar a URL de ping em *Settings → Secrets and variables → Actions* como `HEALTHCHECK_URL`. O ping não leva dados do projeto. Sem o secret, o passo é ignorado.

## Se os agendamentos forem desativados
`gh workflow enable refresh.yml` (e `security.yml`, `heartbeat.yml`); depois `gh workflow run refresh.yml`.

## Primeira publicação (cria a branch `data`)
Após o merge da Fase 1: `gh workflow run refresh.yml -f forcar=true`. O bootstrap cria a branch órfã `data`, semeia `snapshots/` de `main` e publica `runs/AAAASS-<sha7>/` + `latest.json`.
