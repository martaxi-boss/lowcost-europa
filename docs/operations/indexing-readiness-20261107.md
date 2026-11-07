# Preparação de indexação — 7 de novembro de 2026

## Estado e limites

**Identidade legal fornecida pelo proprietário. Deploy e indexação em curso; não concluídos nesta fotografia.**
Esta preparação foi autorizada pelo proprietário na conversa de 07/11.
Não foi pedido qualquer comando manual para a VPS.

- Propriedade de domínio `lowcost-europa.eu` criada no Google Search Console e confirmada pelo Google com **Propriedade validada**, por TXT na Dynadot.
- Inspeção da raiz WWW no Google: **O URL não está no Google** / **A Google não reconhece o URL**. Sem sitemap de referência detetado.
- Sitemap ainda não submetido nem pedidos de indexação enviados nesta fotografia: aguarda deploy e verificações finais.
- Produção continua com `DJANGO_PUBLIC_INDEXING_ENABLED=false`, meta/headers noindex e robots `Disallow: /`.
- Código de preparação em PR #207, **rascunho e não implantado**.

## Provas técnicas reais

Auditoria GitHub Actions → SSH → VPS, sem alteração do runtime:
[execução 42421004057](https://github.com/martaxi-boss/VPS/actions/runs/42421004057).

- VPS e GitHub main coincidem em `bb3921b646102cba0af0f397bddfde8b2f37d39a`; ficheiros versionados limpos.
- Django ativo; Nginx válido; vhost HTTPS ligado ao ficheiro versionado; backups de rollback preservados.
- Certificado válido por mais de 30 dias, SAN raiz+WWW, ficheiro de renovação e timer encontrados.
- DNS A raiz+WWW `146.59.145.3`; ausência de AAAA; MX/SPF/DKIM/DMARC preservados em verificações autoritativas e resolver independente.
- HTTP raiz, HTTP WWW e HTTPS raiz devolvem 301 para `https://www.lowcost-europa.eu/`.
- Painel e admin anónimos redirecionam para autenticação; painel noindex e privado.
- Testes locais da aplicação com amostras MMDB PT/ES/FR/DE/GB/NL passaram; não equivalem a seis ligações VPN externas.
- Django deploy check: dois avisos deliberados, HSTS sem includeSubDomains/preload. Sem alargar essas políticas a subdomínios não auditados.
- Sem alterações de migração.

Auditoria HTTPS externa da conversa, concluída às 22:33 UTC:
[JSON de resultados](indexing-public-audit-20261107.json).

- 17 rotas verificadas, sem erros de transporte; 11 URLs no sitemap XML.
- Página principal, cinco categorias e cinco páginas institucionais devolveram 200.
- 52 rotas `/go/` verificadas com HEAD: todas 302 para HTTPS em `s.click.aliexpress.com`; sem seguir destinos ou criar cliques de compra GET.
- Os 52 links ainda não têm `rel=sponsored` em produção. Corrigido apenas na preparação da PR.
- Nenhuma atribuição de comissão, stock no vendedor, preço final de checkout ou entrega física foi certificada.

## Oferta observada na VPS

| Categoria | Ofertas públicas elegíveis |
|---|---:|
| Cavitação + RF + Vacuum | 17 |
| Microdermoabrasão / Hidrodermoabrasão / Multifunções faciais | 10 |
| Pressoterapia / RF Tecar | 5 |
| HIFU | 12 |
| Diodo Laser / Remoção de tatuagens / Pigmentação | 8 |

Total 52. Nenhum URL de afiliado inválido, nenhum preço totalmente ausente.
Três últimos preços válidos têm mais de sete dias. A observação mais recente
das 52 ofertas marca disponibilidade UNKNOWN; isso não prova indisponibilidade
nem autoriza fabricar confirmação de stock. A montra deve continuar a apresentar
preços como observados e stock/prazos sujeitos a confirmação no parceiro.

## Correção preparada

- Indexação apenas no hostname HTTPS público configurado; nomes alternativos mantêm noindex.
- Remoção do noindex global Nginx apenas na origem WWW, mantendo proteção do callback PHP.
- Proteção independente no Django de painel, admin, ops, saúde, integrações, encaminhamentos e páginas de erro.
- Robots público com exclusões operacionais e referência ao sitemap.
- Pesquisa e categorias retiradas excluídas; sitemap continua apenas com páginas públicas.
- Links afiliados qualificados com `rel="sponsored nofollow"`.
- Testes de regressão para lançamento, hostname alternativo, rotas privadas e categoria retirada.

## Identidade legal e privacidade

O proprietário forneceu a identidade individual, morada e NIF na conversa de 07/11.
Os valores não pertencem ao repositório nem aos logs. O deploy transporta-os cifrados,
guarda-os em `.legal/operator.json` e renderiza-os em contacto, termos e privacidade.
A ausência de campos bloqueia a indexação. Não se reutilizam os dados privados da conta Dynadot.
As páginas de privacidade incluem responsável, finalidades, fundamento, critério de conservação,
serviços externos e direitos, com tradução nos cinco idiomas.

Fontes oficiais:
- [DL 7/2004, artigo 10.º](https://diariodarepublica.pt/dr/legislacao-consolidada/decreto-lei/2004-73199154-73197494).
- [RGPD](https://eur-lex.europa.eu/eli/reg/2016/679/pt), informação do responsável pelo tratamento.
- [Google: qualificação de links afiliados](https://developers.google.com/search/blog/2021/07/link-tagging-and-link-spam-update).
- [Google: pedidos de rastreio não garantem indexação](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl).

## Higiene desta fase

Workflow temporário de auditoria retirado de VPS/main após a execução.
A VPS foi apenas lida; não foram criados daemons, instalações, ficheiros temporários
ou apagados dados da aplicação. Preservar a PR de preparação para continuação.
Não chamar a esta fase lançamento público nem fecho de indexação.
