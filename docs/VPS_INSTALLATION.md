# Low Cost Europa — instalacao VPS Ubuntu

## Identidade e estado observado
- GitHub: `martaxi-boss/lowcost-europa`.
- Aplicacao atual: `/srv/lowcost-europa` (nome igual ao repositorio).
- Servico: `lowcost-europa.service`, observado `active` em 03/11/2026.
- Dependencias Python do projeto: `/srv/lowcost-europa/.venv` (aprox. 82,7 MB).
- Arquivo antigo de utilizador administrativo consolidado em `/srv/lowcost-europa/archive/migration-preserved/home-lowcost-admin` (40 960 bytes); antes em `/root/migration-preserved/home-lowcost-admin`.

## Componentes ainda externos (pendente)
- Dados operacionais: `/var/lib/lowcost-europa`.
- Configuracoes privadas: `/root/project-secrets/lowcost-europa`.
- Ficheiros web: `/var/www/lowcost-europa`.
- Unidade `systemd`, configuracao Nginx e tarefas agendadas de manutencao, relatorios, descoberta e backups, associadas ao projeto.
- A release local nao coincide necessariamente com o commit `main` atual. Nao substituir sem auditar o diff e os dados.

Arquivos gerados, bases de dados e segredos ficam fora do GitHub; a pasta `archive/` e ignorada. A migracao destes dados externos para dentro do projeto ainda nao foi realizada.

## Objetivo e desinstalacao
A instalacao canonica pretendida e `/srv/projects/lowcost-europa/`. Atualizar os caminhos do servico, proxy, backups, dados e segredos com preservacao e testes de leitura. Considerar a desinstalacao apenas apos parar os seus servicos, exportar/restaurar dados e retirar referencias exclusivas, sem tocar nos servicos partilhados.

Provas: [auditoria de servicos #41704932726](https://github.com/martaxi-boss/VPS/actions/runs/41704932726), [consolidacao de arquivo #41707116287](https://github.com/martaxi-boss/VPS/actions/runs/41707116287).
