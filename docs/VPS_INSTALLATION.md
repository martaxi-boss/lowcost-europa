# Low Cost Europa — instalacao VPS Ubuntu

## Identidade e estado observado
- GitHub: `martaxi-boss/lowcost-europa`.
- Aplicacao atual **fisicamente** em `/srv/projects/lowcost-europa` (nome igual ao repositorio). O antigo `/srv/lowcost-europa` e um symlink temporario de compatibilidade para os servicos e scripts existentes.
- Servico: `lowcost-europa.service`, observado `active` em 03/11/2026.
- Dependencias Python do projeto: `/srv/projects/lowcost-europa/.venv` (aprox. 82,7 MB).
- Arquivo antigo de utilizador administrativo consolidado em `/srv/projects/lowcost-europa/archive/migration-preserved/home-lowcost-admin` (40 960 bytes); antes em `/root/migration-preserved/home-lowcost-admin`.

## Componentes ainda externos (pendente)
- Dados operacionais: `/var/lib/lowcost-europa`.
- Configuracoes privadas: `/root/project-secrets/lowcost-europa`.
- Ficheiros web: `/var/www/lowcost-europa`.
- Unidade `systemd`, configuracao Nginx e tarefas agendadas de manutencao, relatorios, descoberta e backups, associadas ao projeto.
- A release local nao coincide necessariamente com o commit `main` atual. Nao substituir sem auditar o diff e os dados.

Arquivos gerados, bases de dados e segredos ficam fora do GitHub; a pasta `archive/` e ignorada. A migracao destes dados externos para dentro do projeto ainda nao foi realizada.

## Objetivo e desinstalacao
O codigo foi movido fisicamente para a instalacao canonica `/srv/projects/lowcost-europa/` (117 411 840 bytes, sem libertacao de espaco). Atualizar ainda os caminhos do servico, proxy, backups, dados e segredos, depois remover a ligacao antiga com preservacao e testes de leitura. Considerar a desinstalacao apenas apos parar os seus servicos, exportar/restaurar dados e retirar referencias exclusivas, sem tocar nos servicos partilhados.

Provas: [auditoria de servicos #41704932726](https://github.com/martaxi-boss/VPS/actions/runs/41704932726), [consolidacao de arquivo #41707116287](https://github.com/martaxi-boss/VPS/actions/runs/41707116287).

## Migracao fisica validada

O primeiro teste de mudanca falhou na verificacao Git e foi revertido; a causa era a identidade usada na consulta do repositorio no novo caminho. A execucao repetida como conta proprietaria concluiu sem mudanca de conteudo Git e preservou o PID do servico Low Cost (293428), os outros servicos e ambos os robos Telegram. [Prova real #41709236022](https://github.com/martaxi-boss/VPS/actions/runs/41709236022).

O caminho antigo continua como symlink de compatibilidade; a migracao nao esta certificada para desinstalacao ate atualizar as referencias systemd, backups e tarefas agendadas.
