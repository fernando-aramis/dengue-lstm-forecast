# Spike 1.16 — `<head>` por idioma no servidor

**Pergunta:** servir título/description do idioma pedido (`?lang=`) para os crawlers?

**Achados (leitura de `app.py`):** o `index_string` é montado uma vez; o idioma é resolvido no cliente
(`?lang=`, `localStorage`, `navigator.language`) e o título é trocado por script antes do boot. O layout já
varia por `Referer`/`Accept-Language` e por isso não é cacheável de forma compartilhada (`Cache-Control` privado).

**Custo/risco de ir ao servidor:** exigiria um `index` por requisição (ou 3 variantes pré-montadas) e `hreflang`
com URLs distintas; `?lang=` na mesma URL canônica gera conteúdo diferente sob o mesmo canonical (duplicidade).
Para valer a pena seria preciso rotas por idioma (`/en/`, `/es/`), o que muda sitemap, canonical e links.

**Decisão: não adotar agora.** Mantém-se `<head>` em PT (`og:locale` pt_BR) e título trocado no cliente.
Reavaliar se houver demanda de tráfego orgânico em EN/ES (rotas por idioma, não `?lang=`).
