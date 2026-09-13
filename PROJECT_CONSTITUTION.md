# LOWCOST EUROPA — PROJECT CONSTITUTION

Documento institucional do projeto. Deve mudar raramente.

## Identidade

O Lowcost Europa é uma plataforma de afiliados focada inicialmente no AliExpress, criada para selecionar poucos produtos, mas produtos de qualidade, confiáveis e com entrega rápida para clientes europeus.

O objetivo não é copiar o catálogo do AliExpress nem criar um marketplace gigantesco. O objetivo é construir uma plataforma simples, leve, séria, credível, rentável, automática e progressivamente inteligente.

## Missão

Filtrar o excesso de oferta do AliExpress e apresentar apenas oportunidades de compra que cumpram critérios elevados de qualidade, confiança, logística e valor económico.

Princípio central:

> Não mostramos tudo. Mostramos aquilo que merece ser mostrado.

Nunca sacrificar confiança apenas para aumentar a quantidade de produtos.

## Mercado inicial

Portugal é o mercado de validação inicial. A arquitetura deve estar preparada para outros países europeus, mas a expansão só deve acontecer quando existirem dados suficientes de tráfego, conversão, logística, SEO e rentabilidade.

## Regra logística

Critério principal: entrega prevista ao cliente em no máximo 5 dias.

Nunca afirmar localização logística, prazos garantidos ou condições aduaneiras sem prova suficiente. Quando apenas o prazo estiver confirmado, usar linguagem factual como “Entrega estimada em 2–5 dias para Portugal”.

## Qualidade acima de quantidade

É aceitável ter 30 excelentes produtos em vez de 30.000 medíocres.

Guardar apenas informação necessária para selecionar, comparar, validar, classificar, monitorizar e aprender. Evitar armazenamento desnecessário, duplicação pesada de imagens e infraestrutura excessiva.

## Filosofia técnica

Começar simples: aplicação web robusta, base de dados relacional, Nginx, tarefas agendadas, arquitetura modular e manutenção fácil.

Não introduzir microserviços, clusters, Elasticsearch ou infraestrutura cara sem necessidade real.

Pergunta obrigatória antes de adicionar complexidade:

> Isto aumenta vendas, confiança ou eficiência de forma mensurável?

Se a resposta for não, não construir ainda.

## Produtos como entidades permanentes

Uma página do Lowcost Europa representa a família de produto; as ofertas de vendedores são substituíveis.

Se uma oferta desaparecer, a página permanente deve continuar e procurar outra oferta equivalente que cumpra os critérios. Isto protege SEO, links partilhados, clientes recorrentes e recomendações.

## Estabilidade e confiança

Guardar métricas de primeira e última observação, dias ativo, desaparecimentos, alterações de URL, preço, entrega e estabilidade do vendedor.

Criar progressivamente um Stability / Reliability Score.

Critérios de confiança incluem avaliações, classificação, quantidade de feedback, vendas, histórico, estabilidade, preço, reputação do vendedor e prazo de entrega.

Nunca fabricar feedback ou apresentar reviews falsas.

## Ciclo de vida

Estados internos possíveis: New, Testing, Verified, Proven, Winner / Top Pick, Observation e Retired.

Produtos novos não devem ultrapassar automaticamente produtos estáveis apenas por custarem menos ou pagarem mais comissão.

## Exploration vs Exploitation

Como ponto de partida, manter aproximadamente 80–90% de produtos comprovados e 10–20% de exploração de novos candidatos. Estes valores devem evoluir com dados reais.

## Algoritmo económico

Nunca otimizar apenas por desconto, comissão ou vendas.

Considerar aproximadamente:

probabilidade de conversão × valor da compra × comissão × confiança × qualidade logística

Métrica estratégica importante: receita por 1.000 impressões.

## Descontos e preços

Não confiar cegamente no “preço original” apresentado pelo vendedor. Construir progressivamente histórico próprio de preços e preferir mensagens como “Preço mais baixo dos últimos 30 dias”, “Poupa €80 face à média recente”, “Cupão disponível” ou “Boa oportunidade de preço”.

## Nichos

Primeiro nicho estratégico: estética profissional, incluindo HIFU 7D, cavitação, Triple Wave / laser de depilação, remoção de tatuagens e outros equipamentos profissionais.

O site não deve ficar limitado a este nicho. Os dados devem descobrir novas oportunidades.

## SEO

Não construir milhares de páginas automáticas de baixo valor. Cada página indexada deve acrescentar utilidade real: comparação de ofertas, histórico de preço, prazo de entrega, avaliação, estabilidade, última verificação e alternativas.

Começar por Portugal e preparar a arquitetura para /pt/, /es/, /fr/ e outros mercados, ativando-os apenas quando estiverem suficientemente desenvolvidos.

## Proposta de valor

Mensagem central: produtos selecionados com entrega rápida e critérios de qualidade verificados.

Outra formulação:

> Nós fazemos a filtragem por si.

Credibilidade deve ser demonstrada, não apenas anunciada.

## Transparência

Não basear o negócio em cloaking, páginas diferentes para bots e pessoas, sistemas para enganar plataformas ou outras práticas manipuladoras.

O visitante recebe a mesma proposta que o sistema anuncia.

## Inteligência própria

O Lowcost Europa deve criar informação própria através de histórico, estabilidade, cliques, impressões, conversões, vendas, receita e alterações de preço e logística.

Com o tempo, estes dados tornam-se vantagem competitiva própria.

## Automação responsável

Não automatizar totalmente uma decisão que ainda não compreendemos.

Sequência preferida: observar, validar, transformar experiência em regra, testar, automatizar, monitorizar e corrigir.

Decisões críticas devem permanecer auditáveis.

## Supervisor

O Supervisor preserva a visão do projeto, decide prioridades, impede overengineering, coordena agentes, valida arquitetura, protege regras de negócio, controla custos, mantém documentação, avalia dados e valida alterações relevantes antes de produção.

Toda alteração relevante deve responder:
1. Por que precisamos disto?
2. Qual problema resolve?
3. Como vamos medir se melhorou?
4. Quanto aumenta a complexidade?
5. É reversível?
6. Pode afetar confiança do utilizador?

## Organização de agentes

Estrutura recomendada:
- Supervisor / Architect
- Builder
- Data / Discovery
- SEO / Content
- QA / Reviewer

O Supervisor mantém a decisão final.

## Processo de desenvolvimento

Usar Git, GitHub, branches por funcionalidade quando apropriado, documentação, staging e separação de produção quando necessário.

Nunca guardar credenciais no repositório.

## Custos

Evitar APIs pagas desnecessárias, servidores demasiado grandes, bases gigantes sem utilidade e processamento contínuo sem necessidade.

Produtos importantes podem ser verificados com maior frequência; produtos experimentais ou inativos, menos frequentemente.

## Honestidade comercial

Regra absoluta:

> Nunca prometer aquilo que não conseguimos cumprir ou verificar.

Se uma informação é estimativa, chamar-lhe estimativa. Se uma oferta deixou de cumprir os critérios, retirar ou atualizar. Se houver dúvida séria, não atribuir selo de confiança.

## Critério de sucesso

O objetivo não é ter o maior catálogo. É ter o catálogo que produz mais confiança, satisfação e retorno económico por produto.

Métricas: compradores satisfeitos, compradores recorrentes, boca a boca, tráfego orgânico, conversão, receita, estabilidade e baixa taxa de ofertas problemáticas.

## Filosofia final

Pequeno quando pequeno for suficiente.

Automático quando automação for segura.

Inteligente quando existirem dados para aprender.

Rentável sem sacrificar confiança.

Adaptável sem complexidade desnecessária.

Construir de raiz para durar.
