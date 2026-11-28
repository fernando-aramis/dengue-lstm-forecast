# 0006 — Desempenho realizado: `avaliar.py`, maturação de 4 semanas e IC de Wilson

**Status:** aceito (2026-11-28; Fase 3 do plano 21, PR #45). Sem dados avaliáveis ainda (ver Consequências).

## Contexto
O painel afirma cobertura nominal de 90% para a banda conformal, mas não mostrava a cobertura **medida** em produção.

## Decisão
1. `pipeline/avaliar.py` (só pandas/numpy, **sem TensorFlow**) compara, para cada (origem, horizonte, município), a
   previsão publicada em `snapshots/` com o observado do `historico.csv` do run novo. Só entra o par cujo alvo
   `T ≤ última_semana − 4` (**atraso de 4 semanas**, para o nowcast consolidar) e que seja posterior à origem
   (sem vazamento).
2. Métricas por horizonte: n, acertos, cobertura, **IC de Wilson 95%**, largura média, MAE do LSTM e do ingênuo
   (em casos e em log1p), MAE mediano por cidade e skill = 1 − MAE/MAE_ingênuo. Abaixo de `n_min = 100`: a UI diz
   "em acumulação (n=…)" e não afirma cobertura.
3. Integração no `refresh.yml`: treino → gate → `avaliar.py` → publicação; **falha da avaliação não bloqueia** a
   publicação das previsões (aviso no log). O `desempenho.json` vai no run, com hash, e é exibido a partir do
   artefato mais recente, independente da fonte escolhida, rotulado com a data de geração.
4. **Honestidade:** o IC supõe independência, mas as cidades são correlacionadas (intervalo otimista); o observado é
   o nowcast consolidado, enquanto a origem usava um último valor ainda preliminar — a direção do viés não foi
   medida e o texto **não** afirma favorecer nenhum lado.

## Consequências
Hoje há 0 pares avaliáveis (último dado 2026-11-15; corte 2026-10-18). n ≥ 100 exige ~4 origens maturadas (h=1 em
~8 semanas; h=4 mais). Até lá a UI mostra "em acumulação". Primeiro run do `avaliar.py` no Actions ainda a conferir.
