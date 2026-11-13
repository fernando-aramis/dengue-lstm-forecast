# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primários — pesquisadores e banca acadêmica (IAGA04/UTFPR):** avaliam o método e os resultados do estudo de previsão de dengue; chegam para ler o artigo, conferir números/intervalos e citar o trabalho.
- **Primários — público técnico curioso (estudantes, gestores de saúde, jornalistas de dados):** querem a resposta operacional — *onde a dengue deve subir nas próximas semanas* — e consultar uma cidade específica. Escaneiam o painel antes de (ou em vez de) ler o artigo.
- **Situação de uso:** consulta pontual, muitas vezes em celular, em conexão variável; o servidor (Render free) pode levar até ~1 min para acordar na primeira visita.

## Product Purpose

Painel web que **prevê casos semanais de dengue de 1 a 4 semanas à frente** (com banda conformal de 90%) para capitais e principais cidades do Brasil, com fallback estadual. Nasceu de um estudo de **LSTM univariada para Curitiba** (IAGA04 — Especialização em IA Generativa Aplicada, UTFPR) e foi estendido ao mapa nacional. Sucesso = o visitante **lê uma previsão e entende como ela foi obtida**, com proveniência e reprodutibilidade explícitas.

## Positioning

O mecanismo difícil de copiar não é o modelo isolado, é a **combinação de casca de artigo científico (padrão JBCS) com um painel interativo embutido**: a mesma página serve a previsão operacional (mapa + detalhe por cidade) e o artigo numerado que a fundamenta (método, tabelas, referências, "como citar"). O nível de alerta é uma **simplificação de incidência** e é declaradamente **NÃO** o alerta oficial do InfoDengue — honestidade metodológica é parte do posicionamento. Mapa de duas camadas (choropleth teal vs. bolhas verde→vermelho) pensado para não confundir "estado verde" com "tudo sob controle".

## Operating Context

- **Duas superfícies (modos):** topo + Figura 1 = **Operate** (consultar o forecast); artigo §1–5, declarações, referências, "como citar" = **Read** (entender e citar o método).
- **Trilíngue PT/EN/ES** com paridade de chaves; tema claro/escuro/sistema; idioma resolvido por `Accept-Language`.
- **Dados:** InfoDengue + Mosqlimate (histórico/alertas) e IBGE (geocodes), até uma semana epidemiológica (SE) de origem datada; proveniência em `data/_meta.json`, snapshots datados.
- **Deploy:** Docker no Render (free tier, cold start). O app só serve; o treino é offline.

## Capabilities and Constraints

- **O app NÃO treina e NÃO re-prevê.** Só **lê CSVs já calculados** (`data/*.csv`); todo o treino/predição LSTM (TensorFlow) é offline em `pipeline/`. O schema de `data/previsoes.csv`/`historico.csv` é o **contrato** entre pipeline e app.
- **Restrições invioláveis:** WCAG **AAA** nos dois temas; **CSP** (Report-Only) sem origens externas — **fontes auto-hospedadas**; aviso permanente de que **não é alerta oficial** nem base para decisão clínica/saúde pública; `<html lang>` sincronizado com a UI; Tabela 1 como alternativa textual ao mapa.
- **Terminologia:** SE (semana epidemiológica), t+1…t+4 (horizontes), intervalo conforme 90%, nível (verde/amarelo/laranja/vermelho por incidência semanal/100 mil hab.).

## Brand Commitments

- **Nome:** "Dengue · LSTM Forecast". **Autor:** Fernando Aramis Colque (UTFPR), ORCID público.
- **Identidade visual verde-terrosa** derivada dos slides do estudo de Curitiba; **tipografia** Inter + Source Serif 4 + IBM Plex Mono (auto-hospedadas).
- **Casca de artigo científico JBCS** (cabeçalho corrido, legendas de figura/tabela, numeração de seções, declarações, referências, "como citar"), licença **CC BY 4.0**.
- **Voz:** técnica, sóbria, honesta sobre limites (projeto acadêmico, não oficial).

## Evidence on Hand

- ORCID `0009-0005-6153-6647`; DOI Zenodo `10.5281/zenodo.13328231`; `CITATION.cff` servido por rota; metadados `citation_*` + JSON-LD *ScholarlyArticle*.
- Artigo completo na própria página (método, Tabela 1/2, referências com DOIs).

<!-- Notas: documento derivado do código do repositório e do brief de refino (fase 0/1).
     Nenhuma afirmação de cliente, benchmark ou licenciamento inventada. -->
