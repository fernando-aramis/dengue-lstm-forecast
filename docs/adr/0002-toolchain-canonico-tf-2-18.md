# 0002 — Toolchain canônico do refresh: Python 3.12 + TensorFlow 2.18

**Status:** aceito (2026-11-28); a comparação com o TF 2.21 (tarefa 0.8) está **pendente** e é opcional.

## Contexto
O treino roda no GitHub Actions. O TensorFlow estável exige `numpy < 2.1` e Python ≤ 3.12, enquanto o
desenvolvimento local usa Python 3.14 com o RC do TF (`pipeline/requirements.txt`). Pins diferentes entre
dev e CI geram previsões ligeiramente diferentes.

## Decisão
1. O **dado publicado** vem sempre do toolchain do CI: `pipeline/requirements-ci.txt` (Python 3.12,
   `tensorflow-cpu~=2.18.0`, `numpy>=1.26,<2.2`, pandas por faixa). O dev local serve só para smoke.
2. Dependabot **ignora** `tensorflow-cpu`/`tensorflow` em **todos** os diretórios pip e `numpy` em `/pipeline`
   (decisão arquitetural, comentada em `.github/dependabot.yml`); a troca de versão é manual. A faixa do
   `numpy` em `requirements-ci.txt` é protegida também por teste. A **decisão de 2026-11-28 é manter o TF 2.18**
   (o comparativo 0.8 fica adiado até haver motivo: CVE, necessidade de recurso novo).
3. Um teste (`test_requirements_ci_numpy_compativel_com_tf`) trava a faixa do `numpy`: em 2026-11-28 um bump
   do grupo `serving` (via diretório raiz) a mudou e quebrou o primeiro refresh (PR #41).
4. A mudança para o TF 2.21 só ocorre após o comparativo 0.8 (diferença mediana ≤ 1 caso e bandas sem
   alteração material nas 33 cidades), registrado aqui.

## Consequências
Reprodutibilidade do dado publicado (versões em `_meta.json`); custo: atualizar o TF exige decisão e ~30 min
de Actions. Risco aceito: ficar em versão sem novas correções até a 0.8.
