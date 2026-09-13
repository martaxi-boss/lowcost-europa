# PHASE_0_RECONNAISSANCE

## 1. Resumo executivo
Na Fase 0 o projeto era documental, sem aplicação. Recomendação: Python 3.12, Django 5.2 LTS, PostgreSQL 16, monólito modular e templates server-side. Nenhum secret foi encontrado e nenhum custo novo era necessário.
## 2. Estado atual do repositório
Existiam cinco ficheiros Markdown, apenas `main`, sem proteção técnica, sem PR, CI, dependências, migrations, testes ou código Python.
## 3. Documentação existente
Constituição, AGENTS e Supervisor estavam coerentes; PROJECT_STATE precisava de alinhamento com o roadmap aprovado; README precisava de instruções técnicas.
## 4. Código e estrutura existente
Não existiam Django, modelos, AliExpress, scoring, discovery, endpoints, admin, CI ou deployment.
## 5. Segurança
Sem passwords, API keys, tokens, chaves privadas, `.env` ou credenciais versionadas. Risco ALTO: `main` sem proteção técnica. Risco BAIXO: e-mail pessoal em metadata Git.
## 6. Infraestrutura conhecida
Droplet Ubuntu 24.04 LTS em Londres, 1 vCPU, 1 GB RAM, 25 GB, cerca de US$6/mês e sem backups reportados; função ainda não formalizada na Fase 0.
## 7. Arquitetura recomendada
Django + PostgreSQL + monólito modular + templates server-side, Nginx apenas em staging/publicação e jobs simples antes de filas.
## 8. Alternativas consideradas
FastAPI, Next.js separado, WordPress/WooCommerce e microserviços foram rejeitados nesta fase por complexidade sem benefício mensurável.
## 9. Estrutura inicial proposta
`manage.py`, `config/settings/`, `apps/core/`, `docs/adr/`, `requirements/`, `.env.example`, `.gitignore`, README e PROJECT_STATE.
## 10. Dependências propostas
Django 5.2 LTS, psycopg 3 e Ruff como ferramenta leve; Celery, Redis e Elasticsearch não eram necessários.
## 11. Riscos
ALTO: `main` sem proteção. MÉDIO: a API AliExpress tinha sido validada tecnicamente fora deste codebase, mas a integração ainda não estava implementada nem versionada na aplicação Django; CI, backups, staging, função do Droplet e margem de 1 GB também permaneciam por tratar. BAIXO: metadata de e-mail e observabilidade ainda ausente.
## 12. Custos
Droplet existente cerca de US$6/mês. Nenhum custo novo necessário na Fase 0; custos futuros possíveis apenas para staging, backups, domínio ou proteção GitHub.
## 13. Proposta ADR-001
Formalizar Python 3.12 + Django 5.2 LTS + PostgreSQL 16 + monólito modular + templates server-side, com sistemas distribuídos apenas mediante futura necessidade mensurável.
## 14. Proposta LE-001 — Foundation
Criar fundação Django mínima, segura e testável com PostgreSQL, settings por ambiente, health checks, testes, Ruff, CI e documentação; excluir AliExpress, modelos comerciais e deployment público.
## 15. Dúvidas ou decisões necessárias
O Supervisor decidiu posteriormente a stack, classificou o Droplet como desenvolvimento/futuro staging interno, aprovou CI e ADR-001, manteve `main` read-only e autorizou LE-001.

**GATE 0 concluído e aprovado pelo Supervisor.**
