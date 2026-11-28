# 0004 — gitleaks-action 3.x e imagem base `python:3.11-slim` por digest

**Status:** aceito (2026-11-27; tarefas 0.6 e 0.7 do plano 21).

## Contexto
`gitleaks/gitleaks-action` 2.3.9 rodava em Node antigo; a imagem base era referenciada por tag móvel.

## Decisão
1. `gitleaks-action` **v3.0.0**, fixado por SHA (mudança só de runtime Node 24; sem alteração de contrato;
   gratuito para repositório público/conta pessoal).
2. `python:3.11-slim` **fixado por digest** no `Dockerfile`; o Dependabot (docker) propõe a troca. Efeito
   medido na PR #22: imagem 905 → 869 MB, `/health` 1,6 → 1,4 s, RSS 207 → 187 MiB; hadolint e trivy sem
   achados novos. A Q.7 reduziu depois para ~513 MB (−21%).
3. Todas as Actions seguem fixadas por SHA com comentário da versão.

## Consequências
Builds reprodutíveis e auditáveis; custo: revisar PRs do Dependabot para base e Actions.
