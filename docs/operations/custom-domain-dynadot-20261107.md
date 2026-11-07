# Low Cost Europa — passagem segura para lowcost-europa.eu (Dynadot)

## Situação auditada em 07/11/2026

Relatório **read-only**: [VPS Actions #42405767220](https://github.com/martaxi-boss/VPS/actions/runs/42405767220).

- Novo domínio: **lowcost-europa.eu**, DNS autoritativo Dynadot `ns1.dyna-ns.net` / `ns2.dyna-ns.net`.
- Registo A raiz e `www` atualmente `185.53.179.149` (estacionamento Dynadot).
- VPS OVH já identificada/pinada: `146.59.145.3`. **Não** trocar servidores de nomes.
- Registos de correio já publicados: MX `0 webhost.dynadot.com`, SPF,
  DKIM e DMARC. **Nunca apagar/substituir** estes registos ao ligar o site.
  A presença de DNS não certifica o envio e a receção reais de mensagens.
- VPS `/srv/projects/lowcost-europa` no commit
  `fefd5df92753382bb7ad191ee19e38b90d8167a3`; Django ativo,
  Nginx `-t` PASS, DuckDNS antigo saudável. Falta novo vhost,
  novo certificado, `DJANGO_ALLOWED_HOSTS` e URL canónica nova.
- Indexação comercial e campanhas NÃO autorizadas. Preservar `noindex`.

## Primeiro, no painel da Dynadot — intervenção na conta do proprietário

No domínio `lowcost-europa.eu`: **My Domains → Manage Domains → Action →
DNS Settings → Dynadot DNS**.

| Secção | Nome | Tipo | Valor |
|---|---|---|---|
| Domain Record (sem escrever @) | raiz `lowcost-europa.eu` | A | `146.59.145.3` |
| Subdomain Record | `www` | A | `146.59.145.3` |

**Editar/substituir** os dois A de estacionamento, não adicionar A
conflituantes. Não criar AAAA sem o IPv6 da VPS validado.
Não utilizar o Website Builder da Dynadot como destino do site.

Guardar as alterações. Preservar integralmente os registos MX, TXT/SPF,
`default._domainkey` (DKIM) e `_dmarc`. Não mudar nameservers nem
introduzir Cloudflare. A propagação de DNS deve ser verificada a partir de
resolvers externos e dos servidores autoritativos antes de qualquer emissão
de certificado.

## Segundo, preparação segura na VPS (apenas quando o DNS estiver correto)

A automatização deve ocorrer pelo fluxo auditado GitHub Actions → SSH,
sem editar a ponte Ferrari, com backup prévio e verificação de host SSH
pinado. Ficheiros de domínio pertencem ao repositório
`/srv/projects/lowcost-europa`; a única integração exterior inevitável
é a configuração Nginx/Let's Encrypt já existente.

1. Confirmar os dois A para `146.59.145.3` e ausência de AAAA órfãos;
   verificar que nada foi alterado no DNS de correio.
2. Confirmar backup recente, revisão esperada e saúde do Nginx/Django.
   Preservar as configurações Nginx e o ficheiro de ambiente atual em
   backup privado antes de alterações.
3. Usar *exclusivamente* `deploy/nginx/lowcost-europa.eu-acme.conf` para
   um vhost **HTTP temporário**. Este ficheiro suporta
   `/.well-known/acme-challenge/` via `/var/www/letsencrypt` e reencaminha
   a restante navegação para DuckDNS até existir SSL. Nunca ativar o
   ficheiro definitivo de HTTPS com certificados inexistentes.
4. Após validar desafio HTTP de ambos os nomes, emitir certificado
   Let's Encrypt com `certbot certonly --webroot`, o webroot existente
   `/var/www/letsencrypt`, e os nomes
   `lowcost-europa.eu` e `www.lowcost-europa.eu`.
   Validar o SAN, a validade do certificado e a renovação automática.
5. Atualizar somente o ambiente privado existente do projeto:
   `DJANGO_ALLOWED_HOSTS` deve incluir o domínio raiz, `www` e
   DuckDNS (sem perder localhost/hosts internos); `DJANGO_CSRF_TRUSTED_ORIGINS`
   deve incluir as novas origens HTTPS; `DJANGO_PUBLIC_SITE_URL`
   passa a `https://lowcost-europa.eu`. Manter
   `DJANGO_PUBLIC_INDEXING_ENABLED=false`. Preservar restantes variáveis.
6. Testar `django check --deploy` e serviço com os hosts novos.
   Só **depois** substituir o vhost temporário por
   `deploy/nginx/lowcost-europa.eu.conf`, verificando `nginx -t` antes
   de recarregar. Não modificar o vhost DuckDNS nem outros projetos.
7. Verificar HTTPS (certificado/cadeia), resposta 200 da raiz,
   `www` → `https://lowcost-europa.eu` (301), cinco categorias,
   filtros e painel, IP→língua em cinco países e fallback inglês,
   `X-Robots-Tag: noindex`, redirecionamentos de afiliado e saúde DuckDNS.
8. Registar evidência de GitHub Actions, commit exato no VPS e estado limpo,
   depois eliminar workflow temporário. Se falhar qualquer verificação,
   repor configurações e ambiente anteriores e confirmar DuckDNS funcional.

**Não** redirecionar DuckDNS para o domínio novo antes de o certificado e
todos os fluxos estarem certificados. Não ativar indexação, marketing ou
publicação comercial apenas por ter um domínio pago.

## O que esta alteração NÃO faz

- Não migra, recria nem configura a caixa `geral@lowcost-europa.eu`;
  apenas **preserva** os registos DNS já existentes.
- Não desloca o alojamento para a Dynadot: esta fornece DNS e correio;
  o site continua a correr na VPS OVH.
- Não adiciona Cloudflare, software global, fornecedor pago obrigatório
  nem um segundo motor/coordenador.

## Fonte para o painel Dynadot

[Documentação oficial de DNS Dynadot](https://www.dynadot.com/pt/ajuda/pergunta/configurar-DNS).
