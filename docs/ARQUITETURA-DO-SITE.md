# LOWCOST EUROPA — Arquitetura do site

Reconciliada com a aplicação `82ff2d68835bf083de3b4da6ce674ae24631b3c5`, 2026-10-03.
Scope técnico aceite: concluído. Estado/autorizações: [PROJECT_STATE.md](../PROJECT_STATE.md).

## Aplicação e operação

Monólito Django 5.2 LTS / Python 3.12 com PostgreSQL e templates no servidor.
HTTPS → Nginx → Gunicorn → Django → PostgreSQL, em OVH, com systemd.
Administração através de workflows GitHub; não reinstalar Desktop Commander ou runners antigos por instruções de fases passadas. Não há rebuild autorizado.

## Catálogo

ProductFamily é permanente; Offer tem identidade global `(source, external_product_id)`.
OfferFamilyPlacement controla a apresentação pública sem duplicar produtos.
OfferObservation, CandidateDecision, CandidateFamilyMoveEvent e OfferClick mantêm factos/histórico.
As cinco famílias operacionais preservam nomes e ordem da base de dados; famílias retiradas ficam no histórico.

Discovery produz apenas candidatos PENDING / A REVER. Owner autenticado aprova/rejeita em `/painel/`.
Approval atesta o protocolo fixo Portugal + origem PL/CZ/FR/ES/DE e verifica a promoção afiliada oficial.
Uma Offer nova fica escondida até publicação humana. Approval não é feedback positivo de ranking.
Rejeições semânticas e movimentos de classificação ficam isolados por família.

## Montra e encaminhamento

Leituras públicas consultam PostgreSQL sem chamar AliExpress.
O gate central em public_eligibility.py exige Offer ativa, editorialmente visível, link afiliado,
promoção ELIGIBLE verificada e protocolo humano não nulo/não futuro.
Não existe expiração de sete dias. Metadados individuais de ship-from são opcionais, nunca inferidos.
Publicação respeita família operacional, placement e cap 20 por família.

Home CTA → `#familias`; compra → `/go/<offer_id>/`, que valida elegibilidade,
regista o clique mínimo e redireciona ao parceiro. Não existe checkout próprio.
WhatsApp → `/contactar/whatsapp/` → número aprovado 351965471236.
Cliques não provam compras ou comissões.

## AliExpress e tarefas

AliExpressClient centraliza signing, HTTP, normalização, lock/cadence, retries,
Retry-After, backoff/jitter e rate-limit breaker.
Discovery semanal: segunda 23:40 UTC, cinco famílias sequenciais, apenas PENDING;
guard de 20 pendentes por família, distinto do cap de publicação.
Maintenance horária: batch 10; indisponibilidade factual desativa.
Erros transitórios não desativam; não há auto-reativação, auto-publicação ou renovação automática do protocolo.

Estado partilhado em `/run/lowcost-europa/`, provisionado por tmpfiles.
PrivateTmp permanece compatível com os locks partilhados.

## Evidência e limites

Estimativa de entrega/destino não prova origem, armazém ou ausência de alfândega.
Não fabricar país, seller, stock, reputação, avaliação ou conversão.
Approval humano verifica a página real; a API verifica a promoção afiliada.
Não publicar garantias sem evidência.

Indexação permanece fail-closed até autorização própria. Conclusão técnica não equivale a ativação comercial/legal.
Scripts e testes de recuperação preservados não certificam timers ativos;
estado do VPS requer inspeção atual. Documentos de fases anteriores são históricos,
não planos para executar novamente. Consulte [índice](README.md).
