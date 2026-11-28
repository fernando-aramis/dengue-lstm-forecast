# 0001 — Dados atuais via artefato publicado (branch `data`)

**Status:** aceito (2026-11-27) · **Contexto do plano:** `21-plano-de-desenvolvimento-dados-atuais.md`, Fase 1.

## Contexto
O app só **lê** CSVs (regra "Opção 1": nada de treino nem API no caminho de serving). Até aqui o refresh
semanal commitava os CSVs em `main`, o que redeployava o Render a cada execução e deixava a `main`
sujeita a CI vermelho sem aviso (o push do `GITHUB_TOKEN` não dispara workflows).

## Decisão
1. O refresh (`refresh.yml`) treina no CI (Py 3.12 + TF 2.18) e publica na branch **`data`**, nunca em `main`:
   `runs/AAAASS-<sha7>/…` (imutável) e, **por último**, `latest.json` com o SHA-256 de cada arquivo.
2. O app (`atual.py`) busca `latest.json` e depois os arquivos do run, **server-side**, em thread daemon por
   worker, e expõe o resultado como um `Conjunto` imutável. O dataset de `main` continua sendo o **original**
   e o fallback: o app nunca depende da rede para subir.
3. O usuário escolhe **Original** ou **Atual** (`?fonte=`); o estado (`carregando|disponivel|defasado|indisponivel`)
   é sempre explicado em texto.
4. Um *probe* barato (SE mais recente de Curitiba × `se_origem` publicada) evita treinar quando nada mudou.

## Consequências
- Sem redeploy a cada refresh; `main` só muda por PR com CI verde.
- **CSP sem mudança:** o fetch é server-side, então `connect-src 'self'` do navegador não se aplica.
- Superfície nova de rede (SSRF): host em allowlist (`raw.githubusercontent.com`), sem redirecionamentos,
  timeout 5 s, teto de 2 MB por arquivo, hash conferido; HTTP em loopback só com `DADOS_ATUAIS_TESTE=1`.
- Estado em memória **por worker** (o `render.yaml` fixa `WEB_CONCURRENCY=1`); `--max-requests` recicla o
  worker e refaz a busca (mitigado por ETag). **Sem `--preload`** (threads não sobrevivem ao fork).
- Kill-switch: `DADOS_ATUAIS=0` (mudar env no Render reinicia o serviço; não é instantâneo).
- Risco aberto: com a `main` sem commit semanal, agendamentos podem ser desativados por inatividade → heartbeat
  e monitor externo (ADR 0003, tarefas 1.4/1.4d).
