# Lowcost Europa — ensaio de ranking PT/ES (09/11/2026)

## Objetivo e fronteiras

A meta **9/10** significa **prontidão técnica observável para iniciar o ensaio de
SEO orgânico**, nunca posição 9, top 10 no Google ou vendas garantidas. A nota
só pode ser anunciada depois de CI, browser e produção confirmarem os gates
abaixo. O fornecedor controla preço final, stock, armazém, entrega e transação.

Não criar centenas de páginas automáticas, estimativas falsas, estrelas/Reviews,
Product/Offer/InStock para páginas de categoria afiliadas, ou novas APIs pagas.
Não alterar o conjunto de **23 URLs** nem as cinco famílias PT/ES.

## Informação externa de referência obtida a 09/11/2026

- Conector Windsor Search Console já autorizado para `sc-domain:lowcost-europa.eu`.
- Consulta `Sitemaps` a 09/11: `/sitemap.txt` com 23 URLs submetidas,
  zero erros e zero avisos, `last_downloaded=2026-11-09T14:42:29.738Z`.
  Uma linha adicional sem caminho tinha `submitted=0`, sem interpretação.
- Consulta `Search Analytics` por página/país/data entre 27/10 e 06/11:
  **0 linhas devolvidas**. Isto não confirma zero impressões ou visitas e não
  prova que todas as páginas já estejam no índice; posição/CTR ainda
  **indisponíveis**. Confirmar no Search Console, não inventar zero nem ranking.
- Site e SEO inicial testados anteriormente em produção no runner GitHub Actions.
- Preços de fornecedor: PT tinha 46/46 ofertas publicáveis com EUR recente;
  ES 8/46 com observação ES/EUR recente na auditoria de 09/11. Uma observação
  ES recente só pode aparecer identificada como preço **ES**, sem stock nem prazo
  presumidos. Se faltar ES, o preço PT será descrito como referência PT.
- Dados de Search Console, preço e cobertura variam com o tempo; nunca copiar
  contagens antigas como valores instantâneos.

## Consultas piloto para interpretação humana no Search Console

Não são previsões de volume. São grupos de procura para procurar, classificar e
priorizar **quando existirem linhas reais da propriedade**:

| PT | ES | Categoria |
| --- | --- | --- |
| máquina cavitação radiofrequência | máquina cavitación radiofrecuencia | Cavitação/RF |
| hidrodermoabrasão aqua facial profissional | hidrodermoabrasión aqua facial profesional | Aqua Facial |
| máquina pressoterapia profissional | máquina presoterapia profesional | Pressoterapia/RF Tecar |
| máquina HIFU profissional | máquina HIFU profesional | HIFU |
| equipamento laser díodo profissional | equipo láser de diodo profesional | Laser e pigmentos |

Não comprar publicidade por estas frases apenas porque aparecem aqui. Primeiro
ver consultas realmente recolhidas pelo Google: `date`, `page`, `country`,
`query`, `impressions`, `clicks`, `position` e `ctr`. Distinguir
marca vs. não marca, e PT vs. ES, e não misturar Portugal/Espanha num só
valor médio. Definir o primeiro período que tiver dados como baseline, separar
o período anterior e posterior a esta publicação, e reavaliar sem prazo garantido.

## Scorecard binário de prontidão técnica (máximo 10 pontos)

1. HTTPS público e páginas indexáveis retornam 200 sem redirecionamento oculto.
2. `robots.txt` público, pesquisa/painel/`/go/` sem indexação indevida.
3. `sitemap.xml` e `sitemap.txt` equivalentes: 23 URLs, TXT aceite pelo Google.
4. Canonicals autorreferentes e `hreflang` pt-PT/es-ES/x-default recíprocos.
5. Cinco títulos/descritivos únicos PT e cinco ES, sem conteúdo duplicado enganoso.
6. Guias específicos para compra com limites transparentes, em ambas as línguas.
7. Ligações internas HTML entre categorias ativas e breadcrumb visível coerente.
8. Prova de mercado de preço separada por país; PT não é apresentado como ES,
   nem stock/prazo ou schema de comércio são inventados.
9. CI Django, segurança, browser de **todas as 23 URLs** em desktop e em mobile
   emulado, e pós-deploy SHA/backup/serviços/links válidos **PASS**.
10. Pelo menos uma linha de desempenho real no Search Console para medir posição
    e impressões PT/ES, **sem inferir indexação a partir de submissão**.

**Critério de fecho do ensaio:** pontos 1–9 certificados = **9/10 para começar o
teste técnico de ranking**, enquanto o 10 estiver `AWAITING_GOOGLE_DATA`.
Sem gates 7–9 efetivamente publicados e verificados, a meta 9 não foi alcançada.

## Independência comercial

A prontidão SEO não valida separadamente: stock por SKU, origem de armazém,
entrega ES/PT, vendas e comissões de publicidade, teste num Android físico,
restauro integral de backups externos ou receção do email institucional.
Permanecem pendências comerciais/operacionais diferentes, sem impedir
rastreamento e análise da pesquisa orgânica de páginas informativas honestas.

## Fontes de método

- Google Search Central: SEO starter guide e conteúdo útil centrado nas pessoas.
- Documentação Google: ligações internas rastreáveis, `hreflang` e BreadcrumbList.
- Provas operacionais: GitHub PR e Actions associados à publicação desta versão.
