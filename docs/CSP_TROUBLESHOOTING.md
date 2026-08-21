# CSS, JS ou navbar quebram com CSP

Abra DevTools e procure violações `Content-Security-Policy`. Prefira assets em `static/`. Se uma origem externa for obrigatória, configure a allowlist `CSP_*_SRC_EXTRA` correspondente com uma origem HTTPS explícita. Não desligue CSP em produção e não use `*`, `unsafe-inline` ou `unsafe-eval` como atalho.
