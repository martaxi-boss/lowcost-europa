# LOWCOST EUROPA — Constituição Operacional do Catálogo

Status: regra permanente do projeto.

## Hierarquia imutável

1. Shipping / protocolo.
2. Família / relevância.
3. Decisão humana.
4. Editorial / montra.
5. Lifecycle factual.
6. Aprendizagem.

Nenhum preço, comissão, vendas, rating, popularidade ou preferência comercial ultrapassa o protocolo.

## Shipping hard gate

Discovery pode criar Candidates PENDING com shipping desconhecido e a fila privada **A REVER** não tem cap20. A regra fixa de approval continua a exigir entrega em Portugal e ship-from dentro de **PL, CZ, FR, ES ou DE**. O ato humano de clicar **APROVAR** é a atestação do Owner de que abriu o anúncio real e confirmou integralmente esse protocolo fixo; não existe checkbox nem seleção configurável de país. UNKNOWN não é PASS para a decisão humana. É proibido inferir ship-from por título, moeda, seller, imagem, prazo, “EU warehouse”, “European warehouse”, “Spain warehouse” ou qualquer heurística.

## Decisão humana e editorial

APPROVE significa que o Owner abriu o anúncio e confirmou disponibilidade, equipamento, família, entrega em Portugal e origem dentro do conjunto permitido. O botão APROVAR é a própria atestação; não é necessário preencher país individual. Approval é sinal positivo de aprendizagem da família, mas **APPROVE != PUBLISH**. Uma nova Offer aprovada nasce com `owner_hidden=True`. Approval nunca limpa `owner_hidden` de uma Offer existente. Campos históricos `ship_from_country` e `ship_from_verified_at` são preservados quando já existem, mas nunca são inventados.

Só a ação editorial humana de publicar/voltar a publicar pode tornar `owner_hidden=False`. Publicação exige Offer ativa, família operacional, placement e affiliate URL válidos, atestação humana de protocolo fresca e vaga na montra. O protocolo fixo atesta Portugal + origem dentro de PL/CZ/FR/ES/DE sem exigir persistência do país individual.

## Cap20

O limite de 20 aplica-se exclusivamente à **montra por família**. Não limita discovery, Candidates, PENDING, A REVER, APPROVED, histórico ou aprendizagem. Pode haver mais de 20 approvals; a 21.ª publicação é bloqueada se já existirem 20 na montra.

## Public eligibility e /go/

Elegibilidade pública central exige `is_active=True`, `owner_hidden=False`, affiliate URL não vazia e `protocol_verified_at` fresco. Essa freshness representa a atestação humana do protocolo fixo Portugal + origem dentro de PL/CZ/FR/ES/DE. `ship_from_country` e `ship_from_verified_at` permanecem como histórico opcional quando factual e conhecido, mas não são necessários para novas approvals. Storefront e `/go/` usam o mesmo gate; oferta inelegível não redireciona nem cria click válido.

## Revalidação

REVALIDAR é novamente uma atestação humana de que o Owner abriu o anúncio e confirmou entrega em Portugal + origem dentro de PL/CZ/FR/ES/DE. Não há checkbox nem dropdown; a ação renova `protocol_verified_at` e não inventa país individual. Maintenance factual nunca renova o protocolo humano.

## Lifecycle factual

Indisponibilidade factual confirmada desativa `is_active`. Erros transitórios (429, 5xx, timeout, network/API transitória ou detalhe insuficiente) não desativam; registam UNKNOWN quando aplicável. Offers inativas não entram na manutenção normal e não são auto-reativadas. Automação nunca limpa `owner_hidden`.

## Rejeição contextual

A rejeição pode guardar sinais factuais/logísticos, um motivo semântico apropriado e uma observação livre em `CandidateDecision.note`. A nota é auditável, mas não vira automaticamente negativo semântico. Shipping failure, origem fora da whitelist e indisponibilidade factual não contaminam aprendizagem comercial; motivos semânticos explícitos como família errada, acessório/peça ou listagem inadequada podem alimentar learning da família.

## Aprendizagem isolada por família

Approval é sinal comercial positivo apenas da família correspondente. Rejeições semânticas apropriadas podem ser sinais negativos; rejeições logísticas/factuais, Owner hide e seller unavailable não são negativos semânticos. O protocolo global (shipping, Portugal, whitelist, availability, dedupe, freshness, API safety e lifecycle) não é reaprendido por família.

## Mudar família

MOVE não é REJECT nem APPROVE. Deve preservar audit trail de origem, destino, título, actor e timestamp. Move-away é sinal de classificação incorreta para a família de origem; move-to é sinal de classificação plausível na família destino, mas não equivale a approval.

## História e autoridade

Candidates, Offers, Placements, Decisions, Observations, Clicks, Editorial Events e Family Move Events não são destruídos por mudanças de estado. Não existe auto-approval, auto-publication, auto-reactivation ou auto editorial rejection.

Estas invariantes não podem ser alteradas por discovery, refactor ou conveniência técnica. Qualquer mudança futura de shipping, approval, publicação, cap20, lifecycle, learning isolation ou history preservation exige **ORDEM EXPLÍCITA DO OWNER + AUDITORIA DO SUPERVISOR + TESTES DE REGRESSÃO**. Na ausência dessa autorização, FAIL CLOSED.

**PUBLIC LAUNCH: NO**, até ordem explícita posterior do Owner.
