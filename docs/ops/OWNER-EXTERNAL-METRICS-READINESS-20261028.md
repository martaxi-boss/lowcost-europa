# Low Cost Europa — monitorização de encomendas e publicidade no painel privado

## Âmbito e dados verificados

A função `/painel/` continua protegida por login de administrador e apresenta apenas agregados verificados. Sem scripts no site público, pixels Meta, cookies novos, indexação Google, alteração de campanha ou publicação de produtos.

**AliExpress:** consulta oficial `aliexpress.affiliate.order.list` para a conta já configurada, dois estados documentados (`Payment Completed` e `Buyer Confirmed Receipt`), até 30 dias. O método devolve `resp_code=405` para uma pesquisa vazia; aceitar como **sem resultados** apenas quando a mensagem indicar ausência de resultados. Erros, payloads incompletos e limites de paginação interrompem a sincronização. Não produzir totais parciais. A consulta distingue `lowcost_europa`, `default`, `meus_links` e outros IDs, inclusive para links manuais.

**Comissão:** fonte é AliExpress. Valores apresentados são **estimativas**, nunca dinheiro liquidado; agrupados por moeda de liquidação, sem conversão artificial. Inteiros monetários devolvidos pelo fornecedor representam unidades mínimas (centavos); decimais/string decimais representam unidades monetárias. Compras com `FullRefund`/`Antispam`/`Invalid` não contam para totais positivos. Identificadores de encomendas só são usados em memória para deduplicação; a base de dados guarda um único JSON agregado e datas, sem identificação de comprador, moradas ou artigos individuais. O clique de saída na loja não comprova compra atribuída.

**Meta:** adaptador read-only Graph Marketing API `v26.0` (preferencial) ou via API do Windsor.ai com a conta Meta já autorizada, relatório de conta para gastar/impressões/cliques/alcance. A conta e a moeda são confirmadas por uma consulta autenticada antes de admitir insights. A credencial de servidor tem de dispor de `ads_read` e acesso à conta exata. Requer `META_AD_ACCOUNT_ID` e **uma** das credenciais `META_ACCESS_TOKEN` ou `WINDSOR_API_KEY` no ficheiro de segredos VPS preexistente, nunca no GitHub; os tokens nunca são passados à página nem aos logs. Embora exista uma ligação no Windsor.ai/ChatGPT, **essa sessão não disponibiliza automaticamente credenciais persistentes ao servidor**. Sem ambas as variáveis, o comando deixa a fonte Meta pendente e não inventa gastos iguais a zero.

## Operação

- `python manage.py sync_affiliate_orders --days 30 --dry-run`: diagnostica a AliExpress sem escrever na base.
- `python manage.py sync_meta_ads --dry-run`: só com token Meta presente e validado.
- `python manage.py sync_external_metrics --dry-run`: testa ambas (Meta sem credenciais é saltado com aviso explícito).
- `python manage.py sync_external_metrics`: atualiza os agregados após consulta completa.
- Unidade `lowcost-europa-affiliate-report.service` e timer de seis em seis horas, no mesmo servidor e com o mesmo utilizador restrito que já opera Lowcost Europa. São tarefas systemd simples, não novos motores, MCPs, containers ou servidores.

## Regras de segurança e falha

1. Verificar backup local e offsite, código exato e migrações antes de instalar a tabela agregada.
2. Alterar/arrancar apenas serviço e timer **Low Cost Europa**, sem tocar nos outros projetos.
3. A página `/painel/` nunca faz chamadas externas nem provoca compras ou cliques de teste.
4. Erro de API não sobrescreve a última consulta bem-sucedida; o Resumo marca como **desatualizados** valores com mais de 12 horas.
5. Informações Meta e AliExpress não são somadas entre si nem convertidas em receita atribuída aos anúncios.
6. Não guardar tokens em logs, documentação, GitHub ou resultados CI.
7. Se a fonte Meta requerer novo consentimento, a autorização deve ocorrer nos canais oficiais da plataforma e o segredo ser guardado diretamente na VPS.
8. Indexação, domínio definitivo, Google Analytics e publicidade comercial ficam fora do âmbito desta tarefa.

## Testes

Testes unitários verificam `405` vazio vs falha, bloqueio de resultados incompletos, deduplicação, diversidade de Tracking IDs e moedas, exclusão de reembolsos, persistência atómica, ausência de API em GET, dados desatualizados, permissão da área privada e credenciais Meta ausentes.

### Opção Windsor.ai já ligada no ChatGPT

A conta Meta `LOW COST` está associada ao Windsor.ai. Para sincronização automática fora do ChatGPT basta uma chave de API **da própria conta Windsor.ai** e o ID exato da conta de anúncios, guardados apenas no cofre da VPS. Em Windsor.ai, abrir **Settings → API Access**, localizar a chave e autorizar o seu armazenamento no cofre existente; nunca a enviar por chat. Não é necessário criar uma aplicação Meta adicional. A conta precisa manter-se autorizada no Windsor.ai.

O conector de Windsor requer `api_key` num **URL HTTPS** (não aceita cabeçalhos de autorização). O código usa exclusivamente o endpoint de leitura `connectors.windsor.ai/facebook`, valida a identidade da conta antes de obter dados e **não regista URLs nem mensagens brutas de exceção**. Os segredos nunca são apresentados na interface nem em logs. Cada consulta fica limitada à conta selecionada com `select_accounts`. Se a ligação ao fornecedor for interrompida, o último relatório válido permanece e passa a ser marcado como desatualizado após 12 horas.

No painel, **«Autorização da VPS necessária»** permanece visível enquanto o servidor não obtiver dados reais. Não lançar campanhas, recolher eventos públicos ou alterar orçamento nesta fase.
