# Low Cost Europa — auditoria SEO encerrada em 15/11/2026

## Decisão

O SEO técnico existente mantém-se. Não criar outro core, não alterar montras manuais, os shortlinks AliExpress fornecidos pelo proprietário, DNS ou campanhas. As melhorias aprovadas são monitorização externa já integrada e auditoria Lighthouse em telemóvel executada com sucesso.

## Evidências verificadas

- VPS [PR #514](https://github.com/martaxi-boss/VPS/pull/514) integrada; execução final [#43773634448](https://github.com/martaxi-boss/VPS/actions/runs/43773634448) PASS: 9 URLs públicas HTTP 200 (homepage, /pt/, /es/, HIFU PT, Pressoterapia PT, robots, sitemap XML e TXT, favicon), 23 URLs no sitemap, canonical, viewport e indexabilidade PT; serviço Nginx e contador privado PASS. Em 15/11, 2 pedidos de pesquisa identificados, **não 2 visitantes únicos**.
- [Lighthouse móvel #43773999217](https://github.com/martaxi-boss/lowcost-europa/actions/runs/43773999217), contra três páginas de produção; artefacto JSON `lowcost-mobile-lab-reports` com retenção de 7 dias. Runner descartável, Lighthouse 13.6.0, nenhum software instalado na VPS.
- Auditoria anterior integral das 23 páginas [VPS #43281486917](https://github.com/martaxi-boss/VPS/actions/runs/43281486917) (12/11): HTTP 200, canonical/robots/sitemap sem falhas conhecidas. Não afirmar 23/23 revalidado a 15/11.

## Resultado Lighthouse móvel — 15/11 (laboratório)

| Página portuguesa | Desempenho | SEO | Acessibilidade | Boas práticas | LCP | CLS | TBT |
|---|---:|---:|---:|---:|---:|---:|---:|
| Homepage | 92 | 100 | 96 | 100 | 2094 ms | 0 | 0 ms |
| HIFU / EMS | 96 | 100 | 97 | 100 | 2183 ms | 0 | 0 ms |
| Pressoterapia / Tecar | 97 | 100 | 97 | 100 | 2114 ms | 0 | 0 ms |

**Estes valores são simulações de laboratório, não Core Web Vitals reais de utilizadores.** As 3 páginas não justificam novas alterações estruturais nesta fase. Auditoria semanal agendada (GitHub Actions, sujeito a atrasos na agenda) e manual disponível, sem serviços pagos.

## Tráfego e posições — separar métricas

- Consulta Search Console histórica de 08/11 documentou 6 URLs canónicas indexadas (homepage e 5 categorias) em [evidência autenticada](google-search-console-20261108-1856.json), mas não prova a cobertura atual. Duas observações anteriores HIFU (posição média 11) e Aqua Facial (posição 86) tinham só 1 impressão cada e 0 cliques. Não demonstram tendência de ranking. Sitemap aceite com 23 URLs descobertas **não equivale a 23 indexadas**.
- Última leitura detalhada Meta: 294 pedidos em 7 dias (220 Instagram, 53 Facebook, 21 Meta indeterminada; 254 etiquetados como publicidade), em 13/11 17:54 UTC, [VPS #43477342995](https://github.com/martaxi-boss/VPS/actions/runs/43477342995). São pedidos HTTP, não pessoas nem cliques oficiais de anúncios.
- Referências de pesquisa da VPS a 15/11: 2 pedidos identificados do Google. O cabeçalho Referer pode faltar ou ser falsificado.
- Última fotografia verificada de saídas para AliExpress (11/11): 135 redirecionamentos nos 7 dias anteriores e 25 em 10/11, [VPS #43077480489](https://github.com/martaxi-boss/VPS/actions/runs/43077480489). Não confundir com número de hoje, vendas ou comissões. Painel privado já fornece os totais atuais quando consultado.
- A fotografia AliExpress de 11/11 inclui um pagamento identificado, mas não comprova comissão aprovada nem atribuição a uma URL manual específica.

## Limites externos e decisão final

A consulta **oficial atualizada** a Google Search Console (impressões, CTR, clicks e posições para Portugal), as métricas de campo dos Core Web Vitals e a atribuição AliExpress a nível de encomenda **não estavam acessíveis por estas ferramentas**. Não inventar números, não voltar a instalar Windsor nem exigir Google Ads ou serviços pagos. O SEO técnico deve permanecer estável; voltar a avaliar a evolução com janelas oficiais comparáveis, preferencialmente 28 dias. Criar apenas conteúdo específico e útil para compradores em Portugal e referências editoriais legítimas, sem promessas falsas ou backlinks comprados.

**Fecho desta ronda:** monitor externo, disponibilidade pública, higiene do fluxo, relatório técnico mobile e respetiva monitorização sem novas instalações na VPS. **Não é certificação de subida de ranking nem de vendas.**
