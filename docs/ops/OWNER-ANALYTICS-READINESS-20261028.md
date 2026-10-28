# Lowcost Europa — métricas privadas e preparação do lançamento (2026-10-28)

## Limite desta entrega

A área privada `/painel/` passa a mostrar **apenas dados verificáveis na base de dados do próprio site**:

- encaminhamentos brutos de `OfferClick` nas últimas 24h, 7d, 7d anteriores e 30d;
- tendência por dia nos últimos 14 dias (fuso `Europe/Lisbon`), incluindo dias a zero;
- ofertas com todos os critérios técnicos de publicação cumpridos e ofertas editorialmente visíveis mas bloqueadas;
- cinco ofertas com mais cliques de saída nos últimos 7 dias;
- Tracking ID configurado no processo da aplicação, sem o confundir com a proveniência histórica de cada link curto;
- as contagens e a gestão existentes por família de produtos.

O painel é um GET autenticado de proprietário, sem scripts de publicidade, cookies analíticos, chamada a APIs externas, criação de encomendas nem alterações na montra. As contagens são **cliques de saída**, não visitas únicas, impressões, cliques Meta, encomendas, conversões ou comissões. A mesma oferta pode aparecer em mais de uma família; a contagem global de `OfferClick` não soma essas duplicações de família.

## Fontes futuras e contratos a verificar

| Fonte | Informação pretendida | Critério para disponibilizar como métrica |
|---|---|---|
| Site / GA4 | Page views, sessões, interações e saídas para parceiro | Domínio final verificado, configuração de consentimento/privacidade aprovada, propriedade GA4, eventos testados; sem PII em eventos |
| Meta Ads | Gasto, impressões, alcance, cliques, campanhas | Acesso de leitura oficial ao identificador exato da conta/campanha e dados medidos para datas/fuso/moeda; nunca inferir compras a partir de cliques |
| AliExpress Portals | Encomendas, estados, valores e comissões por Tracking ID | API ou exportação oficial de encomendas autorizada e testada; deduplicação por ID da encomenda; separar pendente, confirmado, cancelado e reembolsado |
| Google Search Console | Impressões e cliques orgânicos, pesquisas, cobertura/indexação | Domínio final validado pelo proprietário e propriedade Search Console verificada; sitemap e indexação só com autorização de lançamento |

### Prioridades para ativação após lançamento

1. Configurar domínio e HTTPS definitivos; não alterar o `lowcost-europa.duckdns.org` de testes até autorização explícita.
2. Verificar a propriedade no Search Console e criar GA4 no domínio final. A indexação continua desligada até autorização específica.
3. Definir politica de cookies/consentimento adequada aos eventos e tags necessários (quando aplicável). Não ativar GA4, Meta Pixel ou scripts externos antes desta avaliação.
4. Verificar a fonte de métricas Meta (por exemplo, credenciais e permissões de **leitura** na Marketing API). Uma conta acessível por um conector ChatGPT não torna automaticamente as credenciais disponíveis no processo Django.
5. Certificar consulta de encomendas AliExpress, incluindo Tracking ID e estados. Não prometer que cliques ou pedidos se reconciliam 1:1 com compras: existe atraso, janelas de atribuição e pagamentos fora do site.
6. Só então ligar os adaptadores por fonte, com sincronizações idempotentes, última atualização visível, erro/atraso explícito, sem valores fictícios. Informações desconhecidas devem indicar **Indisponível**, nunca zero.
7. Notificações Telegram opcionais e só após nova encomenda confirmada pela fonte; evitar duplicados ou dados pessoais sensíveis.

## O que esta etapa NÃO faz

- Não ativa contas Google, Meta ou AliExpress nem pede credenciais.
- Não recolhe visitas ou eventos de navegação adicionais no site de testes.
- Não efetua importações de encomendas, conversões, pagamentos ou comissões.
- Não modifica campanhas, orçamento, domínio, SEO, cabeçalhos noindex, URLs de afiliado, catálogos ou serviços.
- Não cria infraestrutura, fornecedores pagos, Skills, servidores MCP ou motores adicionais.

## Verificações de regressão

`apps/catalog/tests/test_owner_analytics_dashboard.py` verifica períodos, datas locais, estado de publicação, proteção por proprietário, ausência de scripts de terceiros e ausência de números fictícios. O pipeline de CI continua a executar a suite de regressão Django existente.
