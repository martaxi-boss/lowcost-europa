# Low Cost Europa — Google Search Console no painel privado

## Estado antes da integração (08/11/2026)

O painel `/painel/` tinha uma secção estática "Google Search Console — após domínio definitivo". As métricas reais de `OfferClick` contabilizam somente cliques de saída `/go/` para produtos. Não medem entradas orgânicas oriundas da pesquisa Google.

A propriedade **`sc-domain:lowcost-europa.eu`** já foi validada e foram observadas seis URLs indexadas. O Search Console de uma conta privada está autenticado via Work/Google, mas **essa sessão não autoriza automaticamente uma ligação persistente da VPS à API**.

A VPS já dispõe de `WINDSOR_API_KEY` no ficheiro de ambiente privado e do timer de relatórios externos existente. O conector Google Search Console do Windsor.ai, porém, não tinha nenhuma propriedade ligada à conta do utilizador na auditoria de 08/11 às 01:07.

## Implementação

- Fonte separada `GOOGLE_SEARCH_CONSOLE` na tabela `ExternalMetricsSnapshot` **já existente**. Sem novas migrações, tabelas, serviços, servidores, pixels ou cookies.
- O comando `python manage.py sync_google_search_console` consulta por HTTPS apenas o conector **Search Console** do Windsor.ai, no modo de leitura, condicionado a `GOOGLE_SEARCH_CONSOLE_PROPERTY=sc-domain:lowcost-europa.eu` e à chave privada `WINDSOR_API_KEY`.
- O comando agregado `sync_external_metrics` integra a nova fonte **apenas** quando a propriedade tiver sido autorizada explicitamente no ambiente. As fontes AliExpress e Meta mantêm leitura e funcionamento independentes.
- No painel privado, métricas reais de **cliques orgânicos Google, impressões, CTR e posição média nos últimos 30 dias**. Principais pesquisas até 10, sem somar os subtotais às métricas gerais; consultas raras podem ser omitidas pelo Google. Os números provêm exclusivamente de uma leitura verificada da propriedade correta.
- Sem autorização, sem dados ou em caso de falha, mostrar **pendente/indisponível**; nunca inventar zero. Em caso de falha preservar o último snapshot e marcar desatualizado após 48h. O GET do painel nunca chama a API externa.
- O painel continua staff-only, `noindex`, `private,no-store`. Não acrescentar analytics público nem enviar dados pessoais de visitantes à API.

## Ativação restante (ligação OAuth oficial)

1. O titular autoriza **Google Search Console** no Windsor.ai, usando a conta Google que tem acesso a `lowcost-europa.eu`, com permissão de leitura e selecionando especificamente a propriedade `sc-domain:lowcost-europa.eu`.
2. O operador comprova através de uma consulta **de leitura** do próprio conector que essa propriedade consta como ligada. Não inferir autorização de existir uma conta Meta no Windsor.ai.
3. Só depois adicionar `GOOGLE_SEARCH_CONSOLE_PROPERTY=sc-domain:lowcost-europa.eu` ao **ficheiro privado já usado pelo serviço** `/srv/projects/lowcost-europa/private/systemd-env/lowcost-europa.env`. Nunca publicar `WINDSOR_API_KEY` em GitHub, URL de painel, logs ou reports.
4. Executar `python manage.py sync_google_search_console --dry-run`, confirmar identidade e integridade dos valores; executar a versão de escrita e ler o snapshot na BD. Validar o painel staff-only no endereço HTTPS atual.
5. Deixar o timer de métricas **já existente** atualizar o snapshot de 6 em 6 horas. Controlar atrasos e erros sem alterar serviços alheios.
6. Preservar explicitamente os contadores de `OfferClick` separados dos cliques orgânicos Google.

**Sem a etapa OAuth de titular não é correto declarar \"Google ligado\" nem inventar impressões ou cliques.** A Search Console API tem um atraso normal de dados nos últimos dias; não equivale ao Google Analytics 4 nem mede sessões completas do site.

## Segurança e conformidade

- Nenhum identificador de utilizador, cookies ou IPs processados pelo adaptador. Apenas resumos de pesquisa já disponibilizados ao proprietário Google.
- A consulta ao Windsor.ai exige `api_key` no URL de transporte; o processo não imprime o URL nem mensagens de exceção HTTP, e nunca expõe a chave na interface.
- Recusar qualquer linha da API referente a propriedade diferente de `sc-domain:lowcost-europa.eu`. Recusar dados parciais, inválidos e erros de autenticação.
- `--dry-run` só lê, nunca grava `ExternalMetricsSnapshot`. Execução normal usa `update_or_create` atómico.
- Uma nova integração não implica comprar plano pago: aproveitar o acesso já existente se os limites da conta permitirem. Caso contrário, recorrer à API gratuita oficial do Google com credenciais devidamente autorizadas, não a um fornecedOR pago obrigatório.

Referências:
- Google Search Console API: https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- Windsor.ai fields: https://windsor.ai/data-field/searchconsole/
- Operação pré-existente: `docs/ops/OWNER-EXTERNAL-METRICS-READINESS-20261028.md`
