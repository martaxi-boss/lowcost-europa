# Low Cost Europa — reporting privado sem Meta Ads

## Estado atual e limite

A decisão do proprietário em 09/11/2026 foi **retirar integralmente o Meta Ads do projeto Low Cost Europa**, incluindo dados herdados da conta publicitária «Sérgio Almeida». Não configurar uma conta Meta de substituição automaticamente.

O painel `/painel/` é privado: apenas métricas de saída para parceiros, pesquisa Google (quando disponíveis) e informação de comissões da AliExpress. A gestão de ofertas permanece na Loja, não no Resumo.

## Fontes autorizadas

- **AliExpress:** a consulta oficial de encomendas por Tracking ID conserva os controlos de deduplicação, estados, moeda e exclusões; comissões são estimativas, nunca dinheiro recebido.
- **Google Search Console:** propriedade `sc-domain:lowcost-europa.eu`, através do conector Windsor.ai da conta autorizada pelo proprietário; a existência da ligação não garante ainda linhas de dados. Apenas relatório verificável entra no painel.
- **Meta/Facebook Ads:** fonte **desligada por decisão do proprietário**. O comando `sync_meta_ads` permanece como bloqueio de compatibilidade e falha sempre com `META_REPORT=DISABLED_BY_OWNER`, sem chamadas externas. O comando agregado `sync_external_metrics` nunca chama Meta.

## Higienização de configurações e dados

- `META_AD_ACCOUNT_ID` e `META_ACCESS_TOKEN` **não pertencem** ao ambiente privado Low Cost Europa; eliminá-los do ficheiro existente com backup e rollback, sem revelar valores em logs.
- Não remover `WINDSOR_API_KEY` indiscriminadamente, pois é a credencial de servidor utilizada pelo Search Console. A credencial existente pode corresponder à conta Windsor antiga: confirmar a origem da chave antes de trocar para a nova conta, e nunca colocar a chave no chat ou GitHub.
- A migração `0021_purge_disconnected_meta_snapshot` remove **só** a linha `ExternalMetricsSnapshot(source="META")`. Não afeta `GOOGLE_SEARCH_CONSOLE`, `ALIEXPRESS`, produtos ou cliques locais. Fazer cópia PostgreSQL verificada antes de migrar; os backups históricos conservam a informação até ao fim da retenção.
- Revogar um conector na conta Windsor antiga é uma operação separada de administração de conta, que requer confirmação do fornecedor. Não confundir com apagar contas ou campanhas na própria plataforma Meta.

## Segurança e operação

1. Validar `main`, estado do serviço e backup/rollback do projeto.
2. Efetuar apenas deploy Low Cost Europa pelos mecanismos autenticados e autorizados; nunca alterar outros projetos da VPS.
3. Aplicar migrações depois do backup, limpar configuração Meta e confirmar reinício/reload do serviço.
4. Verificar painel sem referências a anúncios, nomes de anunciantes ou dados Meta; testar que o comando Meta falha fechado.
5. Manter `sync_external_metrics` com fontes AliExpress e Google, separado de cliques locais. Qualquer erro não gera zeros inventados.
6. Confirmar HTTP público, proteção de `/painel/`, timers e métricas existentes.
7. Não publicar segredos, chaves, tokens ou dados da conta externa em relatórios públicos.

Este documento substitui as instruções antigas de ativação Meta de 28/10/2026.
