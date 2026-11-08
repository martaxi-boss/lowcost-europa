# Low Cost Europa — higienização canónica de 08/11/2026

**Objetivo:** eliminar resíduos de testes e de domínios de ensaio, manter apenas
a árvore de trabalho ativa e evitar conflitos entre GitHub/VPS. **Não** eliminar
histórico irrecuperável, dados comerciais, backups operacionais, chaves de outros
projetos ou o serviço de DNS/e-mail oficial.

## Fonte única e recursos preservados

- Website canónico: **https://www.lowcost-europa.eu**.
- Domínio raiz: redirecionamento HTTPS 301 para `www`.
- DNS autoritativo e e-mail: **Dynadot**, sem alterações a MX/SPF/DKIM/DMARC,
  certificados ou registos de titularidade do Google.
- Código principal: `martaxi-boss/lowcost-europa`, branch **main**.
- Pasta na VPS: `/srv/projects/lowcost-europa`, independente de Ferrari,
  Pink IPTV, FADEGO, Telegram, outros sites e cofre de segredos.
- Certificado TLS de produção `lowcost-europa.eu`, `certbot.timer` ativo.
- Base de dados, dados editoriais, historial de ofertas, credenciais privadas,
  backups PostgreSQL/offsite e timers de catálogo, descoberta, IndexNow e
  relatórios: **preservados**.

## GitHub — alterações verificadas

- [PR #220](https://github.com/martaxi-boss/lowcost-europa/pull/220):
  removidos da árvore atual os dois *templates* Nginx de teste
  (`deploy/nginx/lowcost-europa.conf` e `lowcost-europa.eu-acme.conf`),
  mantendo `lowcost-europa.eu.conf` como configuração canónica.
- Roteiro de domínio atualizado para a realidade atual; eliminadas as
  instruções transitórias de domínio estacionado e ACME temporário.
- QA externa passou a testar `www`, robots, sitemap, URLs públicas
  indexáveis, painel privado e menus em várias línguas. O teste antigo
  dependente do texto fixo «Produtos» foi corrigido.
- **18 ficheiros históricos de capturas/JSON** retirados da árvore atual.
  Continuam recuperáveis no
  [commit anterior bd25002](https://github.com/martaxi-boss/lowcost-europa/tree/bd25002e619a3f4240b1b4ffe5247ae4a87a67e1/docs/qa).
  Os testes de regressão reais **não foram eliminados**.
- [CI #42439287603](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42439287603):
  **778 testes PASS**.
- [Browser #42439287606](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42439287606):
  **15 verificações PASS**, desktop e mobile emulado, site real.
- [Auditoria de segurança #42439287711](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42439287711):
  **PASS**.
- [Higiene PRs #42439382266](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42439382266):
  **6 branches integradas removidas** com comparação exata do SHA.
- [Arquivo #42439426966](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42439426966):
  **8 branches antigas com commits próprios guardadas em tags**
  `archive/lowcost-20261108/*`, seguidas de eliminação com
  `--force-with-lease`. **Resultado: apenas main**, sem PR aberta.
- Workflows temporários de arquivo removidos depois da execução.

## VPS — alterações reais e recuperação

- [Inventário inicial #42438550280](https://github.com/martaxi-boss/VPS/actions/runs/42438550280):
  código limpo/alinhado, projeto com ~133 MiB; mais de 33 GiB livres
  no volume e os serviços essenciais ativos.
- [Auditoria de consumidores #42439164984](https://github.com/martaxi-boss/VPS/actions/runs/42439164984):
  o legado DuckDNS permanecia somente na configuração de teste do Nginx e
  nas variáveis `DJANGO_ALLOWED_HOSTS`/`DJANGO_CSRF_TRUSTED_ORIGINS`.
- [Higiene aplicada #42439717221](https://github.com/martaxi-boss/VPS/actions/runs/42439717221):
  código sincronizado com GitHub, vhost de ensaio removido,
  hosts CSRF/allowed obsoletos removidos, backup privado feito,
  **15 diretórios de cache Python removidos**.
  Tamanho medido **136520 KiB → 132168 KiB** (redução **4352 KiB**).
  WWW/apex, cinco categorias, privacidade do painel, sitemap, indexação,
  Nginx e quatro timers: **PASS**. Vhosts FADEGO e Pink preservados.
- As tentativas de rollout anteriores que falharam tiveram **rollback**
  ou `MUTATIONS=NONE`; não apagar as respetivas provas.
- [Certificados de teste #42439829660](https://github.com/martaxi-boss/VPS/actions/runs/42439829660):
  retirados pelo Certbot apenas `lowcost-europa.duckdns.org`,
  `lowcost-europa.146-59-145-3.sslip.io` e
  `lowcost-europa.165-22-114-67.sslip.io`, após confirmação de
  **zero consumidores ativos**. Certificado oficial, renovação e
  todos os outros certificados: **preservados**.
  Arquivo de recuperação privado com permissões restritas.
- A ausência de DNS antigo na aplicação **não** é autorização para apagar
  o DNS Dynadot, SPF, DKIM, MX, DMARC, certificados oficiais ou a chave
  IndexNow.

## Ferrari — auditoria independente

[Inventário real Ferrari #42439335006](https://github.com/martaxi-boss/VPS/actions/runs/42439335006):
`FERRARI_SKILL_JOB_STATUS=completed`,
`FERRARI_SKILL_END_TO_END=PASS` e `response.zip` com
`report.json.status=completed`, `catalog.json` e `inventory.json`.
Catálogo único de **450 entradas**, **55/55 programas selecionados** e
**40/40 ações disponíveis** no instantâneo. Esta prova verifica o motor
Ferrari **separadamente**; a limpeza Low Cost foi implantada através do
workflow GitHub→VPS próprio, e não como uma ação de limpeza Ferrari.

## Regras de manutenção futuras

1. Publicar código apenas após testes e revisão na `main`; não restaurar
   branches antigas nem reativar domínios de teste.
2. Manter o workflow de remoção de branches apenas para PRs **realmente
   integradas**, com SHA verificado, sem PR aberta e com lease.
3. Não eliminar testes automatizados atuais. Guardar screenshots, relatórios
   volumosos e logs de execução em artefactos de retenção curta; conservar
   apenas provas essenciais em texto na árvore Git.
4. Não fazer `git clean -fdx`, `apt autoremove`, `rm -rf` genérico,
   purga de bases de dados, certificados de outros sites ou backups.
5. Se uma limpeza exigir remoção de serviço, executar pré-auditoria de
   consumidores, cópia de recuperação, alteração limitada, teste HTTP,
   prova de SHA e readback final.
6. **A validação comercial não está 100% concluída:** a API afiliada
   não fornece prova de stock por SKU nem de todas as origens/prazos.
   Manter «por confirmar» até existir evidência, sem fabricar dados.

Os workflows pontuais da VPS são eliminados após cada execução concluída;
a prova fica no histórico de GitHub Actions, e os backups ficam privados
dentro da pasta do projeto.
