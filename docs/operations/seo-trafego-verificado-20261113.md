# Lowcost Europa — auditoria SEO e tráfego real | 13/11/2026

## Estado operacional e decisão
Não criar um segundo core SEO: o projeto Django já tem categorias, guias, sitemap, canonicals, hreflangs e contador privado sem fornecedores pagos. Foco Portugal, preservando Espanha, cinco montras manuais, links do proprietário e as 23 URLs públicas.

### Provas reais
- [VPS #43281486917](https://github.com/martaxi-boss/VPS/actions/runs/43281486917): auditoria das 23 URLs, HTML indexável, sitemap XML/TXT, robots, canonicals, alternates, favicon e IndexNow PASS.
- [PR #286](https://github.com/martaxi-boss/lowcost-europa/pull/286) e commit `719738cbb80f366255c2adf1a6a60e445e6d9250`: metadados e guia PT da categoria HIFU/EMS atualizados, e descrição da homepage PT com Pressoterapia/Tecar, com CI e testes em navegador PASS; sem alterações de produtos, links, preço, indexação ES ou URLs.
- Falhas temporárias de deploy com HTTP 502 foram causadas por permissões `0600` em ficheiros Python, impedindo leitura pelo Gunicorn; não foi uma falha de indexação. A [recuperação #43456425910](https://github.com/martaxi-boss/VPS/actions/runs/43456425910) repôs `0644` e HTTPS 200.
- [Rollout final #43456760145](https://github.com/martaxi-boss/VPS/actions/runs/43456760145): `umask 022`, código e permissões confirmados, SHA exato, guias PT/ES, sitemap 23, timers e aplicação PASS.
- [Auditoria após publicação #43456907944](https://github.com/martaxi-boss/VPS/actions/runs/43456907944): resposta 200 na homepage, /pt/, HIFU PT/ES, sitemap; Nginx e Gunicorn operacionais; aplicação com SHA correto.
- [Leitura privada e HTTP exterior #43457339968](https://github.com/martaxi-boss/VPS/actions/runs/43457339968): sete rotas públicas HTTP 200; contadores privados lidos com validação, sem dados pessoais nem logs brutos publicados.

### Pedidos identificados por origem, últimos 7 dias
Relatório local gerado em **13/11/2026 às 15:34:47 UTC**:
- **Meta: 291 pedidos**, Facebook 50, Instagram 220, Meta não especificado 21, e 254 identificados por UTMs de meio pago.
- Meta por dia: 09/11=39; 10/11=55; 11/11=70; 12/11=112; 13/11=15 (parcial).
- **Google: 2 pedidos** identificados; Bing, Yahoo, DuckDuckGo, Brave, Seznam e Yandex: 0 pedidos identificados.
- **Estes valores são pedidos HTTP e não visitantes únicos, cliques oficiais, vendas, posições nem prova de ranking.** O Referer pode faltar e os números podem subestimar chegadas.

### Search Console e SEO
Consulta autenticada histórica (10/11) devolveu duas impressões de 08/11, antes da publicação SEO: HIFU 1 impressão, 0 cliques, posição média 11; Aqua Facial 1 impressão, 0 cliques, posição 86. Não é tendência estatística. Sitemap TXT foi aceite com **23 URLs descobertas**, o que não significa **23 URLs indexadas**.
Nenhuma nova consulta oficial de Search Console foi realizada nesta auditoria. O Google não contabiliza visitas da Meta como cliques orgânicos.

### Prioridades sem criar novo core
1. Consultar Search Console oficial com filtro Portugal: páginas realmente indexadas, impressões, CTR, cliques e posições por consulta/página, comparação de períodos equivalentes. Rever de novo a partir de 16/11, e depois janelas de 28 dias.
2. Fortalecer textos originais de intenção comercial em cada especialidade (HIFU/EMS, Pressoterapia/Tecar, Cavitação, Aqua Facial e Laser) a partir de informação efetiva do produto; não inventar eficácia, stock, avaliações, certificados ou entrega.
3. Verificar experiência móvel e Core Web Vitals antes de otimizações estruturais. Preservar velocidade, URLs, montras e links do proprietário.
4. Procurar referências e ligações editoriais legítimas de páginas relevantes, sem comprar backlinks ou tráfego artificial.
5. Medir Meta e saídas AliExpress separadamente do desempenho orgânico; não reinstalar Windsor ou obrigar Google Ads/OAuth para contabilizar pedidos locais.

### Higiene final
Depois do readback PASS, remover da VPS/main apenas os quatro workflows temporários desta missão, mantendo os runs históricos e o contador recorrente existente `lowcost-search-referrers-daily.yml`. Não alterar serviços, cron persistente, DNS ou produtos durante essa limpeza.
