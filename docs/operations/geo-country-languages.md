# Lowcost Europa — idioma automático por IP público (mercado europeu)

## Regra aprovada (2026-11-07)

Apenas cinco traduções da interface: **pt-PT, es, fr, de, en**.
O país do **IP público que chega à aplicação** é a única fonte da escolha
automática. VPN é tratada exatamente como qualquer outro IP; não se deteta
nem identifica o uso de VPN.

| País ISO | Idioma |
| --- | --- |
| PT | pt-PT |
| ES | es |
| FR | fr |
| DE | de |
| GB (Reino Unido) | en |
| Qualquer outro país europeu, fora da Europa ou IP indeterminado | en |

Brasil, Angola e outros países lusófonos **não** recebem português por IP
nesta implementação de âmbito europeu. Uma preferência antiga do navegador
ou cookie de idioma **não** prevalece na montra com o modo IP ativo.
Por isso, o seletor manual antigo é ocultado neste modo para não mostrar um
controlo que não mudaria a regra obrigatória.

Isto **não é bloqueio geográfico** nem autorização para envio de produtos
fora do mercado. A lógica de entrega e as regras da montra são separadas.

## Arquitetura mínima e segurança

- Apenas páginas públicas (início, pesquisa, páginas institucionais, família de
  produtos) recebem escolha automática por IP. O Owner, admin, redirecionamentos
  de afiliado e operações mantêm os comportamentos anteriores.
- A consulta é **local**, usando o ficheiro gratuito DB-IP Country Lite em MMDB.
  Não faz chamadas externas por visita; não guarda IPs para selecionar idioma.
- O REMOTE_ADDR público é preferido. Se o acesso ao Django chegar
  exclusivamente via Nginx **local** (127.0.0.1 ou ::1), admite-se
  X-Real-IP apenas se o Nginx o **substituir sempre** pelo seu remote_addr.
  Nunca confiar em X-Forwarded-For fornecido livremente pelo visitante.
  Se a aplicação receber tráfego por proxy com outro IP interno, validar
  e ajustar explicitamente a cadeia de confiança antes de ativar.
- Páginas públicas em modo geográfico têm Cache-Control: private, no-store
  e Vary: Cookie, para evitar misturar idiomas entre visitantes.
- Em caso de IP desconhecido, base ausente ou país não listado: **inglês**.
  A localização IP é aproximada e pode falhar em VPNs ou operadores móveis.

## Ativação na VPS — apenas após CI e validação operacional

Tudo fica **dentro de** /srv/projects/lowcost-europa, usando o próprio
ambiente Python do projeto. Não instalar dependências globais, nem criar
segredos, ficheiros ou programas fora da pasta de projeto.

1. Confirmar commit do GitHub e backups, estado limpo e serviço existente.
2. Instalar requirements/base.txt no **venv do projeto**, no deploy normal.
3. A partir da raiz do projeto, executar
   ./.venv/bin/python deploy/scripts/update-country-db.py.
   O script descarrega (HTTPS) a versão atual da DB-IP Country Lite,
   tenta o mês anterior se ainda não publicada, valida o formato e instala
   atomica e exclusivamente em data/geoip/dbip-country-lite.mmdb.
   A pasta data/ já é ignorada pelo Git. A base não é versionada.
4. Auditar o Nginx atual: upstream local; verificar no respetivo bloco
   de proxy a diretiva proxy_set_header X-Real-IP $remote_addr;
   sem aceitar valores X-Real-IP oriundos de clientes. **Não** alterar proxies
   ou DNS por suposição.
5. Só então configurar DJANGO_GEO_LANGUAGE_ENABLED=true no ambiente de
   serviço existente e reiniciar/recarregar o serviço Django existente.
   false desativa a escolha geográfica, retornando ao comportamento atual.
6. Verificar localmente e através de VPNs portuguesas, espanholas, francesas,
   alemãs, britânicas e de outro país europeu: Content-Language, HTML lang,
   o texto traduzido e Cache-Control; verificar também que cookie antigo não
   muda o idioma, que o painel privado funciona e que as cinco categorias
   e noindex permanecem intactos.
7. Documentar execução, commit VPS, resultado do teste real e rollback.

A base é mensal; atualizar dentro da mesma pasta com o script do projeto
e reiniciar os processos de aplicação que mantêm o leitor em memória.
Não adicionar uma segunda instalação global.

## Licença / transparência

O [DB-IP Country Lite](https://db-ip.com/db/lite.php) é gratuito, com cobertura
e precisão inferiores à versão comercial, e exige atribuição CC BY 4.0.
Quando a funcionalidade está ativa, o rodapé público mostra o link
**IP Geolocation by DB-IP** para cumprir a atribuição.

A Política de Privacidade também explica o uso transitório do IP para esta
escolha e mantém a descrição separada dos logs técnicos e dos cliques.
