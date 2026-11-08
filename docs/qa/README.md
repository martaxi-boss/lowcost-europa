# Provas de QA — retenção e higiene

Os testes de código e de navegação ativos continuam em `apps/**/tests/`,
`tests/js/`, `tests/browser/` e `.github/workflows/`.

As imagens PNG e ficheiros JSON de **capturas manuais antigas**,
provenientes das fases DuckDNS, MVP e auditorias visuais de outubro de 2026,
foram retirados da árvore de trabalho em 08/11/2026 para não acompanharem
cada `git clone` e cada deploy. Os conteúdos permanecem no histórico Git,
na revisão [bd25002](https://github.com/martaxi-boss/lowcost-europa/tree/bd25002e619a3f4240b1b4ffe5247ae4a87a67e1/docs/qa)
e nas evidências dos Actions originais.

A remoção de ficheiros na árvore atual **não reescreve o histórico Git**,
não recupera automaticamente espaço no armazenamento histórico do GitHub
e não substitui testes de regressão ativos.

As provas novas são conservadas nos artefactos temporários dos próprios
GitHub Actions, com limites de retenção; relatórios textuais persistentes
são mantidos aqui e em `PROJECT_STATE.md`.

Não colocar capturas, logs, caches, ficheiros privados ou credenciais na
árvore versionada sem necessidade demonstrada.
