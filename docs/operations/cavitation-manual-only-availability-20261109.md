# Cavitação — montra manual e proteção de indisponibilidade (09/11/2026)

## Fonte de verdade da montra

Somente os produtos de `Offer.Source.ALIEXPRESS_OWNER` publicados explicitamente
pelo proprietário aparecem na montra `cavitacao-rf-vacuum-corpo`. Os 17 links
originais foram publicados e verificados na execução
[VPS #42700105054](https://github.com/martaxi-boss/VPS/actions/runs/42700105054)
sem regeneração. O limite global continua a ser 20 produtos por categoria.

Na categoria Cavitação, os interfaces privados
`/painel/familias/cavitacao-rf-vacuum-corpo/` e a página pública quando o
proprietário está autenticado mostram **MONTRA** e
**ELIMINAR DA MONTRA** com uma segunda confirmação explícita.
O POST protegido por autenticação staff e CSRF usa o serviço de ocultação
editorial existente. O link original e os dados de cliques ficam preservados,
mas a oferta deixa de ser pública e `/go/<id>/` deixa de encaminhar.

As rotas históricas de rever, aprovar, rejeitar, revalidar, mover e
publicar gerando um link devolvem HTTP 403 **apenas para esta categoria**.
A descoberta semanal mantém a categoria no relatório histórico, mas não
faz pesquisa nem cria candidatos novos para Cavitação. A manutenção
de ofertas automáticas `ALIEXPRESS` exclui os produtos históricos ligados
a esta categoria; os produtos `ALIEXPRESS_OWNER` já estavam excluídos.
As outras quatro categorias mantêm a lógica e painel anteriores.

## Único automatismo permitido: indisponibilidade

O serviço privado `lowcost-europa-cavitation-availability.service` corre
através de um horário systemd calendar explícito, nas horas UTC pares (com atraso aleatório de até 15 min).
Verifica **no máximo 5** ofertas manuais/publicadas por execução em ordem
da verificação mais antiga (17 produtos = cobertura rotativa).
Usa exclusivamente o método AliExpress de **detalhes** do produto; nunca
chama a geração de links, não publica novos produtos nem modifica
`affiliate_url`, títulos, imagens ou preços.

Uma oferta sai da montra somente se houver **duas verificações consecutivas**
com indicações explícitas de indisponibilidade (estado de anúncio como
`offline`, `unavailable`, `out of stock`, `removed` ou erro oficial
específico `product does not exist`) separadas por **pelo menos 3 horas**,
e não mais de 7 dias. Marca `owner_hidden=True` e `is_active=False`, sem
apagamento de dados. A oferta não volta automaticamente à montra.
Observações `UNKNOWN`, erros de rede, problemas de autenticação, API 429,
falta de informação de stock ou discordância de ID **não são prova**
de indisponibilidade e não provocam remoção.

**Limitação real:** a API de afiliados pode não disponibilizar o estado de
stock/variante. Nesses casos a verificação não pode certificar disponibilidade
nem detetar todos os anúncios removidos; não deve alegar 100% de cobertura.
O monitor regista quantidade de verificações, estados inconclusivos e remoções.
A atribuição de comissões continua a depender do portal AliExpress.

## Requisitos de implementação na VPS

Não ativar timer apenas porque estes ficheiros estão no GitHub.
Após CI e deploy de código exato, instalar os dois systemd units no
diretório próprio de serviços do projeto, validar o conteúdo com os
ficheiros versionados, `systemctl daemon-reload`, habilitar somente o
timer específico e executar uma verificação real sem apagar os 17 produtos
por respostas ambíguas. Confirmar `systemctl list-timers`, SHA do código,
URLs públicos PT/ES, 17 `/go/` e todos os serviços prévios.
Preservar env, segredos, backup e projetos vizinhos.
