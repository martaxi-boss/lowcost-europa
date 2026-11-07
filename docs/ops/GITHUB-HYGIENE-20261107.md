# Lowcost Europa — higiene do GitHub (2026-11-07)

## Fonte e regras de segurança
Main inicial: `72546fae851ff7a3f10d7acac74460014bf7ead9`. Alterações controladas apenas no repositório Lowcost Europa. Nenhum ficheiro do servidor, base de dados, oferta, backup ou chave foi tocado.

## Inventário observado
- 17 branches incluindo `main`.
- Um único PR aberto antes desta tarefa: #196, redesign profissional, protegido como draft.
- A árvore `main` tem 377 entradas Git, sem caches Python, node_modules nem pastas de artefactos temporários versionadas.
- Nem todos os HEADs das branches antigas são ancestrais diretos de `main`, possivelmente devido a merges squash/rebase. Isto não justifica apagar branches sem comparar a história dos PRs.

## Correções de manutenção
- `.gitignore` exclui npm, Playwright e caches locais, preservando screenshots editoriais legítimos em `docs/qa/`.
- CI bloqueia artefactos gerados acidentalmente versionados, sem bloquear as provas editoriais.
- O workflow existente de limpeza continua a remover apenas HEADs de PRs efetivamente integrados no próprio repositório: o SHA da branch corresponde ao do PR integrado, não pode existir PR aberto para essa branch, não é main e a referência tem de ser imutável durante a eliminação (force-with-lease).
- A limpeza pode abranger também design/docs/fix/chore previamente integrados, para além de builder/ops/hygiene/rea. Branches experimentais não integradas são preservadas.
- Sem eliminação indiscriminada de branches, história, resultados de Actions, backups ou dados comerciais.

## Aceitação
Verificar CI, integração e resultado do workflow de limpeza. O PR #196 continua separado, à espera de QA visual real antes de eventual publicação.
