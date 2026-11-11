# Auditoria operacional real — Low Cost Europa (11 novembro 2026)

## Âmbito e preservação

Auditoria do percurso Meta -> site -> AliExpress, API de encomendas, medição local, SEO PT, páginas ES, GitHub e VPS, serviços, backups e indexação, por via de workflow GitHub Actions temporário, SSH original com host pinado e consultas de leitura. Não foram adicionados produtos, alterados shortlinks ou transferidos dados privados para GitHub.

Referência de auditoria: https://github.com/martaxi-boss/VPS/actions/runs/43077480489

## Evidência observada em produção (18:25 UTC)

- VPS lowcost-europa commit 060b072964fcf3523643206e94c4ad26807cdf48, igual à main do GitHub à data. Tracked tree limpa e `manage.py check` sem problemas.
- Serviço Django ativo, Nginx `-t` PASS, HTTPS com certificado válido pelo menos sete dias.
- 8 temporizadores relevantes ativos; últimas execuções das unidades correspondentes devolvem `success` (isso não substitui análise dos ficheiros gerados).
- Sitemap XML e TXT coincidentes com 23 URLs; 23/23 HTTP 200; zero `noindex` ou canónicos em falta no conjunto inspecionado; `robots.txt` anuncia sitemaps e resguarda painel.
- SEO PT reforçado publicado nas categorias; páginas ES sem as perguntas novas.
- Cavitação: 17 ofertas do proprietário publicadas e 17 shortlinks originais com prefixo AliExpress; 6 testes seguros HEAD 302/302 devolveram exatamente os links guardados, sem qualquer registo de clique adicional.
- Cliques de saída pelo site: 0 hoje na consulta; 25 ontem; 135 no período de sete dias. Não são visitantes únicos nem vendas.
- API real de afiliados: 1 pagamento, 0 receções, 0 excluídos na janela de 3 dias; grupo `default`. O pagamento não prova comissão aprovada nem associação a um anúncio específico.
- Snapshot local Nginx: 332 minutos de atraso no momento da auditoria; 2 pedidos Meta no dia até à recolha, 55 no dia anterior, 96 nos sete dias; 0 chegadas de pesquisa identificadas na janela. Não se deve interpretar 2 como total em tempo real.
- Snapshot Google Search Console: 3 impressões, 0 cliques, 325 minutos desde a última recolha; fornecedor configurado Windsor.ai; ligação OAuth direta do Google não autorizada.
- Login do proprietário e métricas privadas são protegidos por staff; dados reais não são publicados pela rotina de auditoria.

## Ações de correção (nesta ronda)

1. Corrigir texto do painel privado: o estado `recente` só vale para recolhas até 2 horas, em vez de marcar qualquer snapshot com até 48 horas como atualizado.
2. Reduzir a periodicidade do relatório Nginx na infraestrutura existente, com um único workflow e sem serviço pago, cookies, pixel, API adicional ou daemon.
3. Novos testes do painel para dados recentes e atrasados, apresentação da dependência Windsor e manutenção da segregação Meta / Google / AliExpress.
4. Verificar CI, produção e SHA e eliminar apenas workflows transitórios desta ronda.

## Limites que não se resolvem inventando dados

- Google: a conta proprietária tem de autorizar a API oficial Search Console por OAuth. Até então, a fonte do relatório oficial é o Windsor configurado; Nginx não substitui a posição/CTR do Google.
- Meta: sem dados oficiais da campanha, não é possível provar o URL exato dos anúncios nem atribuir cada clique de saída à campanha; UTMs são apenas sinais observados. Não inventar origem do visitante.
- AliExpress: a plataforma decide elegibilidade/validação de comissões; `pagamento concluído` não é o mesmo que `comissão aprovada`.
- SEO: configuração técnica correta não equivale a indexação completa ou subida efetiva de posições.
- Sem provas de navegação/compra num Android físico, não se pode certificar comportamento da app AliExpress no telemóvel.

## Garantias de não regressão

Portugal é prioritário; Espanha permanece intacta. Manter 23 URLs, versões pt/es, 17 links manuais Cavitação, monitor de disponibilidade e demais timers. Nenhuma instalação global na VPS; sem limpeza fora do projeto, sem coordenador residente. Descrever `100%` apenas para verificações técnicas demonstradas e indicar pendências externas de forma transparente.
