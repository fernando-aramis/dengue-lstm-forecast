# -*- coding: utf-8 -*-
"""
Cadastro das cidades cobertas (capitais + principais cidades de cada estado).

IMPORTANTE: os geocodes do IBGE abaixo são os padrões conhecidos de cada município,
mas DEVEM ser validados contra a malha oficial do IBGE antes de ligar os dados reais
do InfoDengue (o InfoDengue usa exatamente o geocode de 7 dígitos como chave).
Curitiba (4106902) está confirmada pelo projeto original.

lat/lon são aproximados (centro do município) e servem só para posicionar o ponto no mapa.
"""

# nome, UF, geocode IBGE, latitude, longitude, população aprox. (só para escalar o exemplo)
CAPITAIS = [
    ("Rio Branco",      "AC", 1200401,  -9.97,  -67.81,   419000),
    ("Maceió",          "AL", 2704302,  -9.67,  -35.74,   957000),
    ("Macapá",          "AP", 1600303,   0.03,  -51.07,   442000),
    ("Manaus",          "AM", 1302603,  -3.12,  -60.02,  2063000),
    ("Salvador",        "BA", 2927408, -12.97,  -38.51,  2418000),
    ("Fortaleza",       "CE", 2304400,  -3.73,  -38.52,  2428000),
    ("Brasília",        "DF", 5300108, -15.79,  -47.88,  2817000),
    ("Vitória",         "ES", 3205309, -20.32,  -40.34,   365000),
    ("Goiânia",         "GO", 5208707, -16.69,  -49.26,  1437000),
    ("São Luís",        "MA", 2111300,  -2.53,  -44.30,  1037000),
    ("Cuiabá",          "MT", 5103403, -15.60,  -56.10,   623000),
    ("Campo Grande",    "MS", 5002704, -20.47,  -54.62,   906000),
    ("Belo Horizonte",  "MG", 3106200, -19.92,  -43.94,  2316000),
    ("Belém",           "PA", 1501402,  -1.46,  -48.50,  1499000),
    ("João Pessoa",     "PB", 2507507,  -7.12,  -34.86,   817000),
    ("Curitiba",        "PR", 4106902, -25.43,  -49.27,  1948000),
    ("Recife",          "PE", 2611606,  -8.05,  -34.88,  1653000),
    ("Teresina",        "PI", 2211001,  -5.09,  -42.80,   868000),
    ("Rio de Janeiro",  "RJ", 3304557, -22.91,  -43.17,  6748000),
    ("Natal",           "RN", 2408102,  -5.79,  -35.21,   890000),
    ("Porto Alegre",    "RS", 4314902, -30.03,  -51.23,  1488000),
    ("Porto Velho",     "RO", 1100205,  -8.76,  -63.90,   539000),
    ("Boa Vista",       "RR", 1400100,   2.82,  -60.67,   436000),
    ("Florianópolis",   "SC", 4205407, -27.59,  -48.55,   516000),
    ("São Paulo",       "SP", 3550308, -23.55,  -46.63, 12325000),
    ("Aracaju",         "SE", 2800308, -10.95,  -37.07,   664000),
    ("Palmas",          "TO", 1721000, -10.18,  -48.33,   306000),
]

# Algumas cidades grandes não-capitais, para ilustrar "principais cidades" além da capital.
MAJORES = [
    ("Campinas",        "SP", 3509502, -22.91,  -47.06,  1223000),
    ("Guarulhos",       "SP", 3518800, -23.46,  -46.53,  1404000),
    ("Londrina",        "PR", 4113700, -23.31,  -51.16,   580000),
    ("Foz do Iguaçu",   "PR", 4108304, -25.54,  -54.59,   258000),
    ("Feira de Santana","BA", 2910800, -12.27,  -38.97,   619000),
    ("Uberlândia",      "MG", 3170206, -18.92,  -48.28,   699000),
]

CIDADES = CAPITAIS + MAJORES

# Nome do estado por UF (para o fallback estadual).
UF_NOME = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}
