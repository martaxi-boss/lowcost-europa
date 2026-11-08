# Domínio oficial — estado operacional (migração concluída)

**Atualizado em 08/11/2026.** Este documento substitui o roteiro de migração de 07/11; as instruções temporárias de emissão de certificados e de DNS estacionado estão obsoletas. O histórico está preservado nos commits Git anteriores.

## Fonte operacional única

- URL pública e indexável: **https://www.lowcost-europa.eu**.
- O domínio de raiz **https://lowcost-europa.eu** encaminha para o `www` com HTTPS.
- O DNS e o serviço de email permanecem na **Dynadot**; o alojamento da aplicação é a VPS Ubuntu. Não configurar outro servidor DNS, Cloudflare, DDNS nem um segundo domínio público por automatismo.
- O e-mail público é **geral@lowcost-europa.eu**; o encaminhamento para a caixa do proprietário é configuração privada e deve ser verificado funcionalmente, não deduzido da publicação de MX/SPF/DKIM/DMARC.
- O Nginx atual de produção é o vhost canónico em `/etc/nginx/sites-enabled/lowcost-europa-eu.conf`; a fonte versionada é `deploy/nginx/lowcost-europa.eu.conf`.
- As rotas `/painel/`, `/admin/`, `/ops/`, `/health/` e callbacks continuam protegidos. As páginas de montra têm indexação condicionada aos requisitos do código. Não apagar a regra de `/.well-known/acme-challenge/`, os certificados do domínio oficial, a renovação automática nem os registos de correio.
- A manutenção do catálogo e do IndexNow é executada pelos timers próprios; IndexNow envia atualizações de páginas, não faz deteções de DNS.

## Higiene de configurações legadas

O domínio de teste **lowcost-europa.duckdns.org** e os subdomínios de teste **sslip.io** não são origens canónicas. Qualquer desativação de vhosts ou certificados antigos exige inventário dos consumidores, backup reversível da configuração Nginx e leitura privada das referências no ambiente antes da alteração. Não confundir os nomes de outros projetos como `fadego.duckdns.org` ou `pink-iptv.duckdns.org` com o Low Cost Europa.

Não executar antigos testes que presumem `noindex` público ou usam DuckDNS. O teste browser atual aponta para o endereço `www` e verifica que as categorias permanecem indexáveis e que o painel é privado.

## Aceitação após cada alteração

1. Confirmar SHA do GitHub igual ao da pasta de produção, com árvore de trabalho limpa e sem migrações pendentes.
2. `nginx -t` e certificado válido para `lowcost-europa.eu`/`www.lowcost-europa.eu`.
3. Verificar 200 em `www`, redirecionamento 301 do domínio raiz, sitemap e robots públicos; `/painel/` anónimo mantém redirecionamento e `noindex`.
4. Confirmar serviço Django, manutenção do catálogo, descoberta semanal, IndexNow e backups sem alterar dados comerciais.
5. Preservar rollback privado limitado ao projeto; nunca fazer `apt autoremove` nem limpeza genérica da VPS.

**Histórico e provas:** [migração certificada](https://github.com/martaxi-boss/VPS/actions/runs/42421004057), [preços e painel](https://github.com/martaxi-boss/VPS/actions/runs/42438124808). Certificação comercial de stock e origem do armazém continua distinta da operação técnica.
