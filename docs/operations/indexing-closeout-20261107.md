# Lançamento técnico e pedidos Google — 07/11/2026

## Resultado confirmado

**Site tecnicamente publicado; seis pedidos de indexação aceites. A inclusão efetiva no índice Google ainda não foi confirmada.**

| Etapa | Resultado observado |
|---|---|
| Propriedade de domínio Search Console | Validada por TXT na Dynadot |
| Página principal e cinco categorias | HTTP 200, meta index/follow e canonical WWW |
| Páginas institucionais | Contacto, termos e privacidade com identidade confirmada do operador |
| robots.txt | Público, anuncia sitemap e exclui rotas operacionais |
| sitemap.xml | XML válido, HTTP 200, 11 URLs públicos únicos |
| HTTP raiz/WWW e HTTPS raiz | 301 para https://www.lowcost-europa.eu/ |
| Painel e Django Admin anónimos | 302 para autenticação, noindex, private/no-store |
| Pesquisa, ops, saúde e encaminhamentos | Permanecem excluídos de indexação |
| Links de afiliado | 52/52 HEAD devolvem HTTPS; 52/52 qualificados sponsored/nofollow |
| DNS e correio | A raiz+WWW, MX, SPF, DKIM e DMARC preservados; TXT Google acrescentado |
| Inclusão efetiva no Google | Não confirmada nesta sessão |

## Provas de código, testes e implantação

- [PR #207](https://github.com/martaxi-boss/lowcost-europa/pull/207), integrada na revisão de aplicação `51bee8009492c3cd5855f4aae71de3597fd1965b`.
- [CI pós-merge #42422298302](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42422298302): **744 testes PASS**, Ruff, Django, migrações e JavaScript.
- [Chromium #42422298343](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42422298343): **PASS**, catálogo sintético e quatro viewports; não equivale a quatro dispositivos físicos.
- [Auditoria fonte #42422298429](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42422298429): **PASS**.
- [Implantação real #42422451050](https://github.com/martaxi-boss/VPS/actions/runs/42422451050): **LOWCOST_INDEXING_GUARDED_LAUNCH=PASS**, identidade legal nas três páginas, seis páginas comerciais, privacidade, robots/sitemap e serviço verificados.
- [Auditoria externa pós-lançamento](indexing-public-after-20261107.json): **17 rotas sem erros de transporte**, 11/11 páginas públicas com canonical exato e sem noindex, 52/52 redirecionamentos HTTPS.
- A revisão documental posterior só altera este relatório, a evidência HTTP e PROJECT_STATE; o alinhamento final da VPS deve certificar que não existe diferença de código executável.

As tentativas iniciais de rollout falharam em verificações de identidade Git e sintaxe do script de transporte. O processo foi corrigido e a aceitação só é atribuída à execução final acima. Não foram feitas migrações de base de dados.

## Confirmações observadas no Google

Propriedade: `sc-domain:lowcost-europa.eu`.
O Google mostrou **Propriedade validada** por fornecedor DNS.
Não se alteraram nameservers nem registos de correio existentes.

Para cada URL seguinte foi observado **Indexação solicitada** e a indicação de entrada numa fila de rastreio prioritária:

- https://www.lowcost-europa.eu/
- https://www.lowcost-europa.eu/products/cavitacao-rf-vacuum-corpo/
- https://www.lowcost-europa.eu/products/hydrodermoabrasao-aqua-facial-multifuncoes/
- https://www.lowcost-europa.eu/products/pressoterapia-vacuum-drenagem/
- https://www.lowcost-europa.eu/products/hifu/
- https://www.lowcost-europa.eu/products/diodo-laser-remocao-tatuagens-pigmentacao/

**Aceitação do pedido não é confirmação de indexação.** Antes desses pedidos, as inspeções mostravam URL desconhecido / não indexado.

### Sitemap

O envio de `https://www.lowcost-europa.eu/sitemap.xml` foi aceite com
**Mapa do site enviado com êxito**. Contudo, a tabela do Search Console ainda
apresentou **Não foi possível obter**, tipo desconhecido e zero páginas descobertas
na verificação subsequente. Isto não deve ser descrito como leitura Google concluída.

**Teste em direto do próprio Google, 07/11/2026 às 22:59:54:** ferramenta de inspeção para smartphone; rastreio permitido **Sim**; obtenção da página **Com êxito**; indexação permitida **Sim**. Isto confirma acesso em direto, não o processamento pelo serviço de sitemaps nem inclusão no índice.

O ficheiro foi independentemente obtido por HTTPS com HTTP 200, Content-Type
application/xml, namespace correto e onze URLs únicos. Não apresenta noindex,
não requer autenticação e está anunciado em robots.txt. Os seis testes associados
aos pedidos de páginas foram aceites pelo próprio Google.

[Consultar o estado real no Search Console](https://search.google.com/search-console/sitemaps?resource_id=sc-domain%3Alowcost-europa.eu).
A causa do estado inicial de leitura não está confirmada; não se atribui
automaticamente a cache ou a um erro do servidor.

## Identidade e privacidade

Os dados legais confirmados pelo proprietário são carregados de configuração
privada dentro do projeto e publicados apenas nas páginas legais autorizadas.
Os valores não foram incluídos no código, nos testes, neste relatório ou nos logs.
O transporte usou cifra RSA-OAEP; a chave privada temporária foi removida após
a implantação. A aplicação mantém indexação fechada se os campos legais faltarem.

A política de privacidade descreve responsável, dados tratados, finalidades,
fundamento, critério de conservação, serviços externos e direitos, nos cinco idiomas.
Não foi inventada uma sociedade, registo comercial, avaliação de cliente ou certificação.

## Ofertas e limites da auditoria

A fotografia na VPS continha 52 ofertas elegíveis em cinco categorias,
nenhuma sem preço observado e nenhuma com URL afiliado inválido.
Três preços observados tinham mais de sete dias. As últimas observações de stock
eram UNKNOWN. A apresentação mantém datas, avisos de informação antiga e confirmação
final no parceiro; não promete stock, entrega garantida, preço de checkout ou comissão.
Os testes HEAD não seguiram o parceiro nem registaram cliques GET de compra.

## Higiene e recuperação

- Workflows temporários de preparação, auditoria e lançamento retirados de VPS/main; execuções preservadas como prova.
- Chave privada temporária eliminada; configuração legal intencional preservada com acesso apenas do utilizador da aplicação.
- Rollback privado da configuração e revisão anterior preservados.
- Sem alteração de credenciais, nameservers, caixa de correio, outros projetos ou fornecedores pagos.
- O alinhamento documental final verifica árvore versionada limpa, serviço ativo, Nginx válido, saúde e permissões legais. Apenas uma cópia duplicada do rollback criado por esta tarefa pode ser eliminada após comparação byte a byte.

## Pendente externo

Aguardar leitura do sitemap e inclusão das páginas pelo Google, verificando
o estado no Search Console. Não repetir pedidos das mesmas páginas para tentar
alterar a prioridade. A documentação oficial esclarece que um pedido não garante
inclusão: https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl
