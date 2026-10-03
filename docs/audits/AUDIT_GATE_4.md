# Lowcost Europa — Auditoria Profunda até ao Gate 4

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

**Data do checkpoint:** 2026-09-13  
**Estado:** registo histórico aprovado pelo Supervisor  
**Âmbito:** Foundation até LE-004, inclusive  
**Nota:** este documento é um snapshot histórico. Decisões futuras devem consultar também `PROJECT_STATE.md`, ADRs e issues posteriores.

## 1. Resumo executivo

O desenvolvimento do Lowcost Europa foi interrompido deliberadamente após a conclusão do Gate 4 para realizar uma revisão global antes de introduzir discovery automático, scoring, frontend ou deployment público.

Conclusão geral:

**A base construída até ao Gate 4 é tecnicamente sólida, coerente com a visão do projeto e adequada à fase atual.**

Não foi identificado nenhum defeito crítico que obrigue a abandonar ou reconstruir a arquitetura. Também não existe justificação, neste checkpoint, para aumentar a infraestrutura.

O sistema continua deliberadamente pequeno:

- Python 3.12;
- Django 5.2 LTS;
- PostgreSQL 16;
- monólito modular;
- integração AliExpress isolada;
- modelo relacional reduzido;
- sem Redis;
- sem Celery;
- sem Docker obrigatório;
- sem microserviços;
- sem Elasticsearch;
- sem frontend JavaScript pesado;
- sem infraestrutura adicional paga.

Princípio mantido:

> Primeiro provar que funciona. Depois provar que vende. Só depois escalar.

O projeto ainda não é um site público nem um produto comercial acabado. Neste ponto existe um motor técnico validado sobre o qual as próximas fases poderão ser construídas.

## 2. Estado concluído até ao Gate 4

### LE-001 — Foundation

Criou a fundação Django/PostgreSQL:

- Django 5.2 LTS;
- Python 3.12;
- PostgreSQL 16;
- settings por ambiente;
- health checks;
- CI;
- Ruff;
- testes;
- documentação.

### LE-002 — AliExpress Integration Layer

Criou uma camada independente para comunicação com AliExpress:

- HMAC-SHA256;
- categorias;
- pesquisa;
- detalhe;
- affiliate links;
- PT/EUR;
- timeouts;
- retries limitados;
- tratamento estruturado de erros;
- normalização de respostas;
- proteção de secrets.

A integração foi testada também contra a API real.

### LE-003 — Minimal Catalog Data Model

Criou:

- `ProductFamily`;
- `Offer`;
- `OfferObservation`.

O modelo representa a regra estratégica principal:

> Product Family permanente, Offer substituível.

Existem constraints PostgreSQL para proteger estados impossíveis diretamente na base.

### LE-004 — Controlled AliExpress Persistence

Foi provado o fluxo completo:

```text
AliExpress
    ↓
AliExpressClient
    ↓
AliExpressProduct
    ↓
Offer
    ↓
OfferObservation
```

Um produto AliExpress conhecido pode ser consultado, normalizado e preparado para persistência. Reimportações reutilizam a mesma Offer e acrescentam novas observações históricas. O dry-run real no Droplet confirmou rollback completo.

## 3. Arquitetura

**Avaliação: APROVADA**

A opção de monólito modular Django continua apropriada. Não existe sinal, nesta fase, de necessidade de:

- microserviços;
- Kubernetes;
- filas distribuídas;
- múltiplos servidores;
- Elasticsearch;
- frontend desacoplado.

A separação atual é suficientemente clara:

```text
apps.core
    infraestrutura básica / health

apps.integrations
    integração AliExpress

apps.catalog
    domínio de catálogo

apps.catalog.services
    casos de uso / persistência
```

Isto permite crescimento sem criar complexidade prematura.

## 4. Integração AliExpress

**Avaliação: APROVADA**

A integração não espalha chamadas AliExpress pelo projeto. Existe um cliente dedicado e um contrato normalizado `AliExpressProduct`.

O cliente implementa:

- assinatura;
- POST para gateway;
- timeout;
- retries limitados;
- tratamento de 429/5xx;
- autenticação;
- parsing;
- categorias;
- pesquisa;
- detalhe;
- affiliate links.

Durante os Gates foi corrigido um ponto importante: `evaluate_rate` não é tratado como estrelas; é tratado como `evaluation_rate_percent`.

Também foi adotada interpretação conservadora de logística:

- valor raw preservado;
- dias apenas quando é possível interpretar com segurança.

Isto está alinhado com o princípio de confiança do projeto.

## 5. Modelo de dados

**Avaliação: APROVADO**

O modelo é pequeno e apropriado. Não foi tentado copiar todo o catálogo AliExpress.

```text
ProductFamily
      ↓
    Offer
      ↓
OfferObservation
```

`ProductFamily` é permanente. `Offer` representa uma listing concreta de uma fonte externa. `OfferObservation` mantém histórico factual.

Isto permite futuramente substituir uma oferta sem destruir:

- página;
- URL;
- SEO;
- histórico;
- confiança acumulada.

A base protege diretamente invariantes importantes, incluindo:

- lifecycle válido;
- source válido;
- availability válida;
- preço não negativo;
- comissão dentro do intervalo;
- evaluation rate 0–100;
- `last_seen_at >= first_seen_at`;
- IDs externos únicos.

## 6. Persistência controlada

**Avaliação: APROVADA**

A LE-004 foi corretamente limitada. Não foi criado crawler, discovery automático nem loop massivo de produtos.

É importado apenas um `product_id` explicitamente indicado.

O serviço executa primeiro as chamadas externas e apenas depois abre a transação PostgreSQL. Isto evita manter uma transação aberta enquanto se espera pela rede.

A persistência:

- reutiliza Offer;
- preserva `first_seen_at`;
- atualiza `last_seen_at`;
- mantém ProductFamily;
- não apaga metadata útil por resposta incompleta;
- cria nova Observation;
- não reutiliza preço/logística antigos como se fossem factos atuais.

O `dry-run` executa a operação e força rollback. A validação live confirmou zero Offer e zero Observation persistentes após o rollback.

## 7. Testes e CI

**Avaliação: FORTE**

No Gate 4 a suite tinha 55 testes.

O CI do SHA final da LE-004 terminou `completed / success` e passou:

- PostgreSQL;
- checkout;
- Python;
- dependências;
- Django check;
- migration drift;
- Ruff;
- migrations;
- testes;
- cleanup dos containers.

A cobertura inclui, entre outros:

- idempotência;
- histórico;
- metadata;
- ProductFamily;
- affiliate link;
- falhas API;
- rollback;
- dry-run.

## 8. Segurança do código

**Avaliação: BOA PARA A FASE ATUAL**

Foi feito scan dos ficheiros versionados. Não foram encontrados:

- App Secrets reais;
- passwords reais;
- tokens;
- private keys;
- credenciais AliExpress.

Os valores encontrados no README/CI são exemplos fictícios de desenvolvimento/teste.

O `.gitignore` bloqueia `.env`, variantes `.env.*`, dumps SQL, SQLite, logs e ambientes virtuais.

A configuração Django exige `DJANGO_SECRET_KEY` e credenciais PostgreSQL via environment variables.

## 9. Segurança de produção

**Avaliação: AINDA NÃO PRONTA — NORMAL NESTA FASE**

O projeto ainda não foi autorizado para produção. O `production.py` é mínimo e força `DEBUG = False`.

Antes de deployment público devem ser decididas/configuradas medidas como:

- HTTPS obrigatório;
- secure session cookies;
- secure CSRF cookies;
- HSTS;
- trusted proxy/origin settings;
- headers apropriados;
- política de logs;
- static files;
- Gunicorn;
- Nginx definitivo;
- rollback.

Isto deve ser bloqueador quando chegar a fase de produção, mas não é defeito neste checkpoint porque produção continua fora de escopo.

## 10. Health checks

**Avaliação: CORRETOS**

Existem:

- `/health/live/`;
- `/health/ready/`.

O readiness faz `SELECT 1` e devolve HTTP 503 quando PostgreSQL não está acessível. É suficiente para a arquitetura atual.

## 11. Droplet — estado real auditado

Configuração confirmada no checkpoint:

- Ubuntu 24.04 LTS;
- 1 vCPU;
- 1 GB RAM;
- 25 GB disco;
- região Londres;
- plano DigitalOcean de US$6/mês;
- Python 3.12.3;
- PostgreSQL 16.15;
- Nginx 1.24.

A restrição económica original continua válida.

## 12. Recursos do Droplet

No momento da auditoria:

- aproximadamente 585 MB de RAM em uso;
- aproximadamente 376 MB disponíveis;
- algum uso de swap;
- swap total de 4 GB;
- disco aproximadamente a 63%;
- aproximadamente 8,8 GB livres.

Isto não significa que o Lowcost Europa esteja pesado: o projeto ainda não está deployed publicamente e o Droplet é partilhado com outras utilizações.

Decisão do checkpoint:

**não aumentar o Droplet.**

Antes de produção, rever logs, utilização de disco, memória e processos. Só aumentar recursos mediante necessidade medida.

## 13. Backups

**Risco: MÉDIO/ALTO antes de produção**

No checkpoint não existiam backups automáticos nem snapshots registados no Droplet.

O risco ainda é limitado porque não existe base de produção com dados comerciais importantes. Contudo, produção com dados reais não deve arrancar sem estratégia de backup.

A solução futura deve ser simples e economicamente proporcional ao estágio do projeto.

## 14. Firewall e superfície do servidor

UFW está ativo.

Portas efetivamente em listening no checkpoint:

- SSH 22;
- HTTP 80;
- HTTPS 443;
- PostgreSQL apenas em localhost 5432.

PostgreSQL não está exposto publicamente.

O firewall ainda tinha regras públicas antigas para 7860, 7861 e 8000, sem processos a escutar nessas portas naquele momento. Devem ser revistas antes de produção, mas não removidas automaticamente porque podem pertencer a outros projetos do mesmo servidor.

## 15. Serviços pesados

Estado no checkpoint:

- PostgreSQL: ativo;
- Nginx: ativo;
- Redis: inativo;
- Docker: inativo.

Isto confirma que a arquitetura continua leve e não mantém componentes desnecessários residentes em memória.

## 16. GitHub e processo de desenvolvimento

O processo por Gates funcionou bem:

1. Builder trabalha em branch;
2. Builder testa;
3. Builder abre PR;
4. Builder para;
5. Supervisor audita;
6. correções são exigidas quando necessário;
7. só depois existe merge.

Este processo apanhou problemas antes da `main`, incluindo:

- significado errado de `evaluate_rate`;
- interpretação de logística;
- IDs `"None"`;
- integridade PostgreSQL;
- perda de decisões estratégicas em documentação.

A disciplina de Gate demonstrou valor real.

## 17. Proteção da main

**Risco de governação: MÉDIO**

A `main` não tinha branch protection técnica neste checkpoint. A tentativa de ativar proteção encontrou uma limitação do plano/configuração GitHub para o repositório privado.

Não se recomenda tornar o repositório público apenas para obter esta funcionalidade.

Até existir alternativa adequada:

> `main` permanece read-only por regra operacional e todas as alterações devem continuar via PR.

## 18. Migrations e base local

Durante a LE-004 foi encontrado que a base local de desenvolvimento tinha uma versão antiga da primeira migration `catalog` aplicada durante trabalho anterior.

Como:

- era desenvolvimento;
- as tabelas estavam vazias;
- não existia produção;
- Offers = 0;
- Observations = 0;

as tabelas foram recriadas localmente a partir da migration oficial final.

Não houve perda de dados.

Lição obrigatória para o futuro: depois de migrations entrarem em produção, migrations aplicadas não devem ser reescritas; deve existir evolução normal por migrations adicionais.

## 19. Documentação e governação

O projeto tem:

- `PROJECT_CONSTITUTION.md`;
- `PROJECT_STATE.md`;
- `AGENTS.md`;
- `SUPERVISOR_PROMPT.md`;
- ADR-001;
- ADR-002;
- documentação AliExpress;
- documentação do modelo;
- documentação da persistência;
- issues por fase;
- PRs auditáveis.

A Issue #12 formalizou a pausa para auditoria após Gate 4 e bloqueou novas fases até revisão humana.

## 20. LE-UX-001

A fase UX/UI não foi esquecida. Está registada no roadmap e não foi executada prematuramente.

Antes do frontend é necessário saber com confiança:

- quais dados existem;
- quais conseguimos validar;
- quais podemos mostrar publicamente;
- quais são suficientemente estáveis.

Só depois deve ser construída a apresentação final.

## 21. O que ainda não existia neste checkpoint

Ainda não existiam:

- discovery automático;
- seleção automática <=5 dias;
- scoring;
- ranking;
- Winner selection;
- histórico de preço suficiente;
- estabilidade longitudinal;
- páginas públicas;
- homepage;
- SEO comercial;
- analytics comercial;
- deployment público;
- processo de backup de produção;
- monitorização de produção;
- frontend final.

Isto era intencional e coerente com o desenvolvimento faseado.

## 22. Riscos classificados

### Críticos

**Nenhum identificado neste checkpoint.**

### Altos antes de produção

- backups ainda não definidos;
- hardening de produção ainda não concluído.

### Médios

- `main` sem proteção técnica;
- disco do Droplet já parcialmente ocupado por utilização partilhada;
- margem limitada de RAM por desenho;
- regras de firewall legadas a rever;
- servidor partilhado com outras utilizações.

### Baixos

- processo futuro de atualização de dependências;
- observabilidade ainda básica, adequada à fase atual.

## 23. Avaliação por área

| Área | Avaliação |
|---|---|
| Visão/Constituição | Muito boa |
| Simplicidade arquitetural | Muito boa |
| Controlo de custos | Muito bom |
| Foundation Django | Boa |
| PostgreSQL | Boa |
| AliExpress integration | Boa |
| Qualidade de dados | Muito boa para a fase |
| Modelo Product Family / Offer | Muito bom |
| Histórico | Bem preparado |
| Persistência | Boa |
| Segurança do repositório | Boa |
| CI/Testes | Muito bons |
| Documentação | Boa |
| Processo Supervisor/Builder | Muito bom |
| Produção | Ainda não preparada |
| Backups | Por resolver antes de produção |
| Frontend/UX | Deliberadamente ainda não iniciado |

## 24. Parecer do Supervisor

A arquitetura não mostra sinais de sobreengenharia e não existem sinais de que o projeto esteja a ser construído depressa demais.

Foram encontrados problemas durante as revisões e corrigidos antes de entrarem na base oficial.

O projeto chegou a um ponto saudável:

> sabemos falar com a AliExpress, sabemos normalizar os dados, temos onde guardá-los e provámos que conseguimos persistir um produto de forma segura e histórica.

Ainda não foi permitido ao sistema começar a tomar decisões automáticas. Essa separação foi considerada correta.

## 25. Decisão do checkpoint

**Resultado: APROVADO ATÉ AO GATE 4.**

Mas:

**LE-005 não foi autorizada neste checkpoint.**

O projeto deve permanecer em pausa até revisão pelo proprietário, sócio e consultor. Depois dos comentários, o Supervisor decide se deve prosseguir, corrigir algo, alterar prioridades ou solicitar nova auditoria.

## 26. Questões recomendadas para revisão externa

1. A arquitetura está suficientemente simples ou existe complexidade desnecessária?
2. O modelo `ProductFamily -> Offer -> OfferObservation` representa corretamente a estratégia comercial?
3. Existe algum risco técnico ou de negócio que deva ser resolvido antes de discovery?
4. O Droplet atual de US$6 deve continuar como alvo inicial até métricas reais justificarem aumento?
5. A sequência futura geral `discovery controlado -> validação de dados -> scoring -> UX/design -> frontend -> staging/MVP` continua adequada?

## 27. Conclusão

Neste checkpoint não se recomendou:

- recomeçar o projeto;
- mudar de stack;
- aumentar infraestrutura;
- introduzir novos serviços;
- acelerar para importação em massa.

A recomendação foi manter o projeto parado enquanto a auditoria era revista externamente.

O Lowcost Europa chegou ao Gate 4 com uma fundação pequena, auditável e tecnicamente coerente.

O próximo passo, naquele momento, era uma decisão humana informada — não mais código.
