# Low Cost Europa — instalacao VPS Ubuntu

## Identidade e estado observado
- GitHub: `martaxi-boss/lowcost-europa`.
- Aplicacao atual **fisicamente** em `/srv/projects/lowcost-europa` (nome igual ao repositorio). O antigo `/srv/lowcost-europa` e um symlink temporario de compatibilidade para os servicos e scripts existentes.
- Servico: `lowcost-europa.service`, observado `active` em 03/11/2026.
- Dependencias Python do projeto: `/srv/projects/lowcost-europa/.venv` (aprox. 82,7 MB).
- Arquivo antigo de utilizador administrativo consolidado em `/srv/projects/lowcost-europa/archive/migration-preserved/home-lowcost-admin` (40 960 bytes); antes em `/root/migration-preserved/home-lowcost-admin`.

## Componentes ainda externos (pendente)
- Dados operacionais: `/srv/projects/lowcost-europa/data` (a antiga `/var/lib/lowcost-europa` e agora ligacao temporaria).
- Configuracoes privadas: `/srv/projects/lowcost-europa/private` (o antigo caminho de segredos e agora ligacao temporaria).
- Ficheiros web: **movidos fisicamente** para `/srv/projects/lowcost-europa/www`; `/var/www/lowcost-europa` e apenas um symlink temporario usado pela configuracao Nginx antiga.
- Unidade `systemd`, configuracao Nginx e tarefas agendadas de manutencao, relatorios, descoberta e backups, associadas ao projeto.
- A release local nao coincide necessariamente com o commit `main` atual. Nao substituir sem auditar o diff e os dados.

Arquivos gerados, bases de dados e segredos ficam fora do GitHub; a pasta `archive/` e ignorada. Os dados operacionais e a pasta privada foram consolidados fisicamente em 04/11/2026. Os ficheiros web ja estavam consolidados. Ainda existem referencias de compatibilidade que exigem cutover e testes.

## Objetivo e desinstalacao
O codigo foi movido fisicamente para a instalacao canonica `/srv/projects/lowcost-europa/` (117 411 840 bytes, sem libertacao de espaco). A unidade `lowcost-europa.service` ja utiliza `/srv/projects/lowcost-europa` (configuracao systemd validada e recarregada sem reinicio). Faltam o proxy, backups, dados e segredos, a validacao de um reinicio e a eliminacao da ligacao antiga. Considerar a desinstalacao apenas apos parar os seus servicos, exportar/restaurar dados e retirar referencias exclusivas, sem tocar nos servicos partilhados.

Provas: [auditoria de servicos #41704932726](https://github.com/martaxi-boss/VPS/actions/runs/41704932726), [consolidacao de arquivo #41707116287](https://github.com/martaxi-boss/VPS/actions/runs/41707116287).

## Migracao fisica validada

O primeiro teste de mudanca falhou na verificacao Git e foi revertido; a causa era a identidade usada na consulta do repositorio no novo caminho. A execucao repetida como conta proprietaria concluiu sem mudanca de conteudo Git e preservou o PID do servico Low Cost (293428), os outros servicos e ambos os robos Telegram. [Prova real #41709236022](https://github.com/martaxi-boss/VPS/actions/runs/41709236022).

O caminho antigo continua como symlink de compatibilidade; a migracao nao esta certificada para desinstalacao ate atualizar as referencias systemd, backups e tarefas agendadas.

## Ambiente Python e unidade systemd

Seis scripts do venv (incluindo `gunicorn` e `pip`) foram atualizados para `/srv/projects/lowcost-europa`, com testes CLI positivos e Git intacto. [Execucao #41716321831](https://github.com/martaxi-boss/VPS/actions/runs/41716321831). Unidade systemd recarregada com o caminho canonico, processo PID 293428 sem reinicio. [Prova #41716531862](https://github.com/martaxi-boss/VPS/actions/runs/41716531862).

## Migracao fisica do diretorio web publico — 04-11-2026

O diretorio `/var/www/lowcost-europa` foi movido fisicamente, no mesmo filesystem, para `/srv/projects/lowcost-europa/www`, com preservacao de inode, UID, GID e conteudo. O caminho externo ficou como symlink temporario para que a configuracao Nginx ainda funcional nao falhe durante a transicao.

O teste real [GitHub Actions #41750334632](https://github.com/martaxi-boss/VPS/actions/runs/41750334632) terminou com **MOVED_AND_VERIFIED**: `nginx -t` passou, o utilizador `www-data` manteve acesso ao diretorio de conteudo e os servicos protegidos permaneceram com estado igual. Nao foram movidas bases de dados, segredos ou configuracoes privadas. O rename nao liberta espaco no disco.

**Ainda pendente:** migrar as referencias Nginx de `/var/www/lowcost-europa` para `/srv/projects/lowcost-europa/www`, validar HTTP/HTTPS e reinicio, e so depois remover o symlink antigo. Permanecem em aberto os dados proprios em `/var/lib/lowcost-europa` e configuracoes privadas externas. Nao considerar a desinstalacao autonoma totalmente certificada.

## Consolidacao de dados e segredos — 04-11-2026

O motor Ferrari/REA, via [Actions #41751694306](https://github.com/martaxi-boss/VPS/actions/runs/41751694306), confirmou `MOVED_VERIFIED` para os dois diretórios: `/var/lib/lowcost-europa` mudou fisicamente para `data/` e `/root/project-secrets/lowcost-europa` para `private/`. As propriedades, modos e inodes foram preservados, sem copiar o conteudo; os caminhos originais ficaram como ligacoes temporarias. Os servicos protegidos mantiveram o estado.

A configuracao ambiental externa em `/etc/lowcost-europa` e os ficheiros de integracao do Ubuntu ainda precisam de auditoria e migracao apropriada. O Nginx precisa apontar para `www/` e os servicos, backups e scripts devem usar os caminhos fisicos novos antes de retirar qualquer alias. Nao declarar desinstalacao completamente independente ate certificar reinicio e ausencia de referencias externas.

## Nginx e ficheiro de ambiente da instalacao — 04-11-2026

A configuracao ativa Nginx foi atualizada para `/srv/projects/lowcost-europa/www`, sem referencias ao antigo `/var/www/lowcost-europa`. A execucao [#41753196864](https://github.com/martaxi-boss/VPS/actions/runs/41753196864) confirmou substituicao de quatro referencias, `nginx -t` positivo, reload valido, servicos preservados e backup dentro da pasta do projeto. O ficheiro versionado `deploy/nginx/lowcost-europa.conf` foi alinhado com os caminhos canonicos, incluindo `staticfiles/`.

A antiga pasta `/etc/lowcost-europa` foi movida fisicamente para `/srv/projects/lowcost-europa/private/systemd-env` com [prova #41753483523](https://github.com/martaxi-boss/VPS/actions/runs/41753483523). Permissoes e inode preservados; a origem continua apenas como alias temporario. O template `deploy/systemd/lowcost-europa.service` aponta para o ficheiro de ambiente interno e para o `gunicorn` do venv do projeto.

O proximo teste deve verificar o `EnvironmentFile` da unidade systemd efetiva e o arranque controlado; so depois e permitido remover o alias `/etc/lowcost-europa`. **Esta documentacao nao equivale a certificacao de reinicio.**
