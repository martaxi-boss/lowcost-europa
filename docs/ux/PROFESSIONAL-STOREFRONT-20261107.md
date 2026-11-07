# Lowcost Europa — evolução visual profissional, 07/11/2026

## Objetivo
Redesenhar a apresentação na aplicação Django existente, sem alterar dados, cinco categorias, regras de elegibilidade, aprovação humana, links afiliados, VPS, domínio ou SEO.

## Alterações propostas em branch
- Homepage e navegação com linguagem mais direta, orientação por especialidades e melhor hierarquia visual.
- Cartões editoriais com estado honesto: **Seleção editorial** quando existe uma oferta publicada, estado público original quando não existe.
- Preço e logística continuam dados observados e da oferta representativa, sem afirmar preço mínimo de toda a categoria.
- Avaliação e vendas do parceiro em secção expandível acessível; preço, logística e saída para AliExpress permanecem visíveis.
- CTA curto, legível e transparente: **VER PREÇO NO ALIEXPRESS**, com nota explicativa de compra no parceiro.
- Barra para voltar à comparação de até três equipamentos; funcionamento progressivo sem chamadas externas.
- Cores, sombras e espaçamento afinados no CSS existente. Nenhum framework, CDN ou instalação nova.

## Lacunas que dependem de provas reais e não devem ser ocultadas
1. Fotografias de fornecedores continuam externas. A imagem HIFU de 123x123 px, documentada anteriormente, requer fotografia factual de melhor qualidade do mesmo produto ou aceitação de aviso de baixa resolução.
2. Preço, stock por variante, país de origem e entrega precisam de confirmação no vendedor; observação UNKNOWN nunca é garantia.
3. A ordem editorial não representa ranking, melhores produtos ou stock certificado.
4. Índice SEO e lançamento permanecem desligados até decisão própria do proprietário.

## Testes e portas antes de publicar
- CI: Django check, testes, migrações, Ruff, Node unit e sintaxe.
- QA real por navegador a 360, 390, 430 e 1440 px para homepage, categorias, pesquisa, filtros, comparação, estados vazios, imagens, teclado e reduced-motion.
- Testes pós-deploy contra SHA efetivo da VPS; reportar erros, screenshots e estado de noindex, sem visitas automáticas aos links /go/.
- Testar /painel/ autenticado e regressar à versão anterior quando existir regressão.
- CI verde não é prova de deploy nem de aceitação estética. Nenhuma publicação comercial automática.
