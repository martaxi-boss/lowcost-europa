# Low Cost Europa: contador local simples (11/11/2026)

## Pedido final do proprietário
Eliminar o Windsor e a ligação Google OAuth. Não usar Google Ads. Manter somente contagem gratuita de tráfego e cliques no painel privado.

## Contadores mantidos
- **Google** e outros motores: pedidos de páginas que chegam com `Referer` identificável no Nginx, agregados localmente. Janela de sete dias. Não são cliques oficiais, visitantes únicos nem sessões. Alguns navegadores omitem o `Referer`, pelo que os contadores podem subestimar as chegadas.
- **Meta**: pedidos com origem ou parâmetros identificadores de Facebook/Instagram no Nginx. Não equivalem a cliques faturados pela Meta.
- **Saídas para AliExpress**: registos de redirecionamentos reais `/go/` no Django; não medem visitas sem origem definida nem provam atribuição da venda.
- **Encomendas AliExpress**: a API afiliada e o timer de seis em seis horas continuam independentes dos contadores de origem.

## O que foi removido do código ativo
- Adaptadores Windsor e Google Search Console OAuth, comando de sincronização de ambos e testes associados.
- Consulta periódica a Google/Windsor pelo serviço de métricas. O serviço periódico trata apenas das encomendas AliExpress.
- Secções de Search Console no painel. Relatórios históricos do Google podem permanecer na base de dados para auditoria, mas nunca são publicados como dados do contador local.

## Infraestrutura e limites
- Os contadores Nginx já são recolhidos pela ponte horária existente do GitHub Actions: `martaxi-boss/VPS/.github/workflows/lowcost-search-referrers-daily.yml`. Apesar do nome histórico do ficheiro, o `cron` corre a cada hora e foi validado na execução #43078346025.
- O relatório privado fica sob `.local-metrics/search-referrers.json`, sem novos cookies, pixels, scripts externos, serviços ou instalações.
- A VPS deve retirar do ambiente da aplicação as variáveis `WINDSOR_API_KEY`, `GOOGLE_SEARCH_CONSOLE_PROVIDER`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REFRESH_TOKEN` e `GOOGLE_SEARCH_CONSOLE_PROPERTY` apenas depois de validação dos testes e do deploy. Não divulgar valores antigos.
- A recolha Nginx é **a cada hora**, não em tempo real; o painel indica quando está desatualizada. O botão de saída continua contado pela base de dados.
- Não existe necessidade de autorizar Google Ads, Google OAuth, Search Console, Windsor.ai, qualquer outro intermediário nem planos pagos.
- Preservar Espanha, 23 URLs, os 17 links manuais Cavitação, timer de disponibilidade, backups, encriptação, painel privado e toda a restante infraestrutura.
- Sem Google Search Console **não podemos medir impressões, CTR, posição média ou todos os cliques orgânicos**. Nunca inventar esses números ou usar cliques de anúncios como prova de ranking.

## Higiene
Não apagar histórico ou evidência de auditoria. Uma alteração de credenciais na VPS requer prova de ausência por nomes de variáveis (não mostrar os segredos), a execução do timer de encomendas e a leitura do painel privado. Em caso de falha, reverter a atualização de código e configuração do servidor.
