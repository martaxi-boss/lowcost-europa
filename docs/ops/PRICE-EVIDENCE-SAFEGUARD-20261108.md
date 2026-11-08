# Low Cost Europa — proteção de preço comprovado na montra

## Origem da auditoria (08/11/2026)

O dono mostrou o painel com avisos de produtos sem preços recentes, sem prazo de entrega, com stock desconhecido e ofertas editoriais excluídas pela política pública.

Auditorias independentes **somente leitura** na VPS:
- [#42435819072](https://github.com/martaxi-boss/VPS/actions/runs/42435819072), [#42435911890](https://github.com/martaxi-boss/VPS/actions/runs/42435911890), [#42436038334](https://github.com/martaxi-boss/VPS/actions/runs/42436038334), [#42436127296](https://github.com/martaxi-boss/VPS/actions/runs/42436127296).
- 77 ofertas selecionadas sem `owner_hidden`; 52 cumpriam os requisitos técnicos antigos de publicação; 25 não cumpriam: 19 sem promoção afiliada elegível e 6 sem protocolo editorial inicial confirmado.
- Das 52: 46 têm observação real de **preço positivo EUR** nas últimas 24h; 6 não (IDs internos 83, 62, 184, 101, 98, 137); **0 sem qualquer histórico de preço**.
- Todas as 52 tiveram a última observação com disponibilidade `UNKNOWN`; 50 sem qualquer prazo de entrega numérico; 47 sem prova individual de origem. **UNKNOWN não comprova esgotado.** Não inventar stock, prazo de até cinco dias ou armazém europeu.
- O serviço horário de manutenção está ativo, verificou 240 produtos/observações nas últimas 24h, 150 com preço, mas nenhuma consulta conseguiu provar stock positivo ou prazo numérico.
- Uma consulta real da Affiliate Product Detail API para uma oferta sem preço recente devolveu `current_record_count`/objeto `products` vazio (sem dados de item). **Não equivale, por si só, a confirmação de produto esgotado** ou autorização de apagar a oferta. Não copiar resposta, identificadores do parceiro ou segredos para logs/repo.

## Correção: não anunciar preços antigos como atuais

No Django de produção, `PUBLIC_RECENT_PRICE_REQUIRED=True` por omissão (rollback só se aprovado via `DJANGO_PUBLIC_RECENT_PRICE_REQUIRED=false`).

`public_eligibility_q` exige, **além de todas as condições editoriais existentes**, `Exists(OfferObservation)` da mesma oferta com:
- preço **maior que zero**;
- moeda **EUR**;
- data não futura e **há menos de 24 horas**.

O mesmo filtro é aplicado na montra, pesquisa, contagens e no endpoint `/go/` de redirecionamento afiliado. Logo, a oferta com preço desatualizado **não aparece como disponível para clique**, e o acesso direto ao antigo link de saída também é bloqueado até existir prova nova. A diferença não altera os atributos editoriais (`owner_hidden`, `is_active`), não apaga observações, não decide rejeições, não modifica links, não cria programas ou novas bases de dados. A manutenção rotativa continuará a verificar as ofertas para reativação automática **apenas pela ocorrência de uma observação real de preço válido**.

### Painel privado

Separar:
- `eligible_public_offers`: ofertas com requisitos editoriais **e** preço recente;
- `visible_blocked_offers`: ofertas selecionadas cuja promoção ou protocolo ainda não habilita a publicação;
- `price_held_from_public`: ofertas editorial e tecnicamente aptas, **temporariamente fora da montra por preço vencido**;
- disponibilidade, origem e prazos: apresentadas sem promessas não demonstradas, somente para as ofertas que permanecem públicas.

Se a fonte AliExpress disponibilizar apenas preço e não stock/prazo, **não transformar ausências em prova de disponibilidade ou expedição**. O valor no site é *preço observado*, não cotação fixa garantida.

### Segurança e verificação

- Testes unitários e de integração devem cobrir `/go/`, homepage, páginas das cinco categorias, prefixos `offer__` do filtro, preço recente EUR positivo, inválido, zero, futuro e vencido, histórico preservado, e retorno à montra após nova observação válida.
- Não alterar Google Search Console, Google Analytics, Meta, e-mail, DNS, TLS, credenciais ou comissões.
- Validar VPS através de deploy por SHA exato, backup privado e prova do Django de produção: contagem 46/6 no instante da auditoria **antes de novas atualizações horárias**; a contagem poderá variar com as próximas observações. Verificar sitemap/página inicial ainda indexáveis, HTTPS, painel privado e timer de manutenção ativo.
- Bloquear a produção se um teste mostrar que a atualização retira todas as cinco categorias ou cria erro de base de dados.

## Pendências factuais, não bugs inventados

Os 52 estados `UNKNOWN` exigem evidência adicional do fornecedor, idealmente por SKU. O prazo/país de origem depende do armazém e da variante; a API de afiliados nem sempre devolve esses campos. Não comprar serviços pagos nem instalar scrapers para mascarar o problema. Os 19 + 6 bloqueios técnicos/editoriais exigem revalidação autónoma; **não alterar estado editorial por automatismo**.

Ferrari: perfil independente de cinco famílias fornecido por pedido não confidencial `lowcost-offer-family-profile-20261108-0149` na ponte existente, [#42436054190](https://github.com/martaxi-boss/VPS/actions/runs/42436054190). Não confundir o perfil de dados Ferrari com a aplicação Django do próprio projeto.
