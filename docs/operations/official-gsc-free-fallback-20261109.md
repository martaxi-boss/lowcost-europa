# Google Search Console — alternativa gratuita oficial (9/11/2026)

## Objetivo e segurança

A API oficial Google Search Console pode substituir o Windsor.ai para **métricas
orgânicas Google** sem serviço de subscrição adicional. O código não cria contas,
não subscreve planos nem efetua login no navegador. Usa apenas o endpoint
`searchAnalytics.query` e a propriedade **exata**
`sc-domain:lowcost-europa.eu`. Não recebe nem guarda informações individuais de
visitantes, cookies, IPs ou identificadores de compradores.

A integração Windsor existente **permanece ativa por omissão**. Nenhuma mudança
automática ocorre durante erros de autorização ou no fim do período trial.

## Preparação independente da conta Windsor

O proprietário deve autorizar uma aplicação OAuth Google com acesso de **leitura**:

- API Google Search Console habilitada num projeto Google Cloud controlado pelo
  proprietário; sem faturação obrigatória para este uso sujeito a quotas;
- OAuth consentimento autorizado pelo titular da propriedade;
- escopo exclusivo `https://www.googleapis.com/auth/webmasters.readonly`;
- acesso offline e refresh token válido. Aplicações OAuth ainda em Testing podem
  ter refresh tokens de curta duração: verificar a configuração de publicação do
  consentimento antes de depender de tarefas agendadas.

A autorização concedida ao Windsor.ai **não transfere** o seu refresh token para
a aplicação; nunca tentar extraí-lo de uma sessão ou da ferramenta de terceiros.

No ambiente **privado** já utilizado por systemd no projeto Lowcost Europa:

```text
GOOGLE_SEARCH_CONSOLE_PROPERTY=sc-domain:lowcost-europa.eu
GOOGLE_SEARCH_CONSOLE_PROVIDER=GOOGLE_OFFICIAL
GOOGLE_OAUTH_CLIENT_ID=<guardar-privadamente>
GOOGLE_OAUTH_CLIENT_SECRET=<guardar-privadamente>
GOOGLE_OAUTH_REFRESH_TOKEN=<guardar-privadamente>
```

Nunca colocar os valores no GitHub, CI, logs, tickets, ChatGPT ou documentação.
Manter o `WINDSOR_API_KEY` privado até o primeiro relatório oficial ser
comprovadamente recolhido e guardado; depois o proprietário decide desativar
o fornecedor antigo.

## Teste e passagem controlada

1. Preservar cópia do ficheiro de configuração e snapshot anterior.
2. Sem alterar produção, testar sinteticamente o adaptador no CI.
3. Com OAuth autorizado, executar na VPS **na pasta do projeto** o comando
   `python manage.py sync_google_search_console --dry-run`: leitura real, sem
   gravação de base de dados.
4. Se a leitura devolver dados válidos, executar
   `python manage.py sync_google_search_console` através do fluxo operacional
   já autorizado, preservando o reporte anterior em caso de erro.
5. Confirmar no painel staff-only a propriedade e a data da sincronização.
   O comando `sync_external_metrics` existente mantém a cadência normal
   e nenhuma tarefa nova é criada.
6. Verificar a disponibilidade e a renovação do token antes do fim do trial
   Windsor; o prazo documentado para esse trial era 19/11/2026.

Se o Google devolver `rows=[]`, o estado será **AWAITING_DATA**, não zero
cliques. Em falhas do OAuth ou de identidade, a sincronização falha
explicitamente; não elimina o último snapshot. As métricas usam 30 dias
completos, terminados três dias antes da leitura para evitar dias recentes
incompletos. A Google pode omitir consultas raras, limitar as linhas
disponibilizadas e atualizar dados retroativamente.

## Limites

Search Console mede impressões, cliques orgânicos e posição média na pesquisa
Google. **Não** prova inclusão das 23 URLs no índice nem associa campanhas
pagas a vendas/comissões. O relatório AliExpress de encomendas é agregado por
Tracking ID, separado dos cliques de saída. Não prometer atribuição de compra a
campanha sem identificador autorizado que conste em ambos os lados.

Nenhum script de migração, pixel público, tabela nova, API paga, fluxo OAuth
num endpoint do site, serviço systemd novo ou alteração de DNS é necessário.

Documentação oficial:
- https://developers.google.com/webmaster-tools/v1/searchanalytics/query
- https://developers.google.com/webmaster-tools/v1/how-tos/authorizing
- https://developers.google.com/identity/protocols/oauth2/web-server
