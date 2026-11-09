# SEO sem OAuth — contagem local de pedidos vindos da pesquisa

**Escolha técnica (09/11/2026):** não instalar GoAccess, Matomo, GA4, Windsor ou
outro motor. Reutilizar apenas Nginx + Python 3 existentes no projeto e o
GitHub Actions que já executa tarefas na VPS. Não acrescentar cookies, pixels,
scripts ao público, chamadas a serviços externos, credenciais nem migrações.

## O que se mede

O servidor conta pedidos HTTP **GET 200/304** de páginas públicas, quando
o cabeçalho `Referer` anuncia um dos motores Google, Bing, Yahoo,
DuckDuckGo, Brave, Seznam ou Yandex. Só são guardados agregados por motor
dos últimos sete dias, sem IP, User-Agent, URL referenciadora, pesquisa ou
informações pessoais. Não processa páginas administrativas ou redirecionamentos
de afiliados.

É uma medição **de pedidos observados, não de pessoas ou de cliques oficiais**.
O Referer pode faltar ou ser falsificado; bots podem gerar pedidos. Não
substitui o Google Search Console para impressões, CTR, ranking/posição,
termos de pesquisa ou indexação. A interface distingue explicitamente os dados.

## Operação

- O Nginx escreve o log deste vhost separadamente em
  `/var/log/nginx/lowcost-europa.access.log`, usando o formato padrão
  `combined` e a rotação normal de logs do Nginx; não misturar os outros
  projetos. Este é um ficheiro de infraestrutura do serviço Nginx, não uma
  instalação de aplicação.
- O GitHub Actions usa a ponte SSH já autorizada e só envia comandos
  fixos para a VPS. Os logs brutos **não saem do servidor**.
- O agregador de biblioteca padrão
  `apps/catalog/services/search_referral_metrics.py` lê o log exclusivo
  e respetivas cópias rotativas, aplica filtros de segurança e gera apenas
  `private/metrics/search-referrers.json` com permissão 0600, dentro da
  pasta do projeto.
- A vista existente `/painel/` lê o agregado validado, desde que o ficheiro
  exista, esteja recente e pertença ao domínio correto; caso contrário mostra
  estado indisponível, não zero. O painel continua privado/noindex.
- Pode utilizar o agendamento GitHub Actions diário, sem timer adicional na
  VPS. Revalidar saúde da aplicação e integridade Nginx após deploy.

O backup do projeto, as credenciais e as restantes aplicações não devem ser
alterados por este mecanismo. Não afirmar que existem dados antes da primeira
recolha real. Não inferir posições ou vendas a partir desta contagem.
