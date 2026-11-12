# -*- coding: utf-8 -*-
"""
Traduções da interface (PT / EN / ES). Idioma vem do navegador; sem correspondência, cai em EN.
Use tr(lang, "chave") — valores com {campos} são formatados no app.py.
Os nomes de nível de alerta são traduzidos só para EXIBIÇÃO; a chave interna continua em PT.
"""
IDIOMAS = ["pt", "en", "es"]
FALLBACK = "en"

NIVEIS = {
    "pt": {"Verde": "Verde", "Amarelo": "Amarelo", "Laranja": "Laranja", "Vermelho": "Vermelho"},
    "en": {"Verde": "Green", "Amarelo": "Yellow", "Laranja": "Orange", "Vermelho": "Red"},
    "es": {"Verde": "Verde", "Amarelo": "Amarillo", "Laranja": "Naranja", "Vermelho": "Rojo"},
}

T = {
    # ---------------------------------------------------------------- topbar / controles
    "brand": {"pt": "Dengue · Previsão LSTM", "en": "Dengue · LSTM Forecast",
              "es": "Dengue · Pronóstico LSTM"},
    "curso": {"pt": "IAGA04 — Aprendizado Profundo · UTFPR",
              "en": "IAGA04 — Deep Learning · UTFPR",
              "es": "IAGA04 — Aprendizaje Profundo · UTFPR"},
    "tema_light": {"pt": "Modo claro", "en": "Light mode", "es": "Modo claro"},
    "tema_system": {"pt": "Modo do sistema", "en": "System mode", "es": "Modo del sistema"},
    "tema_dark": {"pt": "Modo escuro", "en": "Dark mode", "es": "Modo oscuro"},

    # ---- casca JBCS (F2): skip link, navegação, cabeçalho corrido, rodapé ----
    "skip": {"pt": "Pular para o conteúdo", "en": "Skip to content", "es": "Saltar al contenido"},
    "nav_label": {"pt": "Seções da página", "en": "Page sections", "es": "Secciones de la página"},
    "nav_menu": {"pt": "Menu", "en": "Menu", "es": "Menú"},
    "nav_painel": {"pt": "Painel", "en": "Panel", "es": "Panel"},
    "nav_artigo": {"pt": "Artigo", "en": "Article", "es": "Artículo"},
    "nav_metodos": {"pt": "Métodos", "en": "Methods", "es": "Métodos"},
    "nav_dados": {"pt": "Dados", "en": "Data", "es": "Datos"},
    "nav_citar": {"pt": "Como citar", "en": "How to cite", "es": "Cómo citar"},
    "rh_esq": {"pt": "IAGA04 — Aprendizado Profundo · Especialização em IA Generativa Aplicada · UTFPR, 2026",
               "en": "IAGA04 — Deep Learning · Graduate Certificate in Applied Generative AI · UTFPR, 2026",
               "es": "IAGA04 — Aprendizaje Profundo · Especialización en IA Generativa Aplicada · UTFPR, 2026"},
    "rh_esq_curto": {"pt": "IAGA04 · UTFPR 2026", "en": "IAGA04 · UTFPR 2026", "es": "IAGA04 · UTFPR 2026"},
    "rh_dir": {"pt": "Dados: Zenodo 10.5281/zenodo.13328231 · {licenca}",
               "en": "Data: Zenodo 10.5281/zenodo.13328231 · {licenca}",
               "es": "Datos: Zenodo 10.5281/zenodo.13328231 · {licenca}"},
    "rodape_sobre_t": {"pt": "Sobre", "en": "About", "es": "Acerca de"},
    "rodape_sobre_p": {"pt": "Painel acadêmico de previsão semanal de dengue com redes LSTM e "
                             "intervalos conformais de 90%. Nasceu de um estudo de Curitiba (IAGA04/UTFPR).",
                       "en": "Academic panel for weekly dengue forecasting with LSTM networks and 90% "
                             "conformal intervals. Born from a Curitiba case study (IAGA04/UTFPR).",
                       "es": "Panel académico de pronóstico semanal de dengue con redes LSTM e "
                             "intervalos conformes del 90%. Nació de un estudio de Curitiba (IAGA04/UTFPR)."},
    "rodape_dados_t": {"pt": "Dados e fontes", "en": "Data & sources", "es": "Datos y fuentes"},
    "rodape_dados_p": {"pt": "Casos prováveis do SINAN via InfoDengue; malha estadual do IBGE. "
                             "Conjunto da Sprint 2024 (Zenodo 10.5281/zenodo.13328231).",
                       "en": "Probable SINAN cases via InfoDengue; IBGE state boundaries. "
                             "2024 Sprint dataset (Zenodo 10.5281/zenodo.13328231).",
                       "es": "Casos probables del SINAN vía InfoDengue; malla estatal del IBGE. "
                             "Conjunto de la Sprint 2024 (Zenodo 10.5281/zenodo.13328231)."},
    "rodape_lic_t": {"pt": "Licenças e IA", "en": "Licenses & AI", "es": "Licencias e IA"},
    "rodape_lic_p": {"pt": "Código sob GPL-3.0; texto sob CC BY 4.0. O assistente Claude (Anthropic) "
                           "apoiou planejamento, código e revisão.",
                     "en": "Code under GPL-3.0; text under CC BY 4.0. The Claude assistant (Anthropic) "
                           "supported planning, code and review.",
                     "es": "Código bajo GPL-3.0; texto bajo CC BY 4.0. El asistente Claude (Anthropic) "
                           "apoyó la planificación, el código y la revisión."},
    "rodape_aviso": {"pt": "Projeto acadêmico — não é ferramenta oficial de vigilância epidemiológica. "
                           "Para informação oficial, consulte o InfoDengue e as autoridades de saúde.",
                     "en": "Academic project — not an official epidemiological surveillance tool. "
                           "For official information, consult InfoDengue and health authorities.",
                     "es": "Proyecto académico — no es una herramienta oficial de vigilancia epidemiológica. "
                           "Para información oficial, consulte InfoDengue y las autoridades de salud."},

    # ---------------------------------------------------------------- hero
    "chip1": {"pt": "Vigilância epidemiológica", "en": "Epidemiological surveillance",
              "es": "Vigilancia epidemiológica"},
    "chip2": {"pt": "Redes LSTM", "en": "LSTM networks", "es": "Redes LSTM"},
    "chip3": {"pt": "Predição conformal", "en": "Conformal prediction", "es": "Predicción conforme"},
    "chip4": {"pt": "InfoDengue · Mosqlimate", "en": "InfoDengue · Mosqlimate",
              "es": "InfoDengue · Mosqlimate"},
    "h1": {"pt": "Previsão semanal de casos de dengue no Brasil",
           "en": "Weekly dengue case forecasting in Brazil",
           "es": "Pronóstico semanal de casos de dengue en Brasil"},
    "lede": {"pt": "Projeção de uma a quatro semanas à frente para capitais e principais cidades, "
                   "com intervalo de incerteza de 90%. Baseado no estudo de LSTM para Curitiba, "
                   "estendido ao mapa nacional.",
             "en": "One- to four-week-ahead projection for state capitals and major cities, with a "
                   "90% uncertainty interval. Based on the LSTM study for Curitiba, extended to a "
                   "nationwide map.",
             "es": "Proyección de una a cuatro semanas para capitales y principales ciudades, con un "
                   "intervalo de incertidumbre del 90%. Basado en el estudio LSTM para Curitiba, "
                   "extendido al mapa nacional."},
    "stat1": {"pt": "casos prováveis em Curitiba: 2023 vs. 1º sem. 2024 — quase 2× o pico de 2016 (7.883)",
              "en": "probable cases in Curitiba: 2023 vs. 1st half 2024 — nearly 2× the 2016 peak (7,883)",
              "es": "casos probables en Curitiba: 2023 vs. 1er sem. 2024 — casi 2× el pico de 2016 (7.883)"},
    "stat2": {"pt": "erro (MAE) da LSTM vs. ingênuo em 4 semanas (2022/23)",
              "en": "LSTM error (MAE) vs. naïve at 4 weeks (2022/23)",
              "es": "error (MAE) de la LSTM vs. ingenuo a 4 semanas (2022/23)"},
    "stat3": {"pt": "cobertura dos intervalos de 90% (temporada 2022/23)",
              "en": "coverage of the 90% intervals (2022/23 season)",
              "es": "cobertura de los intervalos del 90% (temporada 2022/23)"},
    "stat4": {"pt": "semanas na série de Curitiba (2010–2024)",
              "en": "weeks in the Curitiba series (2010–2024)",
              "es": "semanas en la serie de Curitiba (2010–2024)"},

    # ---- hero + resumo da situação + avisos + KPIs (F3) ----
    "hero_eyebrow": {"pt": "Projeto de pesquisa · IAGA04 · UTFPR 2026",
                     "en": "Research project · IAGA04 · UTFPR 2026",
                     "es": "Proyecto de investigación · IAGA04 · UTFPR 2026"},
    "h1_acento": {"pt": "com redes LSTM", "en": "with LSTM networks", "es": "con redes LSTM"},
    "autor_afil": {"pt": "Especialização em IA Generativa Aplicada · UTFPR",
                   "en": "Graduate Certificate in Applied Generative AI · UTFPR",
                   "es": "Especialización en IA Generativa Aplicada · UTFPR"},
    "cta_painel": {"pt": "Explorar o painel", "en": "Explore the panel", "es": "Explorar el panel"},
    "cta_artigo": {"pt": "Ler o artigo", "en": "Read the article", "es": "Leer el artículo"},
    "cta_citar": {"pt": "Como citar →", "en": "How to cite →", "es": "Cómo citar →"},
    "sit_eyebrow": {"pt": "Próxima semana · SE {se} ({ini}–{fim})",
                    "en": "Next week · EW {se} ({ini}–{fim})",
                    "es": "Próxima semana · SE {se} ({ini}–{fim})"},
    "sit_total": {"pt": "casos previstos nas {n} cidades monitoradas",
                  "en": "cases forecast across the {n} monitored cities",
                  "es": "casos previstos en las {n} ciudades monitoreadas"},
    "sit_barra_aria": {"pt": "Distribuição das {n} cidades por nível: {lista}",
                       "en": "Distribution of the {n} cities by level: {lista}",
                       "es": "Distribución de las {n} ciudades por nivel: {lista}"},
    "palavra_cidade": {"pt": "cidade", "en": "city", "es": "ciudad"},
    "palavra_cidades": {"pt": "cidades", "en": "cities", "es": "ciudades"},
    "aviso_warn_t": {"pt": "Projeto acadêmico — não é alerta oficial",
                     "en": "Academic project — not an official alert",
                     "es": "Proyecto académico — no es una alerta oficial"},
    "aviso_warn_p": {"pt": "O nível exibido é uma simplificação (incidência semanal por 100 mil hab.) "
                           "e não corresponde ao alerta do InfoDengue. Não use para decisões clínicas "
                           "ou de saúde pública.",
                     "en": "The level shown is a simplification (weekly incidence per 100k inhabitants) "
                           "and does not match the InfoDengue alert. Do not use for clinical or public "
                           "health decisions.",
                     "es": "El nivel mostrado es una simplificación (incidencia semanal por 100 mil hab.) "
                           "y no corresponde a la alerta de InfoDengue. No lo use para decisiones clínicas "
                           "o de salud pública."},
    "stat4b": {"pt": "pico de 2024 na escala normalizada: fora da faixa de treino — nenhuma rede previu",
               "en": "2024 peak on the normalized scale: outside the training range — no network predicted it",
               "es": "pico de 2024 en la escala normalizada: fuera del rango de entrenamiento — ninguna red lo previó"},

    # ---- Figura 1: recência, legenda da série, horizontes, Tabela 1, como ler (F4) ----
    "fig1_eyebrow": {"pt": "Figura 1 · interativa", "en": "Figure 1 · interactive",
                     "es": "Figura 1 · interactiva"},
    "recencia": {"pt": "Dados até SE {se}/{ano} · atualização semanal",
                 "en": "Data up to EW {se}/{ano} · weekly update",
                 "es": "Datos hasta SE {se}/{ano} · actualización semanal"},
    "fig1_caption": {"pt": "Previsão de casos prováveis de dengue para t+1 a t+4 semanas (origem: "
                           "SE {se}/{ano}) com intervalo conformal de 90%. Fonte: InfoDengue/SINAN; "
                           "malha estadual IBGE; elaboração própria. Nível simplificado — não é o alerta oficial.",
                     "en": "Forecast of probable dengue cases for t+1 to t+4 weeks (origin: EW {se}/{ano}) "
                           "with a 90% conformal interval. Source: InfoDengue/SINAN; IBGE state boundaries; "
                           "own elaboration. Simplified level — not the official alert.",
                     "es": "Pronóstico de casos probables de dengue para t+1 a t+4 semanas (origen: "
                           "SE {se}/{ano}) con intervalo conforme del 90%. Fuente: InfoDengue/SINAN; "
                           "malla estatal del IBGE; elaboración propia. Nivel simplificado — no es la alerta oficial."},
    "leg_sem_dado": {"pt": "Sem dado", "en": "No data", "es": "Sin dato"},
    "serie_obs": {"pt": "Observado", "en": "Observed", "es": "Observado"},
    "serie_prev": {"pt": "Previsto", "en": "Forecast", "es": "Previsto"},
    "serie_int": {"pt": "Intervalo 90%", "en": "90% interval", "es": "Intervalo 90%"},
    "serie_origem": {"pt": "Origem (SE {se})", "en": "Origin (EW {se})", "es": "Origen (SE {se})"},
    "horiz_nota": {"pt": "A faixa se alarga com o horizonte: ±{a} → ±{b} casos em 4 semanas.",
                   "en": "The band widens with the horizon: ±{a} → ±{b} cases in 4 weeks.",
                   "es": "La franja se ensancha con el horizonte: ±{a} → ±{b} casos en 4 semanas."},
    "tab1_caption": {"pt": "Maiores previsões para a próxima semana (SE {se}). Alternativa textual ao mapa.",
                     "en": "Largest forecasts for next week (EW {se}). Text alternative to the map.",
                     "es": "Mayores pronósticos para la próxima semana (SE {se}). Alternativa textual al mapa."},
    "tab1_cidade": {"pt": "Cidade (UF)", "en": "City (state)", "es": "Ciudad (estado)"},
    "tab1_prev": {"pt": "Previsto", "en": "Forecast", "es": "Previsto"},
    "tab1_inf": {"pt": "IC 90% inf.", "en": "90% CI low", "es": "IC 90% inf."},
    "tab1_sup": {"pt": "IC 90% sup.", "en": "90% CI high", "es": "IC 90% sup."},
    "tab1_nivel": {"pt": "Nível", "en": "Level", "es": "Nivel"},
    "como_ler_t": {"pt": "Como ler este painel", "en": "How to read this panel",
                   "es": "Cómo leer este panel"},
    "como_ler_1": {"pt": "O ponto previsto é a melhor estimativa; a faixa de 90% mostra onde o valor "
                         "real deve cair em 9 de cada 10 semanas.",
                   "en": "The forecast point is the best estimate; the 90% band shows where the real "
                         "value should fall in 9 out of 10 weeks.",
                   "es": "El punto previsto es la mejor estimación; la franja del 90% muestra dónde debe "
                         "caer el valor real en 9 de cada 10 semanas."},
    "como_ler_2": {"pt": "Quanto mais longe (t+4), mais larga a faixa: a previsão perde precisão.",
                   "en": "The further out (t+4), the wider the band: the forecast loses precision.",
                   "es": "Cuanto más lejos (t+4), más ancha la franja: el pronóstico pierde precisión."},
    "como_ler_3": {"pt": "Em surtos fora do histórico (como 2024), o modelo subestima — trate valores "
                         "altos com cautela.",
                   "en": "In outbreaks outside the history (like 2024), the model underestimates — treat "
                         "high values with caution.",
                   "es": "En brotes fuera del histórico (como 2024), el modelo subestima — trate los "
                         "valores altos con cautela."},
    "aviso": {"pt": "Previsões reais. Dados do InfoDengue até a semana de {origem}; LSTM univariada "
                    "(versão A do estudo) com intervalo conformal de 90%, uma rede por cidade. "
                    "Treino do pipeline completo; geocodes validados no IBGE.",
              "en": "Real forecasts. InfoDengue data up to the week of {origem}; univariate LSTM "
                    "(study version A) with a 90% conformal interval, one network per city. Full "
                    "pipeline training; geocodes validated against IBGE.",
              "es": "Pronósticos reales. Datos de InfoDengue hasta la semana de {origem}; LSTM "
                    "univariada (versión A del estudio) con intervalo conforme del 90%, una red por "
                    "ciudad. Entrenamiento del pipeline completo; geocódigos validados en el IBGE."},
    "aviso_strong": {"pt": "Previsões reais. ", "en": "Real forecasts. ", "es": "Pronósticos reales. "},

    # ---------------------------------------------------------------- mapa
    "map_kicker": {"pt": "Mapa interativo", "en": "Interactive map", "es": "Mapa interactivo"},
    "map_h2": {"pt": "Onde a dengue deve subir nas próximas semanas",
               "en": "Where dengue is expected to rise in the coming weeks",
               "es": "Dónde se espera que la dengue aumente en las próximas semanas"},
    "map_sub": {"pt": "Origem: semana de {origem}. Estados coloridos pelo total previsto; bolhas = "
                      "cidades pelo nível de alerta. Clique num estado ou cidade.",
                "en": "Origin: week of {origem}. States shaded by total forecast; bubbles = cities by "
                      "alert level. Click a state or city.",
                "es": "Origen: semana de {origem}. Estados coloreados por el total previsto; burbujas "
                      "= ciudades por nivel de alerta. Haz clic en un estado o ciudad."},
    "lbl_estado": {"pt": "Estado", "en": "State", "es": "Estado"},
    "lbl_cidade": {"pt": "Cidade", "en": "City", "es": "Ciudad"},
    "ph_cidade": {"pt": "Selecione…", "en": "Select…", "es": "Selecciona…"},
    "brasil_todos": {"pt": "Brasil (todos os estados)", "en": "Brazil (all states)",
                     "es": "Brasil (todos los estados)"},
    "map_hint": {"pt": "Fallback: estados sem cidade coberta mostram a previsão estadual agregada.",
                 "en": "Fallback: states without a covered city show the aggregated state forecast.",
                 "es": "Reserva: los estados sin ciudad cubierta muestran el pronóstico estatal agregado."},
    "legend_title": {"pt": "Nível previsto (cidade)", "en": "Forecast level (city)",
                     "es": "Nivel previsto (ciudad)"},
    "estados_trace": {"pt": "Estados", "en": "States", "es": "Estados"},
    "sem_cobertura": {"pt": "Sem cidade monitorada ainda", "en": "No monitored city yet",
                      "es": "Sin ciudad monitoreada aún"},
    "hover_estado": {"pt": "Estado · próx. semana: {v} casos", "en": "State · next week: {v} cases",
                     "es": "Estado · próx. semana: {v} casos"},
    "hover_cidade": {"pt": "Próx. semana: {v} casos · {nivel}", "en": "Next week: {v} cases · {nivel}",
                     "es": "Próx. semana: {v} casos · {nivel}"},

    # ---------------------------------------------------------------- cartão
    "card_prompt": {"pt": "Selecione uma cidade ou estado no mapa.",
                    "en": "Select a city or state on the map.",
                    "es": "Selecciona una ciudad o estado en el mapa."},
    "card_prev": {"pt": "Previsão · próxima semana", "en": "Forecast · next week",
                  "es": "Pronóstico · próxima semana"},
    "card_casos": {"pt": "{v} casos", "en": "{v} cases", "es": "{v} casos"},
    "card_intervalo": {"pt": "Intervalo de 90%: {inf} – {sup} casos",
                       "en": "90% interval: {inf} – {sup} cases",
                       "es": "Intervalo del 90%: {inf} – {sup} casos"},
    "card_nivel": {"pt": "Nível: ", "en": "Level: ", "es": "Nivel: "},
    "escopo_municipio": {"pt": "Município", "en": "Municipality", "es": "Municipio"},
    "escopo_estado": {"pt": "Estado", "en": "State", "es": "Estado"},
    "escopo_cidades": {"pt": "Cidades monitoradas", "en": "Monitored cities", "es": "Ciudades monitoreadas"},
    "nota_piso": {"pt": "Soma das cidades monitoradas da UF — é um piso, não o total do estado.",
                  "en": "Sum of the state's monitored cities — a floor, not the state total.",
                  "es": "Suma de las ciudades monitoreadas del estado — es un piso, no el total estatal."},
    "nota_nivel": {"pt": "Nível simplificado — incidência semanal por 100 mil hab.: <2,5 Verde · "
                         "<10 Amarelo · <30 Laranja · ≥30 Vermelho. Não é o alerta oficial do "
                         "InfoDengue (que combina incidência, Rt e temperatura).",
                   "en": "Simplified level — weekly incidence per 100k inhab.: <2.5 Green · <10 Yellow "
                         "· <30 Orange · ≥30 Red. Not the official InfoDengue alert (which combines "
                         "incidence, Rt and temperature).",
                   "es": "Nivel simplificado — incidencia semanal por 100 mil hab.: <2,5 Verde · <10 "
                         "Amarillo · <30 Naranja · ≥30 Rojo. No es la alerta oficial de InfoDengue "
                         "(que combina incidencia, Rt y temperatura)."},
    "sem_cob_cartao": {"pt": "Ainda não há cidade monitorada neste estado. Quando uma capital ou "
                             "cidade entrar no pipeline, a previsão aparece aqui.",
                       "en": "No monitored city in this state yet. Once a capital or city enters the "
                             "pipeline, its forecast shows up here.",
                       "es": "Aún no hay ciudad monitoreada en este estado. Cuando una capital o "
                             "ciudad entre al pipeline, el pronóstico aparecerá aquí."},

    # ---------------------------------------------------------------- gráfico de detalhe
    "g_intervalo": {"pt": "Intervalo 90%", "en": "90% interval", "es": "Intervalo 90%"},
    "g_observado": {"pt": "Observado", "en": "Observed", "es": "Observado"},
    "g_previsto": {"pt": "Previsto", "en": "Forecast", "es": "Previsto"},
    "g_ytitle": {"pt": "casos / semana", "en": "cases / week", "es": "casos / semana"},

    # ---------------------------------------------------------------- como funciona
    "how_kicker": {"pt": "Como funciona", "en": "How it works", "es": "Cómo funciona"},
    "how_h2": {"pt": "O modelo em quatro peças", "en": "The model in four pieces",
               "es": "El modelo en cuatro piezas"},
    "how1_t": {"pt": "Janela de entrada", "en": "Input window", "es": "Ventana de entrada"},
    "how1_p": {"pt": "Cada previsão usa as 12 semanas anteriores de casos (e, opcionalmente, clima e "
                     "sazonalidade) para projetar t+1 a t+4.",
               "en": "Each forecast uses the previous 12 weeks of cases (and, optionally, climate and "
                     "seasonality) to project t+1 to t+4.",
               "es": "Cada pronóstico usa las 12 semanas anteriores de casos (y, opcionalmente, clima "
                     "y estacionalidad) para proyectar t+1 a t+4."},
    "how2_t": {"pt": "Rede recorrente", "en": "Recurrent network", "es": "Red recurrente"},
    "how2_p": {"pt": "Duas camadas LSTM (64 e 32) com Dropout 0,2 e saída densa. Treino com Adam e "
                     "perda sobre log(1+casos), parada antecipada.",
               "en": "Two LSTM layers (64 and 32) with Dropout 0.2 and a dense output. Trained with "
                     "Adam and loss over log(1+cases), early stopping.",
               "es": "Dos capas LSTM (64 y 32) con Dropout 0,2 y salida densa. Entrenamiento con Adam "
                     "y pérdida sobre log(1+casos), parada temprana."},
    "how3_t": {"pt": "Incerteza", "en": "Uncertainty", "es": "Incertidumbre"},
    "how3_p": {"pt": "Intervalos de 90% por predição conformal adaptativa: a banda se alarga quando "
                     "os erros recentes crescem.",
               "en": "90% intervals via adaptive conformal prediction: the band widens when recent "
                     "errors grow.",
               "es": "Intervalos del 90% por predicción conforme adaptativa: la banda se ensancha "
                     "cuando los errores recientes crecen."},
    "how4_t": {"pt": "Dados", "en": "Data", "es": "Datos"},
    "how4_p": {"pt": "Casos prováveis do SINAN via InfoDengue e clima ERA5 via Mosqlimate "
                     "(Sprint 2024). Curitiba: código IBGE 4106902.",
               "en": "Probable SINAN cases via InfoDengue and ERA5 climate via Mosqlimate "
                     "(Sprint 2024). Curitiba: IBGE code 4106902.",
               "es": "Casos probables de SINAN vía InfoDengue y clima ERA5 vía Mosqlimate "
                     "(Sprint 2024). Curitiba: código IBGE 4106902."},

    # ---------------------------------------------------------------- achados
    "find_kicker": {"pt": "O que o estudo encontrou", "en": "What the study found",
                    "es": "Lo que encontró el estudio"},
    "find_h2": {"pt": "Útil no curto prazo — e honesto sobre os limites",
                "en": "Useful short-term — and honest about its limits",
                "es": "Útil a corto plazo — y honesto sobre sus límites"},
    "find1_t": {"pt": "Ganho dentro da faixa histórica", "en": "Gain within the historical range",
                "es": "Ganancia dentro del rango histórico"},
    "find1_p": {"pt": "Na temporada 2022/23, a LSTM univariada acompanhou a subida e a descida da "
                      "curva e reduziu o erro em até 20% a quatro semanas (14% na média de 3 sementes).",
                "en": "In the 2022/23 season, the univariate LSTM tracked the rise and fall of the "
                      "curve and cut the error by up to 20% at four weeks (14% averaged over 3 seeds).",
                "es": "En la temporada 2022/23, la LSTM univariada siguió la subida y bajada de la "
                      "curva y redujo el error hasta un 20% a cuatro semanas (14% promedio de 3 semillas)."},
    "find2_t": {"pt": "Clima atrapalhou", "en": "Climate hurt", "es": "El clima perjudicó"},
    "find2_p": {"pt": "Com ~600 janelas de treino, as variáveis climáticas acrescentaram mais ruído "
                      "que sinal (sobreajuste). A sazonalidade sozinha manteve o desempenho.",
                "en": "With ~600 training windows, the climate variables added more noise than signal "
                      "(overfitting). Seasonality alone kept the performance.",
                "es": "Con ~600 ventanas de entrenamiento, las variables climáticas añadieron más "
                      "ruido que señal (sobreajuste). La estacionalidad sola mantuvo el desempeño."},
    "find3_t": {"pt": "A epidemia de 2024 escapou", "en": "The 2024 epidemic escaped",
                "es": "La epidemia de 2024 se escapó"},
    "find3_p": {"pt": "O pico de 1.480 casos ficou fora da faixa de treino (1,16 na escala "
                      "normalizada). Todas as redes subestimaram, e a previsão ingênua teve o menor erro.",
                "en": "The peak of 1,480 cases fell outside the training range (1.16 on the normalized "
                      "scale). All networks underestimated, and the naïve forecast had the lowest error.",
                "es": "El pico de 1.480 casos quedó fuera del rango de entrenamiento (1,16 en la escala "
                      "normalizada). Todas las redes subestimaron, y el pronóstico ingenuo tuvo el menor error."},
    "find4_t": {"pt": "Os intervalos avisaram", "en": "The intervals warned",
                "es": "Los intervalos avisaron"},
    "find4_p": {"pt": "Mesmo errando a magnitude, os intervalos conformais se alargaram com a epidemia "
                      "e passaram a conter boa parte do pico — sinalizando a incerteza.",
                "en": "Even missing the magnitude, the conformal intervals widened with the epidemic "
                      "and came to contain much of the peak — signaling the uncertainty.",
                "es": "Aun errando la magnitud, los intervalos conformes se ensancharon con la epidemia "
                      "y pasaron a contener buena parte del pico — señalando la incertidumbre."},

    # ---------------------------------------------------------------- resultados
    "res_kicker": {"pt": "Resultados", "en": "Results", "es": "Resultados"},
    "res_h2": {"pt": "Erro absoluto médio (MAE) por horizonte",
               "en": "Mean absolute error (MAE) by horizon",
               "es": "Error absoluto medio (MAE) por horizonte"},
    "res_caption": {"pt": "MAE em casos/semana (média de 3 sementes). Em verde, o menor erro de cada "
                          "coluna. E1 = 2022/23 · E2 = 2023/24.",
                    "en": "MAE in cases/week (3-seed average). In green, the lowest error per column. "
                          "E1 = 2022/23 · E2 = 2023/24.",
                    "es": "MAE en casos/semana (promedio de 3 semillas). En verde, el menor error de "
                          "cada columna. E1 = 2022/23 · E2 = 2023/24."},
    "th_modelo": {"pt": "Modelo", "en": "Model", "es": "Modelo"},
    "th_e1h1": {"pt": "E1 · 1 sem", "en": "E1 · 1 wk", "es": "E1 · 1 sem"},
    "th_e1h4": {"pt": "E1 · 4 sem", "en": "E1 · 4 wk", "es": "E1 · 4 sem"},
    "th_e2h1": {"pt": "E2 · 1 sem", "en": "E2 · 1 wk", "es": "E2 · 1 sem"},
    "th_e2h4": {"pt": "E2 · 4 sem", "en": "E2 · 4 wk", "es": "E2 · 4 sem"},
    "mod_ingenuo": {"pt": "Ingênuo (última semana)", "en": "Naïve (last week)",
                    "es": "Ingenuo (última semana)"},
    "mod_ingenuo_sazonal": {"pt": "Ingênuo sazonal (ano anterior)", "en": "Seasonal naïve (prior year)",
                            "es": "Ingenuo estacional (año anterior)"},
    "mod_a": {"pt": "LSTM A (só casos)", "en": "LSTM A (cases only)", "es": "LSTM A (solo casos)"},
    "mod_b": {"pt": "LSTM B (casos + clima)", "en": "LSTM B (cases + climate)",
              "es": "LSTM B (casos + clima)"},
    "mod_c": {"pt": "LSTM C (casos + sazonal.)", "en": "LSTM C (cases + seasonal.)",
              "es": "LSTM C (casos + estacional.)"},
    "res_note": {"pt": "Leitura: a LSTM vence o ingênuo dentro da faixa histórica (E1); na epidemia "
                       "fora da faixa (E2), copiar a última semana erra menos — o limite esperado de "
                       "modelos treinados em níveis já observados.",
                 "en": "Reading: the LSTM beats the naïve within the historical range (E1); in the "
                       "out-of-range epidemic (E2), copying the last week errs less — the expected "
                       "limit of models trained on already-observed levels.",
                 "es": "Lectura: la LSTM supera al ingenuo dentro del rango histórico (E1); en la "
                       "epidemia fuera de rango (E2), copiar la última semana yerra menos — el límite "
                       "esperado de modelos entrenados en niveles ya observados."},

    # ---------------------------------------------------------------- para onde vai
    "fut_kicker": {"pt": "Para onde vai", "en": "Where it's heading", "es": "Hacia dónde va"},
    "fut_h2": {"pt": "Da previsão de Curitiba ao mapa nacional",
               "en": "From the Curitiba forecast to a nationwide map",
               "es": "Del pronóstico de Curitiba al mapa nacional"},
    "fut1_t": {"pt": "Modelo regional", "en": "Regional model", "es": "Modelo regional"},
    "fut1_p": {"pt": "Usar municípios vizinhos e semelhantes como preditores (modelo pooled) para "
                     "ampliar a série curta de cada cidade.",
               "en": "Use neighboring and similar municipalities as predictors (pooled model) to "
                     "extend each city's short series.",
               "es": "Usar municipios vecinos y similares como predictores (modelo agrupado) para "
                     "ampliar la serie corta de cada ciudad."},
    "fut2_t": {"pt": "Prever crescimento", "en": "Forecast growth", "es": "Pronosticar crecimiento"},
    "fut2_p": {"pt": "Modelar a taxa de crescimento em vez do nível absoluto, para não saturar em "
                     "surtos fora da faixa histórica.",
               "en": "Model the growth rate instead of the absolute level, to avoid saturating in "
                     "outbreaks outside the historical range.",
               "es": "Modelar la tasa de crecimiento en vez del nivel absoluto, para no saturar en "
                     "brotes fuera del rango histórico."},
    "fut3_t": {"pt": "Clima defasado", "en": "Lagged climate", "es": "Clima rezagado"},
    "fut3_p": {"pt": "Selecionar temperatura (defasagem ~5 sem., r=0,46) e chuva (~8 sem., r=0,26) em "
                     "vez das variáveis cruas que causaram sobreajuste.",
               "en": "Select temperature (~5-week lag, r=0.46) and rainfall (~8-week lag, r=0.26) "
                     "instead of the raw variables that caused overfitting.",
               "es": "Seleccionar temperatura (rezago ~5 sem., r=0,46) y lluvia (~8 sem., r=0,26) en "
                     "vez de las variables crudas que causaron sobreajuste."},
    "fut4_t": {"pt": "Ensembles", "en": "Ensembles", "es": "Ensambles"},
    "fut4_p": {"pt": "Combinar modelos, como a vigilância do Ministério da Saúde passou a fazer a "
                     "partir da Sprint 2024.",
               "en": "Combine models, as the Ministry of Health's surveillance began doing from "
                     "Sprint 2024 on.",
               "es": "Combinar modelos, como la vigilancia del Ministerio de Salud empezó a hacer a "
                     "partir del Sprint 2024."},

    # ---------------------------------------------------------------- rodapé
    "foot_title": {"pt": "Previsão semanal de casos de dengue em Curitiba com redes LSTM",
                   "en": "Weekly dengue case forecasting in Curitiba with LSTM networks",
                   "es": "Pronóstico semanal de casos de dengue en Curitiba con redes LSTM"},
    "foot_author": {"pt": " — Fernando Aramis Colque · IAGA04, Especialização em IA Generativa "
                          "Aplicada, UTFPR (2026).",
                    "en": " — Fernando Aramis Colque · IAGA04, Specialization in Applied Generative "
                          "AI, UTFPR (2026).",
                    "es": " — Fernando Aramis Colque · IAGA04, Especialización en IA Generativa "
                          "Aplicada, UTFPR (2026)."},
    "foot_ref1": {"pt": "Dados: Coelho et al. (2024), Infodengue-Mosqlimate Sprint 2024 — "
                        "Zenodo 10.5281/zenodo.13328231.",
                  "en": "Data: Coelho et al. (2024), Infodengue-Mosqlimate Sprint 2024 — "
                        "Zenodo 10.5281/zenodo.13328231.",
                  "es": "Datos: Coelho et al. (2024), Infodengue-Mosqlimate Sprint 2024 — "
                        "Zenodo 10.5281/zenodo.13328231."},
    "foot_ref2": {"pt": "Referências: Araujo et al. (2026), PNAS · Chen & Moraga (2025), BMC Public "
                        "Health · Mussumeci & Coelho (2020) · Hochreiter & Schmidhuber (1997).",
                  "en": "References: Araujo et al. (2026), PNAS · Chen & Moraga (2025), BMC Public "
                        "Health · Mussumeci & Coelho (2020) · Hochreiter & Schmidhuber (1997).",
                  "es": "Referencias: Araujo et al. (2026), PNAS · Chen & Moraga (2025), BMC Public "
                        "Health · Mussumeci & Coelho (2020) · Hochreiter & Schmidhuber (1997)."},
    "foot_ref3": {"pt": "Malha estadual: IBGE. Apoio de IA (Claude/Anthropic) no planejamento, "
                        "revisão de código e texto.",
                  "en": "State boundaries: IBGE. AI assistance (Claude/Anthropic) in planning, code "
                        "and text review.",
                  "es": "Límites estatales: IBGE. Apoyo de IA (Claude/Anthropic) en planificación, "
                        "revisión de código y texto."},
}


def resolver(code):
    """Normaliza o idioma do navegador para pt/en/es; sem correspondência -> en."""
    if not code:
        return FALLBACK
    c = str(code)[:2].lower()
    return c if c in IDIOMAS else FALLBACK


def tr(lang, chave, **fmt):
    lang = lang if lang in IDIOMAS else FALLBACK
    s = T.get(chave, {}).get(lang) or T.get(chave, {}).get(FALLBACK, chave)
    return s.format(**fmt) if fmt else s


def nivel(lang, chave_pt):
    return NIVEIS.get(lang, NIVEIS[FALLBACK]).get(chave_pt, chave_pt)


def fmt_int(v, lang="pt"):
    """Inteiro com separador de milhar por idioma: 5291 -> '5.291' (pt/es) / '5,291' (en)."""
    s = f"{int(round(v)):,}"
    return s if lang == "en" else s.replace(",", ".")
