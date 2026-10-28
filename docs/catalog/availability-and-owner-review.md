# Lowcost Europa — disponibilidade e revisão privada

Atualização técnica 2026-10-28, REA 6.8.0. Mantém a Constituição Operacional do Catálogo.

## Monitorização de anúncios AliExpress

- Mantém o timer horário, lote limitado, lock global e limites de chamadas existentes. Em lotes de 3 ou mais, reserva aproximadamente 60% das verificações a ofertas elegíveis para a montra e 40% às demais ofertas ativas; vagas não utilizadas são redistribuídas. Para lotes de 1–2, a ordem continua estritamente cronológica. Ofertas inativas não são reativadas.
- A API de detalhe pode devolver ID, título, URL e preço sem devolver **prova de disponibilidade**. Essa resposta cria uma observação `UNKNOWN`, com dados factuais fornecidos, nunca uma confirmação de stock inventada.
- `AVAILABLE` requer indicação explícita `available` ou `in stock` no estado normalizado. Mesmo esse estado não prova inventário de todas as variantes/SKU ou de um armazém de origem específico.
- `unavailable`, `removed`, `out of stock`, `sold out` e equivalentes inequívocos de estado do produto originam desativação de anúncio. Erros transitórios, ausência de estado e dados de detalhe incompletos não são prova de indisponibilidade; são `UNKNOWN` e não desativam.
- Registos factuais de preço, logística e comissão obtidos num detalhe sem estado positivo são preservados como observações, sem inventar uma conclusão sobre o stock. O relatório da manutenção agora separa `Availability unknown (valid detail)` dos erros transitórios.
- O filtro da montra e `/go/` mantém a política pública anterior. Estado `UNKNOWN` não foi promovido a causa de exclusão automática. Não há garantia de que a API oficial de afiliados devolva inventário por SKU ou origem de armazém.

## Fila A rever

- A gestão privada integrada na página de cada família mostra quando a fila tem 20 ou mais candidatos pendentes. Indica o número mínimo de decisões humanas necessárias para baixar abaixo de 20 e permitir nova pesquisa semanal.
- Permite ordenar por última observação: `antigos` ou `recentes`. Para filas bloqueadas, a ordenação predefinida passa a `antigos`, sem modificar os candidatos.
- Nenhum candidato é aprovado, rejeitado, eliminado, ocultado, publicado ou movido pela ordenação ou pelo aviso. Os dados de gestão permanecem privados e não são expostos no HTML entregue a visitantes públicos.
- O proprietário mantém a obrigação de abrir o anúncio real e confirmar entrega em Portugal e origem `PL`, `CZ`, `FR`, `ES` ou `DE`. Desconhecido não é aprovação.

## Restrições invariantes

Não altera o limite de 20 ofertas públicas por família, o limite de 20 candidatos pendentes para descoberta, o protocolo de aprovação/revalidação, o momento de gerar primeiro link afiliado, as políticas de API, a indexação pública ou o lançamento comercial. Domínio DuckDNS apenas para testes.

Mudanças a classificações de disponibilidade ou à prioridade da verificação exigem regressão automatizada, auditoria factual do REA e aprovação de rollout exato; nunca se pode interpretar um mero sucesso de CI como confirmação de stock de um vendedor.
