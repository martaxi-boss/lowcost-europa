# Portugal SEO - melhoria editorial (11/11/2026)

## Decisao de mercado
- Prioridade exclusiva: Portugal (pt-PT). Mantem-se Espanha com URLs, metadados, guias e hreflangs existentes. Nao e necessario retirar Espanha do indice.
- Sem novos produtos, sem alteracoes de montra manual, links de afiliado, botoes de compra, campanhas Meta, rotas de saida, DNS ou timers.
- Site com 23 URLs mantem-se estavel. Nao criar paginas artificiais.

## Melhorias
1. Metadados da pagina inicial portuguesa mais descritivos e orientados ao mercado e cinco tecnologias do catalogo.
2. Quinze perguntas praticas para compradores em Portugal, tres por categoria, complementam os cinco guias existentes: acessorios, consumiveis, compatibilidade, documentacao, envio, garantia e custo total.
3. Nao afirmar stock, certificacao, eficacia, assistencia ou entrega da variante sem verificacao; condicoes de venda sao sempre do parceiro.
4. Novo conteudo apenas em paginas PT e na rota principal quando apresentada em portugues. Sem alteracao dos guias e dos resultados HTML espanhóis, nem schema FAQPage, Product, Offer ou avaliacoes inventadas.
5. Testes de regressao PT/ES para titulo, canonical, hreflang, 23 URLs e isolamento de conteudos; CI Django e verificacao da producao obrigatorios.

## Medicao de ranking
- O Nginx mede pedidos de paginas com referer; nao mede posicao, CTR ou cliques organicos oficiais.
- Usar o Google Search Console, quando disponivel, com filtro de pais Portugal, tipo web, distinguindo pesquisas de marca e nao marca.
- Acompanhar URLs /pt/ e /pt/products/ e respetivas rotas principais portuguesas, comparando cliques, impressoes e posicao por periodos equivalentes de 28 dias com data de publicacao assinalada.
- Quando nao existirem dados de pesquisas por pais, apresentar INDISPONIVEL e nao um zero inventado.
- Duas observacoes isoladas de 08/11 (HIFU posicao media 11; Aqua Facial 86, uma impressao cada) nao provam ranking estavel.

## Aceitacao e salvaguardas
- CI verde: django check, testes, ruff, migrations, Javascript.
- Deploy protegido com SHA exato, lock, diff permitido, backup/rollback e leitura de HTML PT/ES.
- Pos-deploy: PT apresenta perguntas e ES nao, 23 URLs, canonical/hreflang e servico/Nginx/timers mantidos.
- Higienizar so workflows temporarios da missao depois de verificar sucesso e manter runs como evidencia.
- Sem promessas de posicoes, prazos de ranking, cliques artificiais ou backlinks comprados.

Fontes:
https://developers.google.com/search/docs/fundamentals/creating-helpful-content
https://developers.google.com/search/docs/essentials
https://developers.google.com/search/docs/monitor-debug/google-analytics-search-console
