# Core SEO PT/ES — preparação controlada (08/11/2026)

## Estado e integridade

Esta alteração é **código em revisão**, não uma certificação de implementação na VPS.
As seis páginas comerciais indexadas no Google conservam os respetivos URLs e
canonicals originais. Os endereços `/pt/`, `/es/`, `/pt/products/<slug>/` e
`/es/products/<slug>/` são explicitamente opt-in, inicialmente 404.
Não se faz qualquer redirecionamento GeoIP de motores ou pessoas.

## Cinco pontos

1. **Segurança / GitHub / VPS:** usar PR com CI, verificar versão operacional, serviços,
   backups/offsite, TLS, `main` e rollback antes da implantação. A `main`
   carece de uma regra administrativa de proteção; a capacidade de criar PR
   não equivale a capacidade de gerir Settings > Rules > Rulesets. Não apagar
   backups, certificados nem histórico. Rollout só no projeto `lowcost-europa`.
2. **PT/ES:** URLs estáveis e independentes da localização do IP, referências
   recíprocas `hreflang="pt-PT"`, `"es-ES"` e `"x-default"`; canonicals
   autorreferentes. A raiz e as cinco categorias atuais conservam a sua
   indexação prévia. O sitemap passa de 11 para 23 URLs **apenas após ativação**.
   URLs de operações, checkout externo e pesquisa nunca entram no sitemap.
3. **Estrutura / confiança:** WebSite + Organization básicos na homepage;
   BreadcrumbList nas categorias publicadas. Não publicar schema Product,
   Offer, Review, Ratings, preço atual, stock, entrega ou armazém sem evidência
   por SKU e conteúdo correspondente. Títulos e descrições da montra ganham
   variantes PT/ES. Navegação de página inicial/categorias mantém o idioma.
   Não inventar novas categorias para obter volume.
4. **Medição:** o painel já possui leitor de dados Search Console através do
   Windsor.ai; a conexão OAuth da propriedade `sc-domain:lowcost-europa.eu`
   **ainda não está comprovada**. Somente após o titular autenticar e
   o conector confirmar a propriedade, executar o sincronizador `--dry-run`,
   permitir snapshots no ambiente privado e verificar cliques, impressões,
   CTR e posição verdadeiros. Não confundir com cliques afiliados.
5. **Expansão:** estabilizar PT/ES com dados reais de pesquisa e conversão antes
   de abrir FR/DE/EN. O catálogo de traduções existente pode ser reutilizado
   quando houver conteúdo completo e QA por mercado; nunca gerar páginas
   vazias, traduções parciais ou landing pages em massa.

## Porta operacional

1. Exigir CI, testes unitários específicos, revisão de fonte, migrações sem
   diferenças e QA Playwright em dispositivo mobile emulado + desktop.
2. Verificar na VPS SHA, worktree sem alterações, saúde da BD, Nginx, backups,
   espaço livre e certificados. Fazer backup/rollback privado e não expor
   segredos no GitHub.
3. Implantar por SHA com o **processo autorizado existente**; a nova variável
   `DJANGO_LOCALE_SEO_ENABLED=true` requer ambiente de produção atualizado
   e restart **protegido**, pois HUP não relê variáveis de ambiente.
4. Comparar 11 URLs originais, os 12 novos URLs, 200, canonicals exatos,
   3 alternates por página, `<html lang>`, rastreabilidade, robots, JSON-LD,
   pesquisa, painel privado, `/go/`, cinco categorias, 404 com flag desligada,
   TLS e redirecionamentos raiz/WWW. Testar browsers com IP de PT e ES;
   as páginas explícitas devem ignorar GeoIP e cookies.
5. Validar a sitemap final e o estado IndexNow antes/depois; não fazer envios
   duplicados de páginas antigas. O IndexNow existente poderá notificar apenas
   URLs novos/alterados na próxima execução natural.
6. Conferir novamente métricas em Search Console/Bing **sem** prometer
   indexação imediata ou rankings. Se qualquer porta falhar, regressar à
   configuração anterior, mantendo URLs originais e backups.

O serviço de DNS, e-mail na Dynadot, domínio canónico WWW, propriedade do
Search Console, chaves IndexNow, dados comerciais e outros projetos não fazem
parte da alteração. A ativação externa e a proteção da `main` exigem
autorização/controlo administrativo no respetivo fornecedor.
