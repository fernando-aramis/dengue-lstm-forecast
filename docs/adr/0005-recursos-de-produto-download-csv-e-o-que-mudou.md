# 0005 — Download de CSV por rota Flask e "o que mudou desde a última previsão"

**Status:** aceito (2026-11-28; tarefas P.2 e P.3 do plano 21, PR #45). Verificado em produção em 2026-11-28.

## Contexto
A Fase 2B pede dois recursos que reaproveitam o `Conjunto` e o seletor Original/Atual: baixar as previsões de uma
cidade e comparar a previsão atual com a da execução anterior. Ambos devem respeitar a Opção 1 (o serving não treina
nem chama API) e o contrato de `previsoes.csv`/`historico.csv`.

## Decisão
1. **Download (P.2):** rota `GET /dados/<geo_id>.csv?fonte=original|atual`, link comum (sem callback nem JS).
   `geo_id` é validado contra `Conjunto.nome_por_geo` (allowlist em memória; nada vira caminho de arquivo);
   `fonte` fora dos dois valores → 400; `geo_id` desconhecido ou "atual" indisponível → 404. Resposta
   `text/csv; charset=utf-8`, `Content-Disposition: attachment` com nome saneado (`[A-Za-z0-9_-]`), `nosniff`,
   `Cache-Control: public, max-age=300`. Células de texto que começam com `= + - @ TAB CR` recebem `'` (injeção de
   fórmula em planilhas). Colunas = contrato + `fonte` e `se_origem`; números sem passar por `formato.py` (arquivo de máquina).
2. **"O que mudou" (P.3):** o run publicado inclui `previsoes_anterior.csv` (mesmo schema, com hash no `latest.json`),
   copiado pelo `publicar_run.py` do run anterior se sua origem for anterior. A UI compara **só os alvos em comum**
   (origens consecutivas partilham até 3 das 4 semanas-alvo) e diz quantos são. Arquivo ausente ⇒ recurso omitido.

## Consequências
Contrato dos dois CSVs principais intacto; arquivos novos são opcionais (ausência não derruba o app). O download
público e cacheável expõe só dados já públicos na página. Custo: mais um arquivo por run na branch `data`.
Verificação em produção: 200 (original/atual/UF), 400 (`fonte` inválida), 404 (id inexistente), caminho forjado barrado na borda.
