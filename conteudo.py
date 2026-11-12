# -*- coding: utf-8 -*-
"""
Conteúdo editorial do ARTIGO (JBCS) e constantes do estudo — centralizado para trocar sem caçar
strings pelo código. Módulo de DADOS puro (sem importar i18n/dados → evita ciclo). O i18n faz
`T.update(conteudo.T_ARTIGO)` para que o teste de i18n continue cobrindo tudo.

Decisões do autor (ver project-report/19): licença do texto CC BY 4.0; ORCID com link; e-mail NÃO
exibido; "publicado online" nov 2026; traduções EN/ES geradas (revisar); SEM PDF do artigo.
"""

# ---- identidade / licenças / links ----
ORCID = "0009-0005-6153-6647"                     # None esconde o selo
ORCID_URL = f"https://orcid.org/{ORCID}"
LICENCA = "CC BY 4.0"
LINKS = {
    "colab": "https://colab.research.google.com/drive/1Dpb9zB-YI54vHv6-Mkx-bIlFITgOFuH0?usp=sharing",
    "zenodo": "https://doi.org/10.5281/zenodo.13328231",
    "repo": "https://github.com/fernando-aramis/dengue-lstm-forecast",
    "cff": "/CITATION.cff",
}
PUBLIC_URL = "https://dengue-lstm-forecast.onrender.com"

# ---- números do estudo (NÃO vêm dos CSVs) ----
ESTUDO = {"casos_2023": "913", "casos_2024": "15.389", "pico_2016": "7.883",
          "reducao_mae": "14%", "cobertura": "94–98%", "pico_norm": "1,16", "semanas": "749"}

# tabela de resultados (Tabela 2) — (chave_modelo, E1h1, E1h4, E2h1, E2h4, colunas_destaque)
TAB_RES = [
    ("mod_ingenuo", "4,8", "11,0", "72", "184", {3, 4}),
    ("mod_ingenuo_sazonal", "11,9", "11,9", "409", "409", set()),
    ("mod_a", "4,6", "9,5", "150", "274", {1, 2}),
    ("mod_b", "7,8", "10,4", "284", "354", set()),
    ("mod_c", "5,4", "9,5", "183", "306", set()),
]

# referências (autor-data, ordem alfabética). lang = idioma do título (WCAG 3.1.2).
REFERENCIAS = [
    {"slug": "araujo2026", "lang": "en",
     "texto": "Araujo, E. C., Carvalho, L. M., Ganem, F., et al. (2026). Leveraging probabilistic "
              "forecasts for dengue preparedness and control: The 2024 Dengue Forecasting Sprint in "
              "Brazil. Proceedings of the National Academy of Sciences, 123(7):e2508989123.",
     "doi": "10.1073/pnas.2508989123"},
    {"slug": "chen2025", "lang": "en",
     "texto": "Chen, X. and Moraga, P. (2025). Forecasting dengue across Brazil with LSTM neural "
              "networks and SHAP-driven lagged climate and spatial effects. BMC Public Health, 25:973.",
     "doi": "10.1186/s12889-025-22106-7"},
    {"slug": "coelho2024", "lang": "en",
     "texto": "Coelho, F. C., Codeço, C. T., Almeida, I., Carvalho, L. M., Araújo, E. C., Bastos, L., "
              "Vacaro, L. B., and Lana, R. M. (2024). Full dataset for dengue forecasting in Brazil for "
              "Infodengue-Mosqlimate sprint 2024 (v1). Zenodo.",
     "doi": "10.5281/zenodo.13328231"},
    {"slug": "hochreiter1997", "lang": "en",
     "texto": "Hochreiter, S. and Schmidhuber, J. (1997). Long short-term memory. Neural Computation, "
              "9(8):1735–1780.",
     "doi": "10.1162/neco.1997.9.8.1735"},
    {"slug": "mussumeci2020", "lang": "en",
     "texto": "Mussumeci, E. and Coelho, F. C. (2020). Machine-learning forecasting for dengue "
              "epidemics: comparing LSTM, random forest and lasso regression. medRxiv.",
     "doi": "10.1101/2020.01.23.20018556"},
]

# declarações (texto literal do PDF) — PT; EN/ES nos T_ARTIGO abaixo
BIBTEX = (
    "@misc{colque2026dengue,\n"
    "  author       = {Colque, Fernando Aramis},\n"
    "  title        = {Previsão semanal de casos de dengue em Curitiba com redes LSTM:\n"
    "                  casos, clima e intervalos de previsão},\n"
    "  year         = {2026},\n"
    "  note         = {IAGA04 -- Aprendizado Profundo, Especialização em IA Generativa Aplicada, UTFPR},\n"
    f"  howpublished = {{\\url{{{PUBLIC_URL}/}}}}\n"
    "}"
)


def abnt(data_hoje):
    """ABNT com a data de acesso gerada no servidor (formato 12 nov. 2026)."""
    return (f"COLQUE, Fernando Aramis. Previsão semanal de casos de dengue em Curitiba com redes LSTM: "
            f"casos, clima e intervalos de previsão. Trabalho de disciplina (IAGA04 – Aprendizado "
            f"Profundo) – Especialização em Inteligência Artificial Generativa Aplicada, Universidade "
            f"Tecnológica Federal do Paraná, 2026. Disponível em: {PUBLIC_URL}/. Acesso em: {data_hoje}.")


# ---- textos i18n do artigo (entram em i18n.T via T.update) ----
T_ARTIGO = {
    "artigo_titulo": {"pt": "Previsão semanal de casos de dengue em Curitiba com redes LSTM: "
                            "casos, clima e intervalos de previsão", "en": None, "es": None},
    "artigo_cab_disc": {"pt": "IAGA04 – Aprendizado Profundo · Especialização em IA Generativa "
                              "Aplicada · UTFPR, 2026",
                        "en": "IAGA04 – Deep Learning · Graduate Certificate in Applied Generative AI "
                              "· UTFPR, 2026",
                        "es": "IAGA04 – Aprendizaje Profundo · Especialización en IA Generativa "
                              "Aplicada · UTFPR, 2026"},
    "artigo_cab_lic": {"pt": "Texto sob licença CC BY 4.0 · Código sob GPL-3.0",
                       "en": "Text under CC BY 4.0 · Code under GPL-3.0",
                       "es": "Texto bajo licencia CC BY 4.0 · Código bajo GPL-3.0"},
    "artigo_meta": {"pt": "Disciplina: IAGA04 – Aprendizado Profundo • Entrega: 21 out 2026 • "
                          "Publicado online: nov 2026",
                    "en": "Course: IAGA04 – Deep Learning • Submitted: 21 Oct 2026 • "
                          "Published online: Nov 2026",
                    "es": "Asignatura: IAGA04 – Aprendizaje Profundo • Entrega: 21 oct 2026 • "
                          "Publicado en línea: nov 2026"},
    "artigo_nota_idioma": {"pt": "", "en": "Original article in Portuguese.",
                           "es": "Artículo original en portugués."},
    "resumo_rotulo": {"pt": "Resumo.", "en": "Abstract.", "es": "Resumen."},
    "resumo_texto": {
        "pt": "A epidemia de dengue de 2024 levou Curitiba de 913 casos prováveis em 2023 a mais de "
              "15 mil no primeiro semestre de 2024. Este trabalho avalia redes Long Short-Term Memory "
              "(LSTM) para prever, de uma a quatro semanas à frente, os casos prováveis semanais no "
              "município. Foram comparadas três versões da rede — só casos (A), casos e clima com "
              "sazonalidade (B) e casos com sazonalidade (C) — além de previsões ingênuas, nas "
              "temporadas de teste 2022/23 e 2023/24. Em 2022/23, a LSTM univariada reduziu o erro "
              "absoluto médio em 14% a quatro semanas e teve intervalos de 90% bem calibrados "
              "(cobertura de 94% a 98%). As variáveis climáticas pioraram o desempenho. Na epidemia "
              "de 2023/24, cujo pico foi quase três vezes o maior valor do treino, todas as redes "
              "subestimaram a magnitude. A LSTM é útil no curto prazo dentro da faixa histórica, mas "
              "não substitui o julgamento epidemiológico em eventos extremos.",
        "en": "The 2024 dengue epidemic took Curitiba from 913 probable cases in 2023 to over 15,000 "
              "in the first half of 2024. This work evaluates Long Short-Term Memory (LSTM) networks to "
              "forecast weekly probable cases one to four weeks ahead. Three network versions were "
              "compared — cases only (A), cases and climate with seasonality (B) and cases with "
              "seasonality (C) — plus naïve forecasts, over the 2022/23 and 2023/24 test seasons. In "
              "2022/23 the univariate LSTM cut the mean absolute error by 14% at four weeks and had "
              "well-calibrated 90% intervals (94–98% coverage). Climate variables worsened performance. "
              "In the 2023/24 epidemic, whose peak was nearly three times the training maximum, all "
              "networks underestimated the magnitude. The LSTM is useful short-term within the "
              "historical range but does not replace epidemiological judgement in extreme events.",
        "es": "La epidemia de dengue de 2024 llevó a Curitiba de 913 casos probables en 2023 a más de "
              "15 mil en el primer semestre de 2024. Este trabajo evalúa redes Long Short-Term Memory "
              "(LSTM) para pronosticar, de una a cuatro semanas, los casos probables semanales. Se "
              "compararon tres versiones — solo casos (A), casos y clima con estacionalidad (B) y casos "
              "con estacionalidad (C) — además de pronósticos ingenuos, en las temporadas 2022/23 y "
              "2023/24. En 2022/23 la LSTM univariada redujo el error absoluto medio en 14% a cuatro "
              "semanas, con intervalos del 90% bien calibrados (cobertura 94–98%). Las variables "
              "climáticas empeoraron el desempeño. En la epidemia de 2023/24, cuyo pico fue casi tres "
              "veces el máximo de entrenamiento, todas las redes subestimaron la magnitud. La LSTM es "
              "útil a corto plazo dentro del rango histórico, pero no sustituye el juicio "
              "epidemiológico en eventos extremos."},
    "kw_rotulo": {"pt": "Palavras-chave:", "en": "Keywords:", "es": "Palabras clave:"},
    "kw1": {"pt": "dengue", "en": "dengue", "es": "dengue"},
    "kw2": {"pt": "previsão de séries temporais", "en": "time-series forecasting",
            "es": "pronóstico de series temporales"},
    "kw3": {"pt": "LSTM", "en": "LSTM", "es": "LSTM"},
    "kw4": {"pt": "predição conformal", "en": "conformal prediction", "es": "predicción conforme"},
    "kw5": {"pt": "vigilância epidemiológica", "en": "epidemiological surveillance",
            "es": "vigilancia epidemiológica"},
    # seções
    "sec1_t": {"pt": "Introdução", "en": "Introduction", "es": "Introducción"},
    "sec2_t": {"pt": "Dados e métodos", "en": "Data and methods", "es": "Datos y métodos"},
    "sec3_t": {"pt": "Resultados", "en": "Results", "es": "Resultados"},
    "sec4_t": {"pt": "Limitações e próximos passos", "en": "Limitations and next steps",
               "es": "Limitaciones y próximos pasos"},
    "sec5_t": {"pt": "Conclusão", "en": "Conclusion", "es": "Conclusión"},
    "sec1_eb": {"pt": "Motivação", "en": "Motivation", "es": "Motivación"},
    "sec2_eb": {"pt": "Método", "en": "Method", "es": "Método"},
    "sec3_eb": {"pt": "Resultados · E1 e E2", "en": "Results · E1 and E2", "es": "Resultados · E1 y E2"},
    "sec4_eb": {"pt": "Para onde vai", "en": "Where it goes", "es": "Hacia dónde va"},
    "sec5_eb": {"pt": "Conclusão", "en": "Conclusion", "es": "Conclusión"},
    "sec1_p1": {"pt": "A dengue tem forte componente sazonal, associado à temperatura e à chuva, que "
                      "favorecem a reprodução do Aedes aegypti e a replicação do vírus. Em 2024, o "
                      "Brasil registrou cerca de 6,6 milhões de casos prováveis e 6.199 óbitos "
                      "[Chen e Moraga, 2025], com expansão da doença para o Sul [Araujo et al., 2026]. "
                      "Curitiba, de clima subtropical e historicamente de baixa transmissão, passou de "
                      "913 casos prováveis em 2023 para 15.389 apenas no primeiro semestre de 2024, "
                      "quase o dobro de 2016 (7.883), o maior ano anterior.",
                "en": "Dengue has a strong seasonal component, linked to temperature and rainfall, which "
                      "favour Aedes aegypti reproduction and viral replication. In 2024 Brazil recorded "
                      "about 6.6 million probable cases and 6,199 deaths [Chen and Moraga, 2025], with "
                      "the disease spreading south [Araujo et al., 2026]. Curitiba, subtropical and "
                      "historically low-transmission, went from 913 probable cases in 2023 to 15,389 in "
                      "the first half of 2024 alone, nearly double 2016 (7,883), the previous peak.",
                "es": "El dengue tiene un fuerte componente estacional, ligado a la temperatura y la "
                      "lluvia, que favorecen la reproducción del Aedes aegypti y la replicación del "
                      "virus. En 2024 Brasil registró unos 6,6 millones de casos probables y 6.199 "
                      "muertes [Chen y Moraga, 2025], con expansión hacia el Sur [Araujo et al., 2026]. "
                      "Curitiba, subtropical e históricamente de baja transmisión, pasó de 913 casos "
                      "probables en 2023 a 15.389 solo en el primer semestre de 2024, casi el doble de "
                      "2016 (7.883), el mayor año anterior."},
    "sec1_p2": {"pt": "Antecipar a curva em algumas semanas permite planejar leitos, equipes de campo "
                      "e campanhas de controle. O objetivo é verificar se uma LSTM [Hochreiter e "
                      "Schmidhuber, 1997] supera previsões ingênuas na estimativa semanal de casos "
                      "prováveis em Curitiba, de uma a quatro semanas à frente, e se variáveis "
                      "climáticas melhoram a previsão.",
                "en": "Anticipating the curve by a few weeks helps plan beds, field teams and control "
                      "campaigns. The goal is to check whether an LSTM [Hochreiter and Schmidhuber, "
                      "1997] beats naïve forecasts for weekly probable cases in Curitiba, one to four "
                      "weeks ahead, and whether climate variables improve the forecast.",
                "es": "Anticipar la curva unas semanas permite planificar camas, equipos de campo y "
                      "campañas de control. El objetivo es verificar si una LSTM [Hochreiter y "
                      "Schmidhuber, 1997] supera a los pronósticos ingenuos en la estimación semanal de "
                      "casos probables en Curitiba, de una a cuatro semanas, y si las variables "
                      "climáticas mejoran el pronóstico."},
    "sec2_p1": {"pt": "Utilizou-se o conjunto oficial da Sprint 2024 [Coelho et al., 2024]: casos "
                      "prováveis do SINAN, organizados pelo InfoDengue, e clima semanal da reanálise "
                      "ERA5. Curitiba (código IBGE 4106902) resultou em 753 semanas (3/1/2010 a "
                      "2/6/2024); as quatro últimas, incompletas por atraso de notificação, foram "
                      "excluídas, restando 749. O alvo e a principal entrada são log(1 + casos), "
                      "normalizado por Min-Max do treino; a semana do ano foi codificada por seno e cosseno.",
                "en": "We used the official 2024 Sprint dataset [Coelho et al., 2024]: probable SINAN "
                      "cases organized by InfoDengue, and weekly ERA5 reanalysis climate. Curitiba "
                      "(IBGE code 4106902) yielded 753 weeks (3 Jan 2010 to 2 Jun 2024); the last four, "
                      "incomplete due to reporting delay, were excluded, leaving 749. Target and main "
                      "input are log(1 + cases), Min-Max normalized on the training set; the week of "
                      "year was encoded with sine and cosine.",
                "es": "Se usó el conjunto oficial de la Sprint 2024 [Coelho et al., 2024]: casos "
                      "probables del SINAN organizados por InfoDengue y clima semanal de la reanálisis "
                      "ERA5. Curitiba (código IBGE 4106902) resultó en 753 semanas (3/1/2010 a "
                      "2/6/2024); las cuatro últimas, incompletas por retraso de notificación, se "
                      "excluyeron, quedando 749. El objetivo y la entrada principal son log(1 + casos), "
                      "normalizado Min-Max del entrenamiento; la semana del año se codificó con seno y coseno."},
    "sec3_lead": {"pt": "MAE por horizonte (casos/semana), média de 3 sementes.",
                  "en": "MAE by horizon (cases/week), averaged over 3 seeds.",
                  "es": "MAE por horizonte (casos/semana), promedio de 3 semillas."},
    "sec5_p1": {"pt": "A LSTM univariada é útil no curto prazo dentro da faixa histórica: reduziu o "
                      "erro em 14% a quatro semanas e produziu intervalos de 90% bem calibrados. "
                      "Variáveis climáticas cruas pioraram a previsão. Epidemias fora da faixa, como a "
                      "de 2024, não são antecipadas pelo ponto previsto — mas a faixa de incerteza "
                      "alargada sinaliza o risco, e o julgamento epidemiológico continua indispensável.",
                "en": "The univariate LSTM is useful short-term within the historical range: it cut the "
                      "error by 14% at four weeks and produced well-calibrated 90% intervals. Raw "
                      "climate variables worsened the forecast. Epidemics outside the range, like 2024, "
                      "are not anticipated by the point forecast — but the widened uncertainty band "
                      "signals the risk, and epidemiological judgement remains indispensable.",
                "es": "La LSTM univariada es útil a corto plazo dentro del rango histórico: redujo el "
                      "error en 14% a cuatro semanas y produjo intervalos del 90% bien calibrados. Las "
                      "variables climáticas crudas empeoraron el pronóstico. Las epidemias fuera del "
                      "rango, como la de 2024, no son anticipadas por el punto previsto — pero la franja "
                      "de incertidumbre ensanchada señala el riesgo, y el juicio epidemiológico sigue "
                      "siendo indispensable."},
    # Figura 2 (pipeline) + Tabela 2
    "fig2_caption": {"pt": "Arquitetura: janela de 12 semanas → duas camadas LSTM → saída densa "
                           "multi-horizonte; intervalos por predição conformal adaptativa. Adam "
                           "(1e-3), perda MSE, parada antecipada.",
                     "en": "Architecture: 12-week window → two LSTM layers → multi-horizon dense "
                           "output; intervals via adaptive conformal prediction. Adam (1e-3), MSE "
                           "loss, early stopping.",
                     "es": "Arquitectura: ventana de 12 semanas → dos capas LSTM → salida densa "
                           "multihorizonte; intervalos por predicción conforme adaptativa. Adam "
                           "(1e-3), pérdida MSE, parada temprana."},
    "tab2_caption": {"pt": "MAE (casos/semana). E1 = 2022/23 · E2 = 2023/24. Em verde e negrito, o "
                           "menor erro de cada coluna.",
                     "en": "MAE (cases/week). E1 = 2022/23 · E2 = 2023/24. In green and bold, the "
                           "lowest error of each column.",
                     "es": "MAE (casos/semana). E1 = 2022/23 · E2 = 2023/24. En verde y negrita, el "
                           "menor error de cada columna."},
    # declarações
    "decl_t": {"pt": "Declarações", "en": "Declarations", "es": "Declaraciones"},
    "decl_contrib_t": {"pt": "Contribuições do autor", "en": "Author contributions",
                       "es": "Contribuciones del autor"},
    "decl_contrib_p": {"pt": "F. A. Colque realizou a preparação dos dados, a modelagem, as análises "
                             "e a redação deste trabalho.",
                       "en": "F. A. Colque carried out data preparation, modelling, analyses and the "
                             "writing of this work.",
                       "es": "F. A. Colque realizó la preparación de datos, el modelado, los análisis "
                             "y la redacción de este trabajo."},
    "decl_conflito_t": {"pt": "Conflito de interesses", "en": "Conflict of interest",
                        "es": "Conflicto de intereses"},
    "decl_conflito_p": {"pt": "O autor declara não haver conflito de interesses.",
                        "en": "The author declares no conflict of interest.",
                        "es": "El autor declara no tener conflicto de intereses."},
    "decl_ia_t": {"pt": "Uso de ferramentas de IA", "en": "Use of AI tools",
                  "es": "Uso de herramientas de IA"},
    "decl_ia_p": {"pt": "O assistente Claude (Anthropic) apoiou o planejamento, a revisão do "
                        "pré-processamento, a revisão do código e do texto.",
                  "en": "The Claude assistant (Anthropic) supported planning, preprocessing review, "
                        "code review and text review.",
                  "es": "El asistente Claude (Anthropic) apoyó la planificación, la revisión del "
                        "preprocesamiento, la revisión del código y del texto."},
    "decl_dados_t": {"pt": "Disponibilidade de dados e materiais", "en": "Data and materials availability",
                     "es": "Disponibilidad de datos y materiales"},
    "decl_dados_p": {"pt": "Os dados estão disponíveis em Coelho et al. [2024]. O notebook com o "
                           "código e os resultados está no Google Colab.",
                     "en": "Data are available in Coelho et al. [2024]. The notebook with code and "
                           "results is on Google Colab.",
                     "es": "Los datos están disponibles en Coelho et al. [2024]. El notebook con el "
                           "código y los resultados está en Google Colab."},
    # referências / como citar / materiais
    "ref_t": {"pt": "Referências", "en": "References", "es": "Referencias"},
    "citar_t": {"pt": "Como citar", "en": "How to cite", "es": "Cómo citar"},
    "copiar_abnt": {"pt": "Copiar ABNT", "en": "Copy ABNT", "es": "Copiar ABNT"},
    "copiar_bibtex": {"pt": "Copiar BibTeX", "en": "Copy BibTeX", "es": "Copiar BibTeX"},
    "baixar_cff": {"pt": "Baixar CITATION.cff", "en": "Download CITATION.cff", "es": "Descargar CITATION.cff"},
    "mat_t": {"pt": "Materiais suplementares", "en": "Supplementary materials",
              "es": "Materiales suplementarios"},
    "mat_nb": {"pt": "Notebook (Colab)", "en": "Notebook (Colab)", "es": "Notebook (Colab)"},
    "mat_dados": {"pt": "Dados (Zenodo)", "en": "Data (Zenodo)", "es": "Datos (Zenodo)"},
    "mat_codigo": {"pt": "Código (GitHub, GPL-3.0)", "en": "Code (GitHub, GPL-3.0)",
                   "es": "Código (GitHub, GPL-3.0)"},
    "mat_cff": {"pt": "CITATION.cff", "en": "CITATION.cff", "es": "CITATION.cff"},
    "tres_rs_t": {"pt": "Rigor · Responsabilidade · Reprodutibilidade",
                  "en": "Rigor · Responsibility · Reproducibility",
                  "es": "Rigor · Responsabilidad · Reproducibilidad"},
    "tres_rs_p": {"pt": "Dados, código e as decisões de limpeza publicados com o artigo.",
                  "en": "Data, code and cleaning decisions published with the article.",
                  "es": "Datos, código y decisiones de limpieza publicados con el artículo."},
    "nova_aba": {"pt": "(abre em nova aba)", "en": "(opens in a new tab)", "es": "(abre en una nueva pestaña)"},
    "toc_label": {"pt": "Nesta página", "en": "On this page", "es": "En esta página"},
}

# o título é publicado em PT nos 3 idiomas (WCAG 3.1.2)
T_ARTIGO["artigo_titulo"]["en"] = T_ARTIGO["artigo_titulo"]["pt"]
T_ARTIGO["artigo_titulo"]["es"] = T_ARTIGO["artigo_titulo"]["pt"]
