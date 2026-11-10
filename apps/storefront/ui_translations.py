# ruff: noqa: E501 -- fixed, reviewed UI translations are intentionally long strings
"""Curated five-language public UI copy. Portuguese is the source and fallback.

Only fixed interface terms and known category names are localised. Seller-supplied
product titles and observations are never machine-translated or overwritten.
No network calls, paid translation APIs or visitor IP geolocation.
"""

import re

UI_TRANSLATIONS = {
  "PARTILHAR ESTE PRODUTO": {"es":"COMPARTIR ESTE PRODUCTO","en":"SHARE THIS PRODUCT","fr":"PARTAGER CE PRODUIT","de":"DIESES PRODUKT TEILEN"},
  "Produto a partilhar": {"es":"Producto que vas a compartir","en":"Product to share","fr":"Produit à partager","de":"Produkt zum Teilen"},
  "Produto Low Cost Europa": {"es":"Producto Low Cost Europa","en":"Low Cost Europa product","fr":"Produit Low Cost Europa","de":"Low Cost Europa Produkt"},
  "Link original e identificação do produto enviados para partilha.": {"es":"Enlace original y datos del producto enviados para compartir.","en":"Original link and product details passed to sharing.","fr":"Lien original et détails du produit envoyés au partage.","de":"Originallink und Produktangaben zum Teilen übergeben."},
  "Mensagem com o produto e o link original copiada. Cole-a na conversa.": {"es":"Mensaje con el producto y el enlace original copiado. Pégalo en la conversación.","en":"Message with product details and original link copied. Paste it into the chat.","fr":"Message contenant le produit et le lien original copié. Collez-le dans la conversation.","de":"Nachricht mit Produktangaben und Originallink kopiert. Füge sie in den Chat ein."},
  "A mensagem inclui o produto e o link original. A opção Partilhar da aplicação AliExpress pode criar outro endereço.": {"es":"El mensaje incluye el producto y el enlace original. La función Compartir de la aplicación AliExpress puede crear otra dirección.","en":"The message includes the product and the original link. Sharing inside the AliExpress app may create a different address.","fr":"Le message contient le produit et le lien original. Le partage dans l’application AliExpress peut créer une autre adresse.","de":"Die Nachricht enthält das Produkt und den Originallink. Teilen in der AliExpress-App kann eine andere Adresse erstellen."},
  "PARTILHAR LINK ORIGINAL": {"es":"COMPARTIR ENLACE ORIGINAL","en":"SHARE ORIGINAL LINK","fr":"PARTAGER LE LIEN ORIGINAL","de":"ORIGINALLINK TEILEN"},
  "Partilhe aqui para enviar o link original. A opção Partilhar da aplicação AliExpress pode criar outro endereço.": {"es":"Compártelo aquí para enviar el enlace original. La función Compartir de la aplicación AliExpress puede crear otra dirección.","en":"Share here to send the original link. The AliExpress app's Share option may create a different address.","fr":"Partagez ici pour envoyer le lien d’origine. L’option Partager de l’application AliExpress peut créer une autre adresse.","de":"Teile den Originallink hier. Die Teilen-Funktion der AliExpress-App kann eine andere Adresse erstellen."},
  "Link original enviado para partilha.": {"es":"Enlace original enviado para compartir.","en":"Original link sent to share.","fr":"Lien original envoyé au partage.","de":"Originallink zum Teilen übergeben."},
  "Link original copiado. Cole-o na mensagem que quer enviar.": {"es":"Enlace original copiado. Pégalo en el mensaje que quieras enviar.","en":"Original link copied. Paste it into your message.","fr":"Lien original copié. Collez-le dans votre message.","de":"Originallink kopiert. Füge ihn in deine Nachricht ein."},
  "Não foi possível copiar. Abra a opção abaixo para selecionar o link original.": {"es":"No se pudo copiar. Abre la opción siguiente para seleccionar el enlace original.","en":"Could not copy. Open the option below to select the original link.","fr":"Impossible de copier. Ouvrez l’option ci-dessous pour sélectionner le lien original.","de":"Kopieren fehlgeschlagen. Öffne die Option unten, um den Originallink auszuwählen."},
  "Não abriu no navegador? Copiar link original": {"es":"¿No se abre en el navegador? Copiar enlace original","en":"Not opening in your browser? Copy original link","fr":"Le navigateur ne s'ouvre pas ? Copier le lien original","de":"Öffnet sich der Browser nicht? Originallink kopieren"},
  "Se o telemóvel abrir a aplicação AliExpress, copie o link original e cole-o no Chrome ou Safari.": {"es":"Si el móvil abre la aplicación AliExpress, copia el enlace original y pégalo en Chrome o Safari.","en":"If your phone opens the AliExpress app, copy the original link and paste it into Chrome or Safari.","fr":"Si votre téléphone ouvre l’application AliExpress, copiez le lien original et collez-le dans Chrome ou Safari.","de":"Wenn dein Handy die AliExpress-App öffnet, kopiere den Originallink und füge ihn in Chrome oder Safari ein."},
  "Link de afiliado original": {"es":"Enlace de afiliado original","en":"Original affiliate link","fr":"Lien d'affiliation original","de":"Ursprünglicher Affiliate-Link"},
  "Copiar link original": {"es":"Copiar enlace original","en":"Copy original link","fr":"Copier le lien original","de":"Originallink kopieren"},
  "Link copiado. Cole-o no Chrome ou Safari.": {"es":"Enlace copiado. Pégalo en Chrome o Safari.","en":"Link copied. Paste it into Chrome or Safari.","fr":"Lien copié. Collez-le dans Chrome ou Safari.","de":"Link kopiert. Füge ihn in Chrome oder Safari ein."},
  "Selecione o link acima e copie-o manualmente.": {"es":"Selecciona el enlace de arriba y cópialo manualmente.","en":"Select the link above and copy it manually.","fr":"Sélectionnez le lien ci-dessus et copiez-le manuellement.","de":"Wähle den Link oben aus und kopiere ihn manuell."},
  "Preço EUR observado para Espanha; confirme stock e entrega no vendedor.": {
    "es": "Precio en EUR observado para España; confirma existencias y entrega con el vendedor.",
    "en": "EUR price observed for Spain; confirm stock and delivery with the seller.",
    "fr": "Prix EUR observé pour l'Espagne ; confirmez le stock et la livraison auprès du vendeur.",
    "de": "Für Spanien beobachteter EUR-Preis; Bestand und Lieferung beim Verkäufer bestätigen.",
  },
  "Guia de compra para Portugal": {"es": "Guía de compra para España"},
  "Antes de escolher uma oferta, confirme estes pontos sobre o equipamento anunciado:": {"es": "Antes de elegir una oferta, confirma estos puntos sobre el equipo anunciado:"},
  "Estes critérios ajudam a comparar ofertas, mas não certificam características de um modelo específico. Preço, stock, entrega e condições finais devem ser confirmados junto do parceiro.": {"es": "Estos criterios ayudan a comparar ofertas, pero no certifican las características de un modelo concreto. El precio, las existencias, la entrega y las condiciones finales deben confirmarse con el socio."},
  "Ver seleção de": {"es": "Ver selección de"},
  "pode mudar no parceiro": {"es": "puede cambiar en el socio"},
  "Adicionar": {"es": "Añadir"},
  "à comparação": {"es": "a la comparación"},
  "As fontes apresentam estimativas diferentes": {"es": "Las fuentes muestran estimaciones diferentes"},
  "Dados de referência para Portugal; preço e entrega para Espanha não confirmados.": {
    "es": "Datos de referencia para Portugal; precio y entrega para España no confirmados."
  },
  "Lowcost Europa | Equipamentos de estética profissional": {
    "es": "Lowcost Europa | Equipos de estética profesional",
    "en": "Lowcost Europa | Professional beauty equipment",
    "fr": "Lowcost Europa | Équipements d’esthétique professionnelle",
    "de": "Lowcost Europa | Professionelle Kosmetikgeräte"
  },
  "Início": {
    "es": "Inicio",
    "en": "Home",
    "fr": "Accueil",
    "de": "Startseite"
  },
  "Produtos": {
    "es": "Productos",
    "en": "Products",
    "fr": "Produits",
    "de": "Produkte"
  },
  "Pesquisar": {
    "es": "Buscar",
    "en": "Search",
    "fr": "Rechercher",
    "de": "Suchen"
  },
  "Como funciona": {
    "es": "Cómo funciona",
    "en": "How it works",
    "fr": "Comment ça marche",
    "de": "So funktioniert es"
  },
  "Afiliados": {
    "es": "Afiliados",
    "en": "Affiliates",
    "fr": "Affiliation",
    "de": "Affiliate-Links"
  },
  "Contacto": {
    "es": "Contacto",
    "en": "Contact",
    "fr": "Contact",
    "de": "Kontakt"
  },
  "Menu": {
    "es": "Menú",
    "en": "Menu",
    "fr": "Menu",
    "de": "Menü"
  },
  "Explorar": {
    "es": "Explorar",
    "en": "Explore",
    "fr": "Explorer",
    "de": "Entdecken"
  },
  "Privacidade": {
    "es": "Privacidad",
    "en": "Privacy",
    "fr": "Confidentialité",
    "de": "Datenschutz"
  },
  "Termos": {
    "es": "Condiciones",
    "en": "Terms",
    "fr": "Conditions",
    "de": "Nutzungsbedingungen"
  },
  "Transparência": {
    "es": "Transparencia",
    "en": "Transparency",
    "fr": "Transparence",
    "de": "Transparenz"
  },
  "Informação e transparência": {
    "es": "Información y transparencia",
    "en": "Information and transparency",
    "fr": "Information et transparence",
    "de": "Informationen und Transparenz"
  },
  "Saltar para o conteúdo": {
    "es": "Saltar al contenido",
    "en": "Skip to content",
    "fr": "Aller au contenu",
    "de": "Zum Inhalt springen"
  },
  "Navegação principal": {
    "es": "Navegación principal",
    "en": "Main navigation",
    "fr": "Navigation principale",
    "de": "Hauptnavigation"
  },
  "Navegação mobile": {
    "es": "Navegación móvil",
    "en": "Mobile navigation",
    "fr": "Navigation mobile",
    "de": "Mobile Navigation"
  },
  "Lowcost Europa - início": {
    "es": "Lowcost Europa - inicio",
    "en": "Lowcost Europa - home",
    "fr": "Lowcost Europa - accueil",
    "de": "Lowcost Europa - Startseite"
  },
  "Contactar Lowcost Europa pelo WhatsApp": {
    "es": "Contactar con Lowcost Europa por WhatsApp",
    "en": "Contact Lowcost Europa on WhatsApp",
    "fr": "Contacter Lowcost Europa sur WhatsApp",
    "de": "Lowcost Europa per WhatsApp kontaktieren"
  },
  "Falar connosco no WhatsApp": {
    "es": "Hablar con nosotros por WhatsApp",
    "en": "Chat with us on WhatsApp",
    "fr": "Nous contacter sur WhatsApp",
    "de": "Schreiben Sie uns auf WhatsApp"
  },
  "Uma plataforma de seleção e organização de produtos de parceiros externos. A compra acontece no vendedor ou plataforma parceira.": {
    "es": "Una plataforma para seleccionar y organizar productos de socios externos. La compra se realiza en la tienda o plataforma asociada.",
    "en": "A platform for selecting and organising products from external partners. Purchases take place with the seller or partner platform.",
    "fr": "Une plateforme de sélection et d'organisation de produits de partenaires externes. L'achat s'effectue auprès du vendeur ou de la plateforme partenaire.",
    "de": "Eine Plattform zur Auswahl und übersichtlichen Darstellung von Produkten externer Partner. Der Kauf erfolgt beim Verkäufer oder auf der Partnerplattform."
  },
  "Alguns links podem ser afiliados. Preços, disponibilidade, entrega e condições são definidos pelo parceiro e podem mudar.": {
    "es": "Algunos enlaces pueden ser de afiliación. Los precios, la disponibilidad, el envío y las condiciones los establece el socio y pueden cambiar.",
    "en": "Some links may be affiliate links. Prices, availability, delivery and terms are set by the partner and may change.",
    "fr": "Certains liens peuvent être affiliés. Les prix, la disponibilité, la livraison et les conditions sont définis par le partenaire et peuvent changer.",
    "de": "Einige Links können Affiliate-Links sein. Preise, Verfügbarkeit, Lieferung und Bedingungen werden vom Partner festgelegt und können sich ändern."
  },
  "Equipamentos de estética.": {
    "es": "Equipos de estética.",
    "en": "Aesthetic equipment.",
    "fr": "Équipements esthétiques.",
    "de": "Ästhetikgeräte."
  },
  "Escolhas mais claras.": {
    "es": "Decisiones más claras.",
    "en": "Clearer choices.",
    "fr": "Des choix plus clairs.",
    "de": "Klarere Entscheidungen."
  },
  "Equipamentos de estética profissional · seleção organizada": {
    "es": "Equipos de estética profesional · selección organizada",
    "en": "Professional aesthetic equipment · organised selection",
    "fr": "Équipements esthétiques professionnels · sélection organisée",
    "de": "Professionelle Ästhetikgeräte · übersichtliche Auswahl"
  },
  "Explore equipamentos por especialidade e encontre opções organizadas num só lugar.": {
    "es": "Explore equipos por especialidad y encuentre opciones organizadas en un mismo lugar.",
    "en": "Explore equipment by speciality and find organised options in one place.",
    "fr": "Explorez les équipements par spécialité et retrouvez des options regroupées au même endroit.",
    "de": "Entdecken Sie Geräte nach Fachgebiet und finden Sie übersichtliche Angebote an einem Ort."
  },
  "Compare preços e informações observadas antes de consultar a oferta no parceiro. Sem promessas de stock ou entrega que não podemos confirmar.": {
    "es": "Compare los precios y los datos observados antes de consultar la oferta del socio. Sin promesas de disponibilidad o entrega que no podamos confirmar.",
    "en": "Compare observed prices and information before viewing the partner's offer. We do not promise stock or delivery we cannot verify.",
    "fr": "Comparez les prix et les informations constatées avant de consulter l'offre du partenaire. Aucune promesse de stock ou de livraison non vérifiable.",
    "de": "Vergleichen Sie beobachtete Preise und Angaben, bevor Sie das Partnerangebot aufrufen. Keine unbestätigten Zusagen zu Bestand oder Lieferung."
  },
  "Encontre o seu equipamento": {
    "es": "Encuentre su equipo",
    "en": "Find your equipment",
    "fr": "Trouvez votre équipement",
    "de": "Finden Sie Ihr Gerät"
  },
  "VER EQUIPAMENTOS E PREÇOS": {
    "es": "VER EQUIPOS Y PRECIOS",
    "en": "VIEW EQUIPMENT AND PRICES",
    "fr": "VOIR LES ÉQUIPEMENTS ET PRIX",
    "de": "GERÄTE UND PREISE ANSEHEN"
  },
  "Organizado por categorias": {
    "es": "Organizado por categorías",
    "en": "Organised by category",
    "fr": "Classé par catégorie",
    "de": "Nach Kategorien geordnet"
  },
  "Preços observados": {
    "es": "Precios observados",
    "en": "Observed prices",
    "fr": "Prix constatés",
    "de": "Beobachtete Preise"
  },
  "Compra externa transparente": {
    "es": "Compra externa transparente",
    "en": "Transparent external purchases",
    "fr": "Achat externe transparent",
    "de": "Transparenter Kauf beim Partner"
  },
  "Explore por especialidade": {
    "es": "Explore por especialidad",
    "en": "Browse by speciality",
    "fr": "Explorer par spécialité",
    "de": "Nach Fachgebiet entdecken"
  },
  "Categoria": {
    "es": "Categoría",
    "en": "Category",
    "fr": "Catégorie",
    "de": "Kategorie"
  },
  "Estamos a preparar a seleção das categorias.": {
    "es": "Estamos preparando la selección de categorías.",
    "en": "We are preparing the category selection.",
    "fr": "Nous préparons la sélection des catégories.",
    "de": "Wir bereiten die Kategorienauswahl vor."
  },
  "As imagens representam anúncios das respetivas categorias. Consulte os detalhes antes de comprar.": {
    "es": "Las imágenes proceden de anuncios de las categorías correspondientes. Consulte los detalles antes de comprar.",
    "en": "Images come from listings in their respective categories. Check the details before buying.",
    "fr": "Les images proviennent d'annonces des catégories concernées. Vérifiez les détails avant tout achat.",
    "de": "Die Bilder stammen aus Angeboten der jeweiligen Kategorien. Prüfen Sie die Angaben vor dem Kauf."
  },
  "Explore o catálogo": {
    "es": "Explore el catálogo",
    "en": "Explore the catalogue",
    "fr": "Explorer le catalogue",
    "de": "Katalog entdecken"
  },
  "Encontre a sua especialidade.": {
    "es": "Encuentre su especialidad.",
    "en": "Find your speciality.",
    "fr": "Trouvez votre spécialité.",
    "de": "Finden Sie Ihr Fachgebiet."
  },
  "Catálogo organizado": {
    "es": "Catálogo organizado",
    "en": "Organised catalogue",
    "fr": "Catalogue organisé",
    "de": "Übersichtlicher Katalog"
  },
  "Seleções para comparar com calma.": {
    "es": "Selecciones para comparar con calma.",
    "en": "Selections to compare at your own pace.",
    "fr": "Des sélections à comparer sereinement.",
    "de": "Angebote in Ruhe vergleichen."
  },
  "Entre na categoria, consulte os equipamentos apresentados e compare os dados observados. A ordem é editorial, não um ranking de qualidade.": {
    "es": "Entre en la categoría, consulte los equipos y compare los datos observados. El orden es editorial, no una clasificación de calidad.",
    "en": "Open a category, see the featured equipment and compare observed information. The order is editorial, not a quality ranking.",
    "fr": "Ouvrez une catégorie, consultez les équipements présentés et comparez les informations constatées. L'ordre est éditorial, pas un classement de qualité.",
    "de": "Öffnen Sie eine Kategorie, sehen Sie sich die Geräte an und vergleichen Sie die erfassten Daten. Die Reihenfolge ist redaktionell und keine Qualitätsrangliste."
  },
  "Deslize os cartões para explorar mais categorias.": {
    "es": "Deslice las tarjetas para explorar más categorías.",
    "en": "Swipe the cards to explore more categories.",
    "fr": "Faites défiler les cartes pour découvrir d'autres catégories.",
    "de": "Wischen Sie durch die Karten, um weitere Kategorien zu entdecken."
  },
  "A seleção pública está a ser preparada.": {
    "es": "Estamos preparando la selección pública.",
    "en": "The public selection is being prepared.",
    "fr": "La sélection publique est en préparation.",
    "de": "Die öffentliche Auswahl wird vorbereitet."
  },
  "Estamos a validar produtos e fontes antes de os apresentar aqui.": {
    "es": "Estamos verificando productos y fuentes antes de mostrarlos aquí.",
    "en": "We are validating products and sources before showing them here.",
    "fr": "Nous vérifions les produits et leurs sources avant de les présenter ici.",
    "de": "Wir prüfen Produkte und Quellen, bevor wir sie hier zeigen."
  },
  "Como ajudamos": {
    "es": "Cómo ayudamos",
    "en": "How we help",
    "fr": "Notre approche",
    "de": "So helfen wir"
  },
  "Menos ruído. Mais contexto para decidir.": {
    "es": "Menos ruido. Más contexto para decidir.",
    "en": "Less noise. More context for your decision.",
    "fr": "Moins de bruit. Plus de contexte pour décider.",
    "de": "Weniger Ablenkung. Mehr Informationen für Ihre Entscheidung."
  },
  "Selecionamos e organizamos informação útil sem transformar sinais incompletos em certezas.": {
    "es": "Seleccionamos y organizamos información útil sin presentar datos incompletos como certezas.",
    "en": "We select and organise useful information without presenting incomplete signals as facts.",
    "fr": "Nous sélectionnons et organisons les informations utiles sans présenter des données incomplètes comme des certitudes.",
    "de": "Wir wählen nützliche Informationen aus und ordnen sie, ohne unvollständige Angaben als Gewissheit darzustellen."
  },
  "Selecionamos": {
    "es": "Seleccionamos",
    "en": "We select",
    "fr": "Nous sélectionnons",
    "de": "Wir wählen aus"
  },
  "Organizamos": {
    "es": "Organizamos",
    "en": "We organise",
    "fr": "Nous organisons",
    "de": "Wir ordnen"
  },
  "Encaminhamos": {
    "es": "Redirigimos",
    "en": "We refer",
    "fr": "Nous redirigeons",
    "de": "Wir leiten weiter"
  },
  "Trabalhamos com um catálogo curto e organizado em vez de milhares de listagens sem contexto.": {
    "es": "Trabajamos con un catálogo conciso y organizado, en lugar de miles de anuncios sin contexto.",
    "en": "We use a focused, organised catalogue rather than thousands of listings without context.",
    "fr": "Nous privilégions un catalogue concis et organisé plutôt que des milliers d'annonces sans contexte.",
    "de": "Wir setzen auf einen übersichtlichen Katalog statt auf Tausende Angebote ohne Einordnung."
  },
  "Preço observado, logística disponível e sinais do parceiro aparecem com rótulos claros.": {
    "es": "El precio observado, la logística disponible y los datos del socio se muestran con etiquetas claras.",
    "en": "Observed prices, available delivery information and partner signals are clearly labelled.",
    "fr": "Les prix constatés, les informations logistiques disponibles et les données du partenaire sont clairement indiqués.",
    "de": "Beobachtete Preise, verfügbare Lieferangaben und Partnerdaten sind klar gekennzeichnet."
  },
  "Não fazemos checkout. O clique de oferta leva ao parceiro, onde a compra e o pagamento acontecem.": {
    "es": "No gestionamos el pago. Al seleccionar una oferta, accederá al socio, donde se realizan la compra y el pago.",
    "en": "We do not process checkout. An offer link takes you to the partner, where purchase and payment take place.",
    "fr": "Nous n'encaissons aucun paiement. Le lien de l'offre mène au partenaire, où l'achat et le paiement sont effectués.",
    "de": "Wir wickeln keine Zahlungen ab. Ein Angebotslink führt zum Partner, bei dem Kauf und Zahlung erfolgen."
  },
  "Da categoria ao parceiro, sem esconder quem vende.": {
    "es": "De la categoría al socio, con transparencia sobre quién vende.",
    "en": "From category to partner, with clear seller information.",
    "fr": "De la catégorie au partenaire, en indiquant clairement le vendeur.",
    "de": "Von der Kategorie zum Partner – mit klaren Angaben zum Verkäufer."
  },
  "Escolher uma categoria": {
    "es": "Elegir una categoría",
    "en": "Choose a category",
    "fr": "Choisir une catégorie",
    "de": "Kategorie auswählen"
  },
  "Comparar ofertas": {
    "es": "Comparar ofertas",
    "en": "Compare offers",
    "fr": "Comparer les offres",
    "de": "Angebote vergleichen"
  },
  "Seguir para o parceiro": {
    "es": "Ir al socio",
    "en": "Go to the partner",
    "fr": "Accéder au partenaire",
    "de": "Zum Partner wechseln"
  },
  "Comprar fora do Lowcost Europa": {
    "es": "Comprar fuera de Lowcost Europa",
    "en": "Buy outside Lowcost Europa",
    "fr": "Acheter hors de Lowcost Europa",
    "de": "Außerhalb von Lowcost Europa kaufen"
  },
  "Explore as famílias editoriais disponíveis.": {
    "es": "Explore las categorías editoriales disponibles.",
    "en": "Browse the available editorial categories.",
    "fr": "Parcourez les catégories proposées.",
    "de": "Entdecken Sie die verfügbaren redaktionellen Kategorien."
  },
  "Veja os dados observados, as limitações e a razão editorial quando existir.": {
    "es": "Consulte los datos observados, las limitaciones y los motivos editoriales cuando estén disponibles.",
    "en": "Review observed data, limitations and any stated editorial rationale.",
    "fr": "Consultez les données constatées, leurs limites et les raisons éditoriales, le cas échéant.",
    "de": "Prüfen Sie erfasste Daten, Einschränkungen und gegebenenfalls redaktionelle Gründe."
  },
  "O CTA identifica claramente que vai sair do Lowcost Europa.": {
    "es": "El botón indica claramente que saldrá de Lowcost Europa.",
    "en": "The button clearly indicates that you are leaving Lowcost Europa.",
    "fr": "Le bouton indique clairement que vous quittez Lowcost Europa.",
    "de": "Die Schaltfläche macht deutlich, dass Sie Lowcost Europa verlassen."
  },
  "Pagamento, envio e apoio à encomenda são tratados pelo vendedor ou plataforma.": {
    "es": "El pago, el envío y la atención al pedido corresponden al vendedor o a la plataforma.",
    "en": "Payment, shipping and order support are handled by the seller or platform.",
    "fr": "Le paiement, l'expédition et l'assistance liée à la commande sont assurés par le vendeur ou la plateforme.",
    "de": "Zahlung, Versand und Bestellservice erfolgen durch Verkäufer oder Plattform."
  },
  "Seleção editorial": {
    "es": "Selección editorial",
    "en": "Editorial selection",
    "fr": "Sélection éditoriale",
    "de": "Redaktionelle Auswahl"
  },
  "Em preparação": {
    "es": "En preparación",
    "en": "In preparation",
    "fr": "En préparation",
    "de": "In Vorbereitung"
  },
  "Em avaliação": {
    "es": "En evaluación",
    "en": "Under review",
    "fr": "En évaluation",
    "de": "In Prüfung"
  },
  "Em observação": {
    "es": "En observación",
    "en": "Under observation",
    "fr": "En observation",
    "de": "Unter Beobachtung"
  },
  "Indisponível": {
    "es": "No disponible",
    "en": "Unavailable",
    "fr": "Indisponible",
    "de": "Nicht verfügbar"
  },
  "Seleção em avaliação": {
    "es": "Selección en evaluación",
    "en": "Selection under review",
    "fr": "Sélection en cours d'évaluation",
    "de": "Auswahl in Prüfung"
  },
  "Seleção em preparação": {
    "es": "Selección en preparación",
    "en": "Selection in preparation",
    "fr": "Sélection en préparation",
    "de": "Auswahl in Vorbereitung"
  },
  "Imagem indisponível": {
    "es": "Imagen no disponible",
    "en": "Image unavailable",
    "fr": "Image indisponible",
    "de": "Bild nicht verfügbar"
  },
  "Fotografia de baixa resolução": {
    "es": "Foto de baja resolución",
    "en": "Low-resolution photo",
    "fr": "Photo basse résolution",
    "de": "Foto mit niedriger Auflösung"
  },
  "Especialidade": {
    "es": "Especialidad",
    "en": "Speciality",
    "fr": "Spécialité",
    "de": "Fachgebiet"
  },
  "Consulte opções publicadas e compare preço e logística observados.": {
    "es": "Consulte las opciones publicadas y compare el precio y la logística observados.",
    "en": "See published options and compare observed prices and delivery information.",
    "fr": "Consultez les options publiées et comparez les prix et les informations logistiques disponibles.",
    "de": "Sehen Sie veröffentlichte Angebote und vergleichen Sie beobachtete Preise und Lieferangaben."
  },
  "Preço da oferta apresentada": {
    "es": "Precio de la oferta mostrada",
    "en": "Price of the displayed offer",
    "fr": "Prix de l'offre affichée",
    "de": "Preis des angezeigten Angebots"
  },
  "Não disponível": {
    "es": "No disponible",
    "en": "Not available",
    "fr": "Non disponible",
    "de": "Nicht verfügbar"
  },
  "Observado em": {
    "es": "Observado el",
    "en": "Observed on",
    "fr": "Constaté le",
    "de": "Erfasst am"
  },
  "Preço histórico; confirme no parceiro.": {
    "es": "Precio antiguo; confírmelo con el socio.",
    "en": "Historical price; confirm with the partner.",
    "fr": "Ancien prix ; à confirmer auprès du partenaire.",
    "de": "Älterer Preis; beim Partner prüfen."
  },
  "Prazo indicado": {
    "es": "Plazo indicado",
    "en": "Estimated delivery time",
    "fr": "Délai indiqué",
    "de": "Angegebene Lieferzeit"
  },
  "Prazo não confirmado": {
    "es": "Plazo sin confirmar",
    "en": "Delivery time unconfirmed",
    "fr": "Délai non confirmé",
    "de": "Lieferzeit nicht bestätigt"
  },
  "Prazo histórico; confirme no parceiro.": {
    "es": "Plazo antiguo; confírmelo con el socio.",
    "en": "Historical delivery estimate; confirm with the partner.",
    "fr": "Ancien délai estimé ; à confirmer auprès du partenaire.",
    "de": "Ältere Lieferangabe; beim Partner prüfen."
  },
  "Ainda estamos a validar opções para esta categoria.": {
    "es": "Todavía estamos verificando opciones para esta categoría.",
    "en": "We are still validating options for this category.",
    "fr": "Nous vérifions encore des options pour cette catégorie.",
    "de": "Wir prüfen noch Angebote für diese Kategorie."
  },
  "Explorar equipamentos": {
    "es": "Explorar equipos",
    "en": "Explore equipment",
    "fr": "Explorer les équipements",
    "de": "Geräte entdecken"
  },
  "Preço observado": {
    "es": "Precio observado",
    "en": "Observed price",
    "fr": "Prix constaté",
    "de": "Beobachteter Preis"
  },
  "Logística observada": {
    "es": "Logística observada",
    "en": "Observed delivery information",
    "fr": "Informations logistiques constatées",
    "de": "Erfasste Lieferangaben"
  },
  "Oferta disponível": {
    "es": "Oferta disponible",
    "en": "Available offer",
    "fr": "Offre disponible",
    "de": "Verfügbares Angebot"
  },
  "Equipamento dedicado": {
    "es": "Equipo específico",
    "en": "Dedicated equipment",
    "fr": "Équipement spécialisé",
    "de": "Spezialgerät"
  },
  "Combo multifunções": {
    "es": "Equipo multifunción",
    "en": "Multifunction equipment",
    "fr": "Équipement multifonction",
    "de": "Multifunktionsgerät"
  },
  "Porque está aqui": {
    "es": "Por qué aparece aquí",
    "en": "Why it is shown",
    "fr": "Pourquoi cette offre apparaît",
    "de": "Warum dieses Angebot angezeigt wird"
  },
  "Consultar avaliações e vendas indicadas": {
    "es": "Consultar valoraciones y ventas indicadas",
    "en": "View reported ratings and sales",
    "fr": "Voir les évaluations et ventes indiquées",
    "de": "Angegebene Bewertungen und Verkäufe ansehen"
  },
  "Avaliação no parceiro": {
    "es": "Valoración del socio",
    "en": "Partner rating",
    "fr": "Évaluation chez le partenaire",
    "de": "Bewertung beim Partner"
  },
  "Vendas indicadas": {
    "es": "Ventas indicadas",
    "en": "Reported sales",
    "fr": "Ventes indiquées",
    "de": "Angegebene Verkäufe"
  },
  "VER PREÇO NO ALIEXPRESS": {
    "es": "VER PRECIO EN ALIEXPRESS",
    "en": "VIEW PRICE ON ALIEXPRESS",
    "fr": "VOIR LE PRIX SUR ALIEXPRESS",
    "de": "PREIS AUF ALIEXPRESS ANSEHEN"
  },
  "Compra externa.": {
    "es": "Compra externa.",
    "en": "External purchase.",
    "fr": "Achat externe.",
    "de": "Kauf beim externen Anbieter."
  },
  "Oferta indisponível": {
    "es": "Oferta no disponible",
    "en": "Offer unavailable",
    "fr": "Offre indisponible",
    "de": "Angebot nicht verfügbar"
  },
  "Esta oferta não está disponível para encaminhamento neste momento.": {
    "es": "Esta oferta no está disponible para redirigirle en este momento.",
    "en": "This offer cannot currently be opened on the partner site.",
    "fr": "Cette offre ne peut pas être consultée sur le site partenaire pour le moment.",
    "de": "Dieses Angebot kann derzeit nicht beim Partner aufgerufen werden."
  },
  "Comparar equipamento": {
    "es": "Comparar equipo",
    "en": "Compare equipment",
    "fr": "Comparer l'équipement",
    "de": "Gerät vergleichen"
  },
  "Ver comparação": {
    "es": "Ver comparación",
    "en": "View comparison",
    "fr": "Voir la comparaison",
    "de": "Vergleich anzeigen"
  },
  "Comparação de equipamentos": {
    "es": "Comparación de equipos",
    "en": "Equipment comparison",
    "fr": "Comparaison des équipements",
    "de": "Gerätevergleich"
  },
  "Comparar equipamentos": {
    "es": "Comparar equipos",
    "en": "Compare equipment",
    "fr": "Comparer les équipements",
    "de": "Geräte vergleichen"
  },
  "Limpar comparação": {
    "es": "Borrar comparación",
    "en": "Clear comparison",
    "fr": "Effacer la comparaison",
    "de": "Vergleich löschen"
  },
  "Pesquisar nesta lista": {
    "es": "Buscar en esta lista",
    "en": "Search this list",
    "fr": "Rechercher dans cette liste",
    "de": "Diese Liste durchsuchen"
  },
  "Tipo de equipamento": {
    "es": "Tipo de equipo",
    "en": "Equipment type",
    "fr": "Type d'équipement",
    "de": "Gerätetyp"
  },
  "Todos os tipos": {
    "es": "Todos los tipos",
    "en": "All types",
    "fr": "Tous les types",
    "de": "Alle Typen"
  },
  "Tipo não especificado": {
    "es": "Tipo no especificado",
    "en": "Unspecified type",
    "fr": "Type non précisé",
    "de": "Typ nicht angegeben"
  },
  "Qualquer preço ou moeda": {
    "es": "Cualquier precio o moneda",
    "en": "Any price or currency",
    "fr": "Tout prix ou devise",
    "de": "Beliebiger Preis oder Währung"
  },
  "Sem preço observado": {
    "es": "Sin precio observado",
    "en": "No observed price",
    "fr": "Sans prix constaté",
    "de": "Kein erfasster Preis"
  },
  "Organizar ofertas": {
    "es": "Ordenar ofertas",
    "en": "Sort offers",
    "fr": "Trier les offres",
    "de": "Angebote sortieren"
  },
  "Ordem editorial": {
    "es": "Orden editorial",
    "en": "Editorial order",
    "fr": "Ordre éditorial",
    "de": "Redaktionelle Reihenfolge"
  },
  "Preço observado: crescente": {
    "es": "Precio observado: ascendente",
    "en": "Observed price: low to high",
    "fr": "Prix constaté : croissant",
    "de": "Erfasster Preis: aufsteigend"
  },
  "Preço observado: decrescente": {
    "es": "Precio observado: descendente",
    "en": "Observed price: high to low",
    "fr": "Prix constaté : décroissant",
    "de": "Erfasster Preis: absteigend"
  },
  "Limpar filtros": {
    "es": "Borrar filtros",
    "en": "Clear filters",
    "fr": "Effacer les filtres",
    "de": "Filter löschen"
  },
  "Encontre o equipamento certo": {
    "es": "Encuentre el equipo adecuado",
    "en": "Find the right equipment",
    "fr": "Trouvez l'équipement adapté",
    "de": "Finden Sie das passende Gerät"
  },
  "Decida com informação": {
    "es": "Decida con información",
    "en": "Make an informed decision",
    "fr": "Décidez en connaissance de cause",
    "de": "Gut informiert entscheiden"
  },
  "Equipamento": {
    "es": "Equipo",
    "en": "Equipment",
    "fr": "Équipement",
    "de": "Gerät"
  },
  "Retirar": {
    "es": "Quitar",
    "en": "Remove",
    "fr": "Retirer",
    "de": "Entfernen"
  },
  "Na comparação": {
    "es": "En la comparación",
    "en": "In comparison",
    "fr": "Dans la comparaison",
    "de": "Im Vergleich"
  },
  "Ver no AliExpress": {
    "es": "Ver en AliExpress",
    "en": "View on AliExpress",
    "fr": "Voir sur AliExpress",
    "de": "Auf AliExpress ansehen"
  },
  "HIFU profissional": {
    "es": "HIFU profesional",
    "en": "Professional HIFU",
    "fr": "HIFU professionnel",
    "de": "Professionelles HIFU"
  },
  "Cavitação + RF + Vacuum (corpo)": {
    "es": "Cavitación + RF + vacío (cuerpo)",
    "en": "Cavitation + RF + vacuum (body)",
    "fr": "Cavitation + RF + aspiration (corps)",
    "de": "Kavitation + RF + Vakuum (Körper)"
  },
  "Hydrodermoabrasão / Aqua Facial / Multifunções faciais": {
    "es": "Hidrodermoabrasión / Aqua Facial / Multifunción facial",
    "en": "Hydrodermabrasion / Aqua Facial / Facial multifunction",
    "fr": "Hydrodermabrasion / Aqua Facial / Multifonction visage",
    "de": "Hydrodermabrasion / Aqua Facial / Multifunktion Gesicht"
  },
  "Pressoterapia / Vacuum / Drenagem": {
    "es": "Presoterapia / vacío / drenaje",
    "en": "Pressotherapy / vacuum / drainage",
    "fr": "Pressothérapie / aspiration / drainage",
    "de": "Pressotherapie / Vakuum / Drainage"
  },
  "Diodo Laser / Remoção de Tatuagens / Pigmentação": {
    "es": "Láser de diodo / eliminación de tatuajes / pigmentación",
    "en": "Diode laser / tattoo removal / pigmentation",
    "fr": "Laser diode / détatouage / pigmentation",
    "de": "Diodenlaser / Tattooentfernung / Pigmentierung"
  },
  "← Voltar às categorias": {
    "es": "← Volver a las categorías",
    "en": "← Back to categories",
    "fr": "← Retour aux catégories",
    "de": "← Zurück zu den Kategorien"
  },
  "Uma seleção organizada para comparar ofertas desta categoria com base na informação factual disponível. A compra acontece sempre no parceiro.": {
    "es": "Una selección organizada para comparar ofertas de esta categoría según los datos disponibles. La compra se realiza siempre con el socio.",
    "en": "An organised selection to compare offers in this category using available factual information. Purchases always take place with the partner.",
    "fr": "Une sélection organisée pour comparer les offres de cette catégorie selon les informations disponibles. L'achat se fait toujours auprès du partenaire.",
    "de": "Eine übersichtliche Auswahl zum Vergleich von Angeboten dieser Kategorie anhand verfügbarer Fakten. Der Kauf erfolgt immer beim Partner."
  },
  "Ir para a gestão desta categoria": {
    "es": "Ir a la gestión de esta categoría",
    "en": "Manage this category",
    "fr": "Gérer cette catégorie",
    "de": "Diese Kategorie verwalten"
  },
  "Como ler esta página": {
    "es": "Cómo leer esta página",
    "en": "How to read this page",
    "fr": "Comment lire cette page",
    "de": "Hinweise zu dieser Seite"
  },
  "Escolhas editoriais organizadas para facilitar a comparação. A posição não representa um ranking objetivo.": {
    "es": "Selecciones editoriales organizadas para facilitar la comparación. El orden no representa una clasificación objetiva.",
    "en": "Editorial selections organised to make comparisons easier. Position does not imply an objective ranking.",
    "fr": "Des sélections éditoriales organisées pour faciliter la comparaison. L'ordre n'est pas un classement objectif.",
    "de": "Redaktionell ausgewählte Angebote erleichtern den Vergleich. Die Reihenfolge stellt keine objektive Rangliste dar."
  },
  "Curadoria editorial": {
    "es": "Selección editorial",
    "en": "Editorial curation",
    "fr": "Sélection éditoriale",
    "de": "Redaktionelle Auswahl"
  },
  "Seleções Lowcost Europa": {
    "es": "Selecciones Lowcost Europa",
    "en": "Lowcost Europa selections",
    "fr": "Sélections Lowcost Europa",
    "de": "Lowcost Europa Auswahl"
  },
  "Mais opções validadas": {
    "es": "Más opciones verificadas",
    "en": "More validated options",
    "fr": "Autres options vérifiées",
    "de": "Weitere geprüfte Angebote"
  },
  "Outras ofertas selecionadas": {
    "es": "Otras ofertas seleccionadas",
    "en": "Other selected offers",
    "fr": "Autres offres sélectionnées",
    "de": "Weitere ausgewählte Angebote"
  },
  "Outras ofertas desta categoria, apresentadas pela ordem editorial definida no catálogo.": {
    "es": "Otras ofertas de esta categoría, ordenadas según los criterios editoriales del catálogo.",
    "en": "Other offers in this category, shown in the catalogue's editorial order.",
    "fr": "Autres offres de cette catégorie, présentées dans l'ordre éditorial du catalogue.",
    "de": "Weitere Angebote dieser Kategorie in der redaktionellen Katalogreihenfolge."
  },
  "Preferimos manter a categoria vazia a apresentar um produto sem validação suficiente. Volte mais tarde para consultar novas opções.": {
    "es": "Preferimos dejar la categoría vacía antes que mostrar productos insuficientemente verificados. Vuelva más adelante.",
    "en": "We prefer to leave the category empty rather than show an insufficiently verified product. Please check back later.",
    "fr": "Nous préférons laisser la catégorie vide plutôt que présenter un produit insuffisamment vérifié. Revenez plus tard.",
    "de": "Wir lassen diese Kategorie lieber leer, statt unzureichend geprüfte Produkte zu zeigen. Schauen Sie später wieder vorbei."
  },
  "Antes de continuar": {
    "es": "Antes de continuar",
    "en": "Before you continue",
    "fr": "Avant de continuer",
    "de": "Bevor Sie fortfahren"
  },
  "A compra acontece fora do Lowcost Europa.": {
    "es": "La compra se realiza fuera de Lowcost Europa.",
    "en": "Purchases take place outside Lowcost Europa.",
    "fr": "L'achat s'effectue hors de Lowcost Europa.",
    "de": "Der Kauf erfolgt außerhalb von Lowcost Europa."
  },
  "O Lowcost Europa organiza informação e encaminha para o parceiro. Preço, disponibilidade, pagamento, entrega e apoio à encomenda são definidos pelo vendedor ou plataforma. Alguns links podem gerar comissão afiliada.": {
    "es": "Lowcost Europa organiza información y redirige al socio. El precio, la disponibilidad, el pago, la entrega y la asistencia corresponden al vendedor o plataforma. Algunos enlaces pueden generar una comisión de afiliación.",
    "en": "Lowcost Europa organises information and redirects to partners. Prices, availability, payment, delivery and order support are set by the seller or platform. Some links may earn an affiliate commission.",
    "fr": "Lowcost Europa organise les informations et redirige vers le partenaire. Prix, disponibilité, paiement, livraison et assistance sont définis par le vendeur ou la plateforme. Certains liens peuvent générer une commission d'affiliation.",
    "de": "Lowcost Europa ordnet Informationen und leitet zum Partner weiter. Preis, Verfügbarkeit, Zahlung, Lieferung und Bestellservice werden vom Verkäufer oder der Plattform festgelegt. Einige Links können Provisionen auslösen."
  },
  "Como funcionam os links de afiliado": {
    "es": "Cómo funcionan los enlaces de afiliación",
    "en": "How affiliate links work",
    "fr": "Fonctionnement des liens d'affiliation",
    "de": "So funktionieren Affiliate-Links"
  },
  "← Explorar categorias": {
    "es": "← Explorar categorías",
    "en": "← Browse categories",
    "fr": "← Parcourir les catégories",
    "de": "← Kategorien entdecken"
  },
  "Catálogo Lowcost Europa": {
    "es": "Catálogo Lowcost Europa",
    "en": "Lowcost Europa catalogue",
    "fr": "Catalogue Lowcost Europa",
    "de": "Lowcost Europa Katalog"
  },
  "Pesquisar equipamentos": {
    "es": "Buscar equipos",
    "en": "Search equipment",
    "fr": "Rechercher des équipements",
    "de": "Geräte suchen"
  },
  "Encontre ofertas selecionadas por equipamento ou especialidade, antes de continuar para o parceiro.": {
    "es": "Encuentre ofertas seleccionadas por equipo o especialidad antes de visitar al socio.",
    "en": "Find selected offers by equipment or speciality before going to the partner.",
    "fr": "Trouvez des offres sélectionnées par équipement ou spécialité avant d'accéder au partenaire.",
    "de": "Finden Sie ausgewählte Angebote nach Gerät oder Fachgebiet, bevor Sie zum Partner wechseln."
  },
  "O que procura?": {
    "es": "¿Qué busca?",
    "en": "What are you looking for?",
    "fr": "Que recherchez-vous ?",
    "de": "Wonach suchen Sie?"
  },
  "Pesquisa de produtos validados": {
    "es": "Búsqueda de productos verificados",
    "en": "Search validated products",
    "fr": "Recherche de produits vérifiés",
    "de": "Geprüfte Produkte suchen"
  },
  "Mostramos apenas ofertas elegíveis já publicadas. Selecione até três para comparar antes de visitar o parceiro.": {
    "es": "Solo mostramos ofertas aptas y publicadas. Seleccione hasta tres para comparar antes de visitar al socio.",
    "en": "We only show eligible, published offers. Select up to three to compare before visiting the partner.",
    "fr": "Nous présentons uniquement les offres admissibles et publiées. Sélectionnez jusqu'à trois offres à comparer.",
    "de": "Wir zeigen nur veröffentlichte, zulässige Angebote. Wählen Sie bis zu drei zum Vergleich."
  },
  "← Anterior": {
    "es": "← Anterior",
    "en": "← Previous",
    "fr": "← Précédent",
    "de": "← Zurück"
  },
  "Seguinte →": {
    "es": "Siguiente →",
    "en": "Next →",
    "fr": "Suivant →",
    "de": "Weiter →"
  },
  "A pesquisa e os filtros desta página não alteram os resultados das outras páginas.": {
    "es": "La búsqueda y los filtros de esta página no modifican los resultados de las demás páginas.",
    "en": "Search and filters on this page do not affect results on other pages.",
    "fr": "La recherche et les filtres de cette page ne modifient pas les résultats des autres pages.",
    "de": "Suche und Filter dieser Seite ändern die Ergebnisse anderer Seiten nicht."
  },
  "Não encontramos ofertas para esta pesquisa.": {
    "es": "No se encontraron ofertas para esta búsqueda.",
    "en": "No offers found for this search.",
    "fr": "Aucune offre trouvée pour cette recherche.",
    "de": "Keine Angebote für diese Suche gefunden."
  },
  "Experimente procurar por HIFU, laser, cavitação ou outra especialidade.": {
    "es": "Pruebe a buscar HIFU, láser, cavitación u otra especialidad.",
    "en": "Try searching for HIFU, laser, cavitation or another speciality.",
    "fr": "Essayez HIFU, laser, cavitation ou une autre spécialité.",
    "de": "Versuchen Sie HIFU, Laser, Kavitation oder ein anderes Fachgebiet."
  },
  "Ver todas as categorias": {
    "es": "Ver todas las categorías",
    "en": "View all categories",
    "fr": "Voir toutes les catégories",
    "de": "Alle Kategorien ansehen"
  },
  "Procure um equipamento ou escolha uma especialidade": {
    "es": "Busque un equipo o elija una especialidad",
    "en": "Search for equipment or choose a speciality",
    "fr": "Recherchez un équipement ou choisissez une spécialité",
    "de": "Suchen Sie ein Gerät oder wählen Sie ein Fachgebiet"
  },
  "Escreva um termo acima ou explore as cinco categorias da montra.": {
    "es": "Introduzca un término arriba o explore las cinco categorías de la tienda.",
    "en": "Enter a search term above or explore the five storefront categories.",
    "fr": "Saisissez un terme ci-dessus ou explorez les cinq catégories.",
    "de": "Geben Sie oben einen Suchbegriff ein oder entdecken Sie die fünf Kategorien."
  },
  "Explorar categorias": {
    "es": "Explorar categorías",
    "en": "Explore categories",
    "fr": "Explorer les catégories",
    "de": "Kategorien entdecken"
  },
  "Gerir": {
    "es": "Gestionar",
    "en": "Manage",
    "fr": "Gérer",
    "de": "Verwalten"
  },
  "Seleção em preparação.": {
    "es": "Selección en preparación.",
    "en": "Selection in preparation.",
    "fr": "Sélection en préparation.",
    "de": "Auswahl in Vorbereitung."
  },
  "Observação com mais de 7 dias. Confirme o preço atual no parceiro.": {
    "es": "Dato de hace más de 7 días. Confirme el precio actual con el socio.",
    "en": "Observation over 7 days old. Confirm the current price with the partner.",
    "fr": "Donnée datant de plus de 7 jours. Vérifiez le prix actuel auprès du partenaire.",
    "de": "Die Angabe ist über 7 Tage alt. Prüfen Sie den aktuellen Preis beim Partner."
  },
  "Observação com mais de 7 dias. Confirme o prazo no parceiro.": {
    "es": "Dato de hace más de 7 días. Confirme el plazo con el socio.",
    "en": "Observation over 7 days old. Confirm the delivery time with the partner.",
    "fr": "Donnée datant de plus de 7 jours. Vérifiez le délai auprès du partenaire.",
    "de": "Die Angabe ist über 7 Tage alt. Prüfen Sie die Lieferzeit beim Partner."
  },
  "Vai continuar no parceiro; alguns links podem gerar comissão afiliada. Confirme a variante, o stock e o país de expedição no vendedor antes de pagar.": {
    "es": "Continuará en el sitio del socio; algunos enlaces pueden generar una comisión. Confirme la variante, las existencias y el país de envío antes de pagar.",
    "en": "You will continue on the partner's site; some links may earn a commission. Check the variant, stock and dispatch country before paying.",
    "fr": "Vous allez poursuivre sur le site du partenaire ; certains liens peuvent générer une commission. Vérifiez la variante, le stock et le pays d'expédition avant de payer.",
    "de": "Sie wechseln zum Partner; einige Links können Provisionen auslösen. Prüfen Sie Variante, Lagerbestand und Versandland vor der Zahlung."
  },
  "Pesquise, filtre e compare até três ofertas. Os valores são observações do parceiro, não preços garantidos.": {
    "es": "Busque, filtre y compare hasta tres ofertas. Los importes son datos observados del socio, no precios garantizados.",
    "en": "Search, filter and compare up to three offers. Amounts are observed partner data, not guaranteed prices.",
    "fr": "Recherchez, filtrez et comparez jusqu'à trois offres. Les montants sont des données constatées, pas des prix garantis.",
    "de": "Suchen, filtern und vergleichen Sie bis zu drei Angebote. Die Beträge sind beobachtete Partnerdaten, keine garantierten Preise."
  },
  "Preço observado (EUR)": {
    "es": "Precio observado (EUR)",
    "en": "Observed price (EUR)",
    "fr": "Prix constaté (EUR)",
    "de": "Erfasster Preis (EUR)"
  },
  "Até 500 €": {
    "es": "Hasta 500 €",
    "en": "Up to €500",
    "fr": "Jusqu'à 500 €",
    "de": "Bis 500 €"
  },
  "Até 1 000 €": {
    "es": "Hasta 1.000 €",
    "en": "Up to €1,000",
    "fr": "Jusqu'à 1 000 €",
    "de": "Bis 1.000 €"
  },
  "Até 2 500 €": {
    "es": "Hasta 2.500 €",
    "en": "Up to €2,500",
    "fr": "Jusqu'à 2 500 €",
    "de": "Bis 2.500 €"
  },
  "Até 5 000 €": {
    "es": "Hasta 5.000 €",
    "en": "Up to €5,000",
    "fr": "Jusqu'à 5 000 €",
    "de": "Bis 5.000 €"
  },
  "Preços de moedas diferentes não são comparados nem convertidos. Ofertas sem preço ficam no fim.": {
    "es": "No se comparan ni convierten precios en distintas monedas. Las ofertas sin precio aparecen al final.",
    "en": "Prices in different currencies are neither compared nor converted. Offers without prices appear last.",
    "fr": "Les prix dans différentes devises ne sont ni comparés ni convertis. Les offres sans prix apparaissent à la fin.",
    "de": "Preise in verschiedenen Währungen werden weder verglichen noch umgerechnet. Angebote ohne Preis stehen am Ende."
  },
  "Não foram encontradas ofertas para estes filtros. Experimente outros termos ou limpe os filtros.": {
    "es": "No se encontraron ofertas para estos filtros. Pruebe otros términos o borre los filtros.",
    "en": "No offers match these filters. Try other terms or clear the filters.",
    "fr": "Aucune offre ne correspond à ces filtres. Essayez d'autres termes ou effacez les filtres.",
    "de": "Keine Angebote entsprechen diesen Filtern. Versuchen Sie andere Begriffe oder löschen Sie die Filter."
  },
  "Preços e logística são dados observados que devem ser confirmados na AliExpress. Comparar não envia informação para terceiros.": {
    "es": "Los precios y los datos de envío son observaciones que deben confirmarse en AliExpress. Comparar no envía información a terceros.",
    "en": "Prices and delivery information are observed data to confirm on AliExpress. Comparing does not send information to third parties.",
    "fr": "Les prix et les informations logistiques sont des données à vérifier sur AliExpress. La comparaison n'envoie aucune donnée à des tiers.",
    "de": "Preise und Lieferangaben sind Beobachtungen, die auf AliExpress zu prüfen sind. Beim Vergleichen werden keine Daten an Dritte gesendet."
  },
  "Relação comercial": {
    "es": "Relación comercial",
    "en": "Commercial relationship",
    "fr": "Relation commerciale",
    "de": "Geschäftliche Beziehung"
  },
  "Alguns links do Lowcost Europa são links de afiliado.": {
    "es": "Algunos enlaces de Lowcost Europa son enlaces de afiliación.",
    "en": "Some Lowcost Europa links are affiliate links.",
    "fr": "Certains liens de Lowcost Europa sont des liens d'affiliation.",
    "de": "Einige Links auf Lowcost Europa sind Affiliate-Links."
  },
  "Quando uma compra elegível ocorre depois de um encaminhamento, o Lowcost Europa pode receber uma comissão do vendedor ou da plataforma.": {
    "es": "Si se realiza una compra apta tras acceder mediante un enlace, Lowcost Europa puede recibir una comisión del vendedor o la plataforma.",
    "en": "When an eligible purchase follows a referral, Lowcost Europa may receive a commission from the seller or platform.",
    "fr": "Si un achat admissible suit une redirection, Lowcost Europa peut recevoir une commission du vendeur ou de la plateforme.",
    "de": "Wenn nach einer Weiterleitung ein provisionsfähiger Kauf erfolgt, kann Lowcost Europa eine Provision vom Verkäufer oder der Plattform erhalten."
  },
  "Uma comissão não é garantida em cada clique ou em cada compra. A relação de afiliado não é escondida e não deve ser interpretada como uma avaliação independente de cada vendedor.": {
    "es": "No se garantiza una comisión por cada clic o compra. La relación de afiliación se divulga y no debe interpretarse como una evaluación independiente de cada vendedor.",
    "en": "A commission is not guaranteed for every click or purchase. The affiliate relationship is disclosed and should not be taken as an independent assessment of each seller.",
    "fr": "Une commission n'est pas garantie à chaque clic ou achat. La relation d'affiliation est déclarée et ne constitue pas une évaluation indépendante de chaque vendeur.",
    "de": "Eine Provision ist nicht für jeden Klick oder Kauf garantiert. Die Affiliate-Beziehung wird offengelegt und ist keine unabhängige Bewertung der einzelnen Verkäufer."
  },
  "O Lowcost Europa não apresenta a comissão como um aumento obrigatório do preço pago pelo comprador. O preço e as condições finais são os mostrados pelo vendedor.": {
    "es": "Lowcost Europa no presenta la comisión como un recargo obligatorio para el comprador. El precio y las condiciones finales son los que muestra el vendedor.",
    "en": "Lowcost Europa does not present the commission as a mandatory surcharge for buyers. Final prices and terms are those shown by the seller.",
    "fr": "Lowcost Europa ne présente pas la commission comme un supplément obligatoire pour l'acheteur. Le prix et les conditions définitifs sont ceux du vendeur.",
    "de": "Lowcost Europa stellt die Provision nicht als verpflichtenden Aufpreis für Käufer dar. Maßgeblich sind Preis und Bedingungen des Verkäufers."
  },
  "Para dúvidas sobre a relação de afiliado ou transparência, consulte": {
    "es": "Si tiene preguntas sobre afiliación o transparencia, consulte",
    "en": "For questions about affiliation or transparency, see",
    "fr": "Pour toute question sur l'affiliation ou la transparence, consultez",
    "de": "Bei Fragen zu Affiliate-Links oder Transparenz siehe"
  },
  "O Lowcost Europa apresenta uma seleção curada de ofertas e informação factual disponível no momento da observação.": {
    "es": "Lowcost Europa presenta una selección editorial de ofertas y datos disponibles en el momento de su observación.",
    "en": "Lowcost Europa presents a curated selection of offers and factual information available when observed.",
    "fr": "Lowcost Europa présente une sélection éditoriale d'offres et d'informations factuelles disponibles au moment du relevé.",
    "de": "Lowcost Europa zeigt eine redaktionelle Auswahl von Angeboten und Fakten, die zum Erfassungszeitpunkt verfügbar waren."
  },
  "Selecionamos ofertas para análise editorial.": {
    "es": "Seleccionamos ofertas para su análisis editorial.",
    "en": "We select offers for editorial review.",
    "fr": "Nous sélectionnons des offres pour une analyse éditoriale.",
    "de": "Wir wählen Angebote zur redaktionellen Prüfung aus."
  },
  "Mostramos preço, disponibilidade e logística apenas quando existem dados observados.": {
    "es": "Mostramos precio, disponibilidad y envío solo cuando hay datos observados.",
    "en": "We show price, availability and delivery details only when observed data exists.",
    "fr": "Nous affichons prix, disponibilité et livraison uniquement lorsque des données ont été constatées.",
    "de": "Wir zeigen Preis, Verfügbarkeit und Lieferung nur bei tatsächlich erfassten Daten."
  },
  "Ao escolher": {
    "es": "Al seleccionar",
    "en": "When you select",
    "fr": "Lorsque vous choisissez",
    "de": "Wenn Sie"
  },
  "Ver oferta": {
    "es": "Ver oferta",
    "en": "View offer",
    "fr": "Voir l'offre",
    "de": "Angebot ansehen"
  },
  ", é encaminhado para o site do vendedor.": {
    "es": ", accederá al sitio del vendedor.",
    "en": ", you are taken to the seller's website.",
    "fr": ", vous accédez au site du vendeur.",
    "de": ", werden Sie zur Website des Verkäufers weitergeleitet."
  },
  "A compra, o pagamento, a expedição e o pós-venda acontecem no vendedor.": {
    "es": "La compra, el pago, el envío y el servicio posventa corresponden al vendedor.",
    "en": "Purchase, payment, dispatch and after-sales support are handled by the seller.",
    "fr": "L'achat, le paiement, l'expédition et le service après-vente sont assurés par le vendeur.",
    "de": "Kauf, Zahlung, Versand und Kundendienst erfolgen beim Verkäufer."
  },
  "Algumas ligações são de afiliado e o Lowcost Europa pode receber comissão numa compra elegível.": {
    "es": "Algunos enlaces son de afiliación y Lowcost Europa puede recibir una comisión por una compra apta.",
    "en": "Some links are affiliate links and Lowcost Europa may receive a commission on eligible purchases.",
    "fr": "Certains liens sont affiliés et Lowcost Europa peut recevoir une commission sur un achat admissible.",
    "de": "Einige Links sind Affiliate-Links und Lowcost Europa kann bei provisionsfähigen Käufen eine Provision erhalten."
  },
  "O Lowcost Europa não processa o pagamento da compra. Preços, disponibilidade e estimativas logísticas podem mudar no vendedor.": {
    "es": "Lowcost Europa no procesa los pagos. Los precios, la disponibilidad y las estimaciones de envío pueden cambiar en el sitio del vendedor.",
    "en": "Lowcost Europa does not process payments. Prices, availability and delivery estimates may change on the seller's website.",
    "fr": "Lowcost Europa ne traite pas les paiements. Prix, disponibilité et délais estimés peuvent changer sur le site du vendeur.",
    "de": "Lowcost Europa wickelt keine Zahlungen ab. Preise, Verfügbarkeit und Lieferprognosen können sich beim Verkäufer ändern."
  },
  "Quando mostramos uma estimativa baseada apenas na pesquisa, como 5 dias, isso é uma indicação observada e não uma garantia de entrega.": {
    "es": "Cuando mostramos una estimación basada solo en la búsqueda, como 5 días, se trata de un dato observado y no de una garantía de entrega.",
    "en": "When we show a search-based estimate, such as five days, it is observed information, not a delivery guarantee.",
    "fr": "Lorsqu'un délai est estimé à partir de la recherche, par exemple cinq jours, il s'agit d'une indication constatée et non d'une garantie de livraison.",
    "de": "Eine aus Suchdaten abgeleitete Angabe wie fünf Tage ist eine Beobachtung und keine Liefergarantie."
  },
  "Utilização do site": {
    "es": "Uso del sitio web",
    "en": "Website use",
    "fr": "Utilisation du site",
    "de": "Nutzung der Website"
  },
  "Termos de Utilização": {
    "es": "Condiciones de uso",
    "en": "Terms of use",
    "fr": "Conditions d'utilisation",
    "de": "Nutzungsbedingungen"
  },
  "O Lowcost Europa seleciona, organiza e apresenta produtos e ofertas disponibilizados por vendedores ou plataformas externas.": {
    "es": "Lowcost Europa selecciona, organiza y presenta productos y ofertas de vendedores o plataformas externas.",
    "en": "Lowcost Europa selects, organises and displays products and offers from external sellers or platforms.",
    "fr": "Lowcost Europa sélectionne, organise et présente des produits et offres de vendeurs ou plateformes externes.",
    "de": "Lowcost Europa wählt Produkte und Angebote externer Verkäufer oder Plattformen aus, ordnet und zeigt sie an."
  },
  "Compra em plataformas externas": {
    "es": "Compra en plataformas externas",
    "en": "Purchases on external platforms",
    "fr": "Achats sur des plateformes externes",
    "de": "Käufe auf externen Plattformen"
  },
  "O Lowcost Europa não processa diretamente o pagamento das compras apresentadas. Ao escolher comprar, o utilizador é encaminhado para o vendedor ou plataforma externa, onde a transação é concluída.": {
    "es": "Lowcost Europa no procesa directamente los pagos. Al elegir comprar, el usuario accede al vendedor o plataforma externa, donde se completa la transacción.",
    "en": "Lowcost Europa does not directly process purchase payments. When choosing to buy, users are directed to the external seller or platform, where the transaction is completed.",
    "fr": "Lowcost Europa ne traite pas directement les paiements. Lors d'un achat, l'utilisateur est redirigé vers le vendeur ou la plateforme externe où la transaction est conclue.",
    "de": "Lowcost Europa wickelt Kaufzahlungen nicht selbst ab. Beim Kaufwunsch werden Nutzer zum externen Verkäufer oder zur Plattform weitergeleitet, wo die Transaktion erfolgt."
  },
  "O preço final, o stock, a disponibilidade, o pagamento, a entrega, as devoluções, as garantias e o apoio relativo à encomenda estão sujeitos às condições do vendedor ou da plataforma externa.": {
    "es": "El precio final, las existencias, la disponibilidad, el pago, la entrega, las devoluciones, las garantías y la asistencia se rigen por las condiciones del vendedor o plataforma externa.",
    "en": "Final prices, stock, availability, payment, delivery, returns, warranties and order support are subject to the terms of the seller or external platform.",
    "fr": "Prix final, stock, disponibilité, paiement, livraison, retours, garanties et assistance relèvent des conditions du vendeur ou de la plateforme externe.",
    "de": "Endpreis, Bestand, Verfügbarkeit, Zahlung, Lieferung, Rücksendungen, Garantien und Bestellservice unterliegen den Bedingungen des Verkäufers oder der externen Plattform."
  },
  "Os preços e a disponibilidade apresentados no Lowcost Europa podem alterar-se entre o momento da consulta e a abertura da página externa.": {
    "es": "Los precios y la disponibilidad mostrados pueden cambiar entre la consulta y la apertura de la página externa.",
    "en": "Prices and availability shown on Lowcost Europa may change between viewing the listing and opening the external page.",
    "fr": "Les prix et la disponibilité affichés sur Lowcost Europa peuvent changer entre la consultation et l'ouverture de la page externe.",
    "de": "Die bei Lowcost Europa gezeigten Preise und Verfügbarkeiten können sich bis zum Öffnen der externen Seite ändern."
  },
  "Relação de afiliado": {
    "es": "Relación de afiliación",
    "en": "Affiliate relationship",
    "fr": "Relation d'affiliation",
    "de": "Affiliate-Beziehung"
  },
  "Alguns links do Lowcost Europa são links de afiliado. O Lowcost Europa pode receber uma comissão quando uma compra elegível ocorre após um encaminhamento.": {
    "es": "Algunos enlaces son de afiliación. Lowcost Europa puede recibir una comisión por compras aptas realizadas tras una redirección.",
    "en": "Some Lowcost Europa links are affiliate links. Lowcost Europa may earn a commission on eligible purchases following a referral.",
    "fr": "Certains liens de Lowcost Europa sont affiliés. Lowcost Europa peut recevoir une commission lorsqu'un achat admissible suit une redirection.",
    "de": "Einige Links auf Lowcost Europa sind Affiliate-Links. Lowcost Europa kann bei provisionsfähigen Käufen nach einer Weiterleitung eine Provision erhalten."
  },
  "Essa comissão não é apresentada como um custo adicional obrigatório para o comprador.": {
    "es": "Esa comisión no se presenta como un coste adicional obligatorio para el comprador.",
    "en": "This commission is not presented as a mandatory additional cost to the buyer.",
    "fr": "Cette commission n'est pas présentée comme un coût supplémentaire obligatoire pour l'acheteur.",
    "de": "Diese Provision wird nicht als verpflichtender Zusatzpreis für Käufer dargestellt."
  },
  "Antes de concluir a compra": {
    "es": "Antes de finalizar la compra",
    "en": "Before completing a purchase",
    "fr": "Avant de finaliser l'achat",
    "de": "Vor Abschluss des Kaufs"
  },
  "Antes de concluir a compra, confirme na plataforma externa o produto, o preço, o stock, a entrega, as condições aplicáveis e os restantes dados finais da transação.": {
    "es": "Antes de finalizar, compruebe en la plataforma externa el producto, el precio, las existencias, la entrega y las condiciones aplicables.",
    "en": "Before buying, verify the product, price, stock, delivery, applicable terms and other final transaction details on the external platform.",
    "fr": "Avant l'achat, vérifiez sur la plateforme externe le produit, le prix, le stock, la livraison, les conditions et les détails définitifs.",
    "de": "Prüfen Sie vor dem Kauf auf der externen Plattform Produkt, Preis, Bestand, Lieferung, Bedingungen und alle weiteren abschließenden Angaben."
  },
  "Mais informação": {
    "es": "Más información",
    "en": "More information",
    "fr": "Plus d'informations",
    "de": "Weitere Informationen"
  },
  "Consulte também as páginas de": {
    "es": "Consulte también las páginas de",
    "en": "Also see the pages on",
    "fr": "Consultez également les pages",
    "de": "Weitere Informationen finden Sie unter"
  },
  "Contacto institucional": {
    "es": "Contacto institucional",
    "en": "Institutional contact",
    "fr": "Contact institutionnel",
    "de": "Offizieller Kontakt"
  },
  "Use estes canais para questões sobre o site Lowcost Europa, informação apresentada, links afiliados, correções factuais e transparência da plataforma.": {
    "es": "Utilice estos canales para preguntas sobre Lowcost Europa, la información mostrada, los enlaces de afiliación, correcciones y transparencia.",
    "en": "Use these channels for questions about Lowcost Europa, displayed information, affiliate links, factual corrections and platform transparency.",
    "fr": "Utilisez ces canaux pour toute question sur Lowcost Europa, les informations affichées, l'affiliation, les corrections factuelles et la transparence.",
    "de": "Nutzen Sie diese Kontaktwege für Fragen zur Website, zu angezeigten Angaben, Affiliate-Links, Korrekturen und Transparenz."
  },
  "Compras, pagamentos, expedição, devoluções e suporte da encomenda são tratados pelo vendedor ou pela plataforma de venda, não pelo Lowcost Europa.": {
    "es": "Las compras, pagos, envíos, devoluciones y asistencia al pedido corresponden al vendedor o plataforma, no a Lowcost Europa.",
    "en": "Purchases, payments, shipping, returns and order support are handled by the seller or selling platform, not by Lowcost Europa.",
    "fr": "Les achats, paiements, expéditions, retours et l'assistance aux commandes sont assurés par le vendeur ou la plateforme, pas par Lowcost Europa.",
    "de": "Käufe, Zahlungen, Versand, Rücksendungen und Bestellservice werden vom Verkäufer oder der Plattform bearbeitet, nicht von Lowcost Europa."
  },
  "Esta página explica, em linguagem simples, que informação é registada atualmente quando o Lowcost Europa encaminha um visitante para uma oferta externa.": {
    "es": "Esta página explica de forma sencilla qué información se registra actualmente cuando Lowcost Europa dirige a un visitante a una oferta externa.",
    "en": "This page explains, in plain language, what is currently recorded when Lowcost Europa refers a visitor to an external offer.",
    "fr": "Cette page explique simplement les informations actuellement enregistrées lorsque Lowcost Europa redirige un visiteur vers une offre externe.",
    "de": "Diese Seite erklärt einfach, welche Informationen derzeit erfasst werden, wenn Lowcost Europa Besucher zu externen Angeboten weiterleitet."
  },
  "Registo de encaminhamentos": {
    "es": "Registro de redirecciones",
    "en": "Referral records",
    "fr": "Enregistrement des redirections",
    "de": "Weiterleitungsprotokoll"
  },
  "Quando ocorre um encaminhamento válido para uma oferta externa, o Lowcost Europa pode registar a oferta e a data/hora do clique.": {
    "es": "Cuando se produce una redirección válida a una oferta externa, Lowcost Europa puede registrar la oferta y la fecha y hora del clic.",
    "en": "When a valid referral to an external offer occurs, Lowcost Europa may record the offer and the date and time of the click.",
    "fr": "Lors d'une redirection valide vers une offre externe, Lowcost Europa peut enregistrer l'offre ainsi que la date et l'heure du clic.",
    "de": "Bei einer gültigen Weiterleitung zu einem externen Angebot kann Lowcost Europa das Angebot sowie Datum und Uhrzeit des Klicks erfassen."
  },
  "Esse registo de encaminhamento da aplicação não guarda endereço IP, dados de identificação do navegador ou dispositivo, identificador de sessão, impressão digital do dispositivo, página de origem, e-mail, localização ou outro identificador persistente.": {
    "es": "Este registro de redirección de la aplicación no almacena dirección IP, datos identificativos del navegador o dispositivo, identificador de sesión, huella digital, página de origen, correo electrónico, ubicación ni otros identificadores persistentes.",
    "en": "This application referral record does not store IP addresses, browser or device identification data, session identifiers, device fingerprints, referrer pages, email addresses, locations or other persistent identifiers.",
    "fr": "Cet enregistrement applicatif des redirections ne conserve ni adresse IP, ni données d'identification du navigateur ou de l'appareil, ni identifiant de session, empreinte numérique, page d'origine, e-mail, localisation ou autre identifiant persistant.",
    "de": "Dieser Weiterleitungsdatensatz der Anwendung speichert keine IP-Adresse, Browser- oder Gerätekennungen, Sitzungs-IDs, Fingerabdrücke, Herkunftsseiten, E-Mail-Adressen, Standorte oder sonstigen dauerhaften Kennungen."
  },
  "Um clique registado não significa utilizador único, compra, conversão ou comissão.": {
    "es": "Un clic registrado no significa usuario único, compra, conversión ni comisión.",
    "en": "A recorded click does not mean a unique user, purchase, conversion or commission.",
    "fr": "Un clic enregistré ne signifie pas un utilisateur unique, un achat, une conversion ou une commission.",
    "de": "Ein erfasster Klick bedeutet weder einen eindeutigen Nutzer noch einen Kauf, eine Conversion oder eine Provision."
  },
  "Páginas públicas": {
    "es": "Páginas públicas",
    "en": "Public pages",
    "fr": "Pages publiques",
    "de": "Öffentliche Seiten"
  },
  "As páginas públicas atuais não utilizam ferramentas de análise de utilização.": {
    "es": "Las páginas públicas actuales no usan herramientas de análisis de uso.",
    "en": "Current public pages do not use usage analytics tools.",
    "fr": "Les pages publiques actuelles n'utilisent pas d'outils d'analyse d'utilisation.",
    "de": "Die aktuellen öffentlichen Seiten verwenden keine Nutzungsanalyse-Tools."
  },
  "Logs técnicos": {
    "es": "Registros técnicos",
    "en": "Technical logs",
    "fr": "Journaux techniques",
    "de": "Technische Protokolle"
  },
  "Separadamente do registo de encaminhamento, a infraestrutura que suporta o site pode manter logs técnicos de acesso e erro para operação e segurança. Esses logs podem incluir, por exemplo, o endereço IP e a URL solicitada.": {
    "es": "Al margen del registro de redirecciones, la infraestructura del sitio puede conservar registros técnicos de acceso y error para su funcionamiento y seguridad. Pueden incluir la dirección IP y la URL solicitada.",
    "en": "Separately from application referral records, the infrastructure may keep technical access and error logs for operations and security. These may include IP addresses and requested URLs.",
    "fr": "Indépendamment des redirections enregistrées par l'application, l'infrastructure peut conserver des journaux techniques d'accès et d'erreurs pour l'exploitation et la sécurité, notamment les adresses IP et les URL demandées.",
    "de": "Unabhängig von den Weiterleitungsdaten kann die Infrastruktur technische Zugriffs- und Fehlerprotokolle für Betrieb und Sicherheit speichern, etwa IP-Adressen und aufgerufene URLs."
  },
  "Para questões de privacidade, transparência ou correções factuais, contacte": {
    "es": "Para cuestiones de privacidad, transparencia o correcciones, contacte con",
    "en": "For questions about privacy, transparency or factual corrections, contact",
    "fr": "Pour toute question relative à la confidentialité, la transparence ou des corrections, contactez",
    "de": "Bei Fragen zu Datenschutz, Transparenz oder sachlichen Korrekturen kontaktieren Sie"
  },
  "ou consulte a página": {
    "es": "o consulte la página",
    "en": "or see the page",
    "fr": "ou consultez la page",
    "de": "oder besuchen Sie die Seite"
  },
  "Idioma": {
    "es": "Idioma",
    "en": "Language",
    "fr": "Langue",
    "de": "Sprache"
  },
  "Aplicar": {
    "es": "Aplicar",
    "en": "Apply",
    "fr": "Appliquer",
    "de": "Übernehmen"
  },
  "0 equipamentos selecionados": {
    "es": "0 equipos seleccionados",
    "en": "0 pieces of equipment selected",
    "fr": "0 équipements sélectionnés",
    "de": "0 Geräte ausgewählt"
  },
  "de 3 equipamentos selecionados": {
    "es": "de 3 equipos seleccionados",
    "en": "of 3 pieces of equipment selected",
    "fr": "sur 3 équipements sélectionnés",
    "de": "von 3 Geräten ausgewählt"
  },
  "ofertas nesta lista": {
    "es": "ofertas en esta lista",
    "en": "offers in this list",
    "fr": "offres dans cette liste",
    "de": "Angebote in dieser Liste"
  },
  "de": {
    "es": "de",
    "en": "of",
    "fr": "sur",
    "de": "von"
  },
  "Limite de três equipamentos. Retire um para acrescentar outro.": {
    "es": "Límite de tres equipos. Quite uno para añadir otro.",
    "en": "You can compare up to three pieces of equipment. Remove one to add another.",
    "fr": "Limite de trois équipements. Retirez-en un pour en ajouter un autre.",
    "de": "Sie können bis zu drei Geräte vergleichen. Entfernen Sie eines, um ein anderes hinzuzufügen."
  },
  "O limite aplica-se só a preços em EUR; valores de outras moedas não são convertidos.": {
    "es": "El límite solo se aplica a precios en EUR; los importes en otras monedas no se convierten.",
    "en": "The limit only applies to prices in EUR; other currencies are not converted.",
    "fr": "La limite s'applique uniquement aux prix en EUR ; les autres devises ne sont pas converties.",
    "de": "Das Limit gilt nur für Preise in EUR; andere Währungen werden nicht umgerechnet."
  },
  "+ Comparar equipamento": {
    "es": "+ Comparar equipo",
    "en": "+ Compare equipment",
    "fr": "+ Comparer l'équipement",
    "de": "+ Gerät vergleichen"
  },
  "Na categoria": {
    "es": "En la categoría",
    "en": "In category",
    "fr": "Dans la catégorie",
    "de": "In Kategorie"
  },
  "Comparação": {
    "es": "Comparación",
    "en": "Comparison",
    "fr": "Comparaison",
    "de": "Vergleich"
  },
  "Resultados": {
    "es": "Resultados",
    "en": "Results",
    "fr": "Résultats",
    "de": "Ergebnisse"
  },
  "Famílias de produtos": {
    "es": "Familias de productos",
    "en": "Product families",
    "fr": "Familles de produits",
    "de": "Produktfamilien"
  },
  "Página": {
    "es": "Página",
    "en": "Page",
    "fr": "Page",
    "de": "Seite"
  },
  "resultado para": {
    "es": "resultado para",
    "en": "result for",
    "fr": "résultat pour",
    "de": "Ergebnis für"
  },
  "resultados para": {
    "es": "resultados para",
    "en": "results for",
    "fr": "résultats pour",
    "de": "Ergebnisse für"
  },
  "Uma seleção de equipamentos": {
    "es": "Una selección de equipos",
    "en": "A selection of equipment",
    "fr": "Une sélection d'équipements",
    "de": "Eine Geräteauswahl"
  },
  "Cookie de idioma": {
    "es": "Cookie de idioma",
    "en": "Language cookie",
    "fr": "Cookie de langue",
    "de": "Sprach-Cookie"
  },
  "A escolha manual do idioma é guardada num cookie funcional, sem análise de utilização nem geolocalização por IP.": {
    "es": "La elección manual del idioma se guarda en una cookie funcional, sin análisis de uso ni geolocalización por IP.",
    "en": "Your manual language choice is saved in a functional cookie, without usage analytics or IP geolocation.",
    "fr": "Votre choix manuel de langue est enregistré dans un cookie fonctionnel, sans analyse d'utilisation ni géolocalisation par IP.",
    "de": "Ihre manuelle Sprachauswahl wird in einem funktionalen Cookie gespeichert, ohne Nutzungsanalyse oder IP-Geolokalisierung."
  },
  "Como organizamos a seleção": {
    "es": "Cómo organizamos la selección",
    "en": "How we organise the selection",
    "fr": "Comment nous organisons la sélection",
    "de": "So ordnen wir die Auswahl"
  },
  "Algumas categorias do catálogo": {
    "es": "Algunas categorías del catálogo",
    "en": "Some catalogue categories",
    "fr": "Quelques catégories du catalogue",
    "de": "Einige Katalogkategorien"
  },
  "Laser estético": {
    "es": "Láser estético",
    "en": "Aesthetic laser",
    "fr": "Laser esthétique",
    "de": "Ästhetiklaser"
  },
  "Cavitação e radiofrequência": {
    "es": "Cavitación y radiofrecuencia",
    "en": "Cavitation and radiofrequency",
    "fr": "Cavitation et radiofréquence",
    "de": "Kavitation und Radiofrequenz"
  },
  "Hidrodermoabrasão": {
    "es": "Hidrodermoabrasión",
    "en": "Hydrodermabrasion",
    "fr": "Hydrodermabrasion",
    "de": "Hydrodermabrasion"
  },
  "Pressoterapia": {
    "es": "Presoterapia",
    "en": "Pressotherapy",
    "fr": "Pressothérapie",
    "de": "Pressotherapie"
  },
  "HIFU": {
    "es": "HIFU",
    "en": "HIFU",
    "fr": "HIFU",
    "de": "HIFU"
  },
  "Laser de díodo": {
    "es": "Láser de diodo",
    "en": "Diode laser",
    "fr": "Laser diode",
    "de": "Diodenlaser"
  },
  "Tratamentos corporais": {
    "es": "Tratamientos corporales",
    "en": "Body treatments",
    "fr": "Soins corporels",
    "de": "Körperbehandlungen"
  },
  "Idioma pelo IP": {
    "es": "Idioma por IP",
    "en": "Language by IP address",
    "fr": "Langue selon l'adresse IP",
    "de": "Sprache nach IP-Adresse"
  },
  "O idioma da montra é escolhido pelo país associado ao IP público, incluindo VPN: Portugal em português, Espanha em espanhol, França em francês, Alemanha em alemão e restantes países em inglês. A consulta à base de países é feita localmente, sem guardar o IP para esta escolha.": {
    "es": "El idioma del sitio se elige según el país asociado a la IP pública, incluidas las VPN: Portugal en portugués, España en español, Francia en francés, Alemania en alemán y los demás países en inglés. La consulta a la base de datos de países se hace localmente, sin guardar la IP para esta elección.",
    "en": "The storefront language is chosen by the country associated with the public IP address, including VPNs: Portuguese for Portugal, Spanish for Spain, French for France, German for Germany, and English for all other countries. The country database is queried locally without storing the IP address for this selection.",
    "fr": "La langue du site dépend du pays associé à l'adresse IP publique, y compris en cas de VPN : portugais pour le Portugal, espagnol pour l'Espagne, français pour la France, allemand pour l'Allemagne et anglais pour les autres pays. La base de données des pays est consultée localement, sans enregistrer l'adresse IP pour ce choix.",
    "de": "Die Sprache der Website richtet sich nach dem Land der öffentlichen IP-Adresse, auch bei Verwendung eines VPN: Portugiesisch für Portugal, Spanisch für Spanien, Französisch für Frankreich, Deutsch für Deutschland und Englisch für alle anderen Länder. Die Länder-Datenbank wird lokal abgefragt, ohne die IP-Adresse für diese Auswahl zu speichern."
  },
  "Mensagens de contacto": {
    "es": "Mensajes de contacto",
    "en": "Contact messages",
    "fr": "Messages de contact",
    "de": "Kontaktanfragen"
  },
  "Quando envia um e-mail para o nosso endereço institucional, os dados que incluir (como o seu endereço de e-mail e a mensagem) são tratados por serviços de correio eletrónico para podermos receber e responder. As mensagens podem ser encaminhadas para uma caixa de gestão privada.": {
    "es": "Cuando nos envía un correo electrónico, los datos que incluya (como su dirección de correo y el mensaje) son tratados por servicios de correo electrónico para que podamos recibirlo y responder. Los mensajes pueden reenviarse a una cuenta de gestión privada.",
    "en": "When you email our business address, the details you include (such as your email address and message) are processed by email services so we can receive and reply. Messages may be forwarded to a private management mailbox.",
    "fr": "Lorsque vous écrivez à notre adresse professionnelle, les informations fournies (telles que votre adresse e-mail et votre message) sont traitées par des services de messagerie pour nous permettre de recevoir votre demande et d'y répondre. Les messages peuvent être transférés vers une boîte de gestion privée.",
    "de": "Wenn Sie uns an unsere geschäftliche E-Mail-Adresse schreiben, werden Ihre Angaben (z. B. Ihre E-Mail-Adresse und Ihre Nachricht) von E-Mail-Diensten verarbeitet, damit wir die Nachricht empfangen und beantworten können. Nachrichten können an ein privates Verwaltungspostfach weitergeleitet werden."
  }
}


UI_TRANSLATIONS.update({
  "Identificação do operador": {
    "en": "Operator identification",
    "es": "Identificación del operador",
    "fr": "Identification de l’opérateur",
    "de": "Angaben zum Betreiber"
  },
  "Operador e responsável pelo tratamento": {
    "en": "Operator and data controller",
    "es": "Operador y responsable del tratamiento",
    "fr": "Opérateur et responsable du traitement",
    "de": "Betreiber und Verantwortlicher"
  },
  "Morada": {
    "en": "Address",
    "es": "Dirección",
    "fr": "Adresse",
    "de": "Anschrift"
  },
  "Finalidades, fundamento e conservação": {
    "en": "Purposes, legal basis and retention",
    "es": "Finalidades, base jurídica y conservación",
    "fr": "Finalités, base juridique et conservation",
    "de": "Zwecke, Rechtsgrundlage und Aufbewahrung"
  },
  "Prestadores e serviços externos": {
    "en": "Providers and external services",
    "es": "Proveedores y servicios externos",
    "fr": "Prestataires et services externes",
    "de": "Anbieter und externe Dienste"
  },
  "Os seus direitos": {
    "en": "Your rights",
    "es": "Sus derechos",
    "fr": "Vos droits",
    "de": "Ihre Rechte"
  },
  "Os dados das mensagens são utilizados para responder ao contacto. Os logs técnicos servem a operação e a segurança do site. Estes tratamentos baseiam-se no interesse legítimo em responder às comunicações e manter o serviço seguro. A conservação é limitada ao tempo necessário para essas finalidades e para cumprir obrigações legais ou defender direitos.": {
    "en": "Message data is used to respond to your enquiry. Technical logs support website operations and security. This processing relies on our legitimate interest in responding to communications and keeping the service secure. Retention is limited to the time needed for those purposes and to meet legal obligations or defend legal rights.",
    "es": "Los datos de los mensajes se utilizan para responder a su consulta. Los registros técnicos sirven para operar y proteger el sitio. El tratamiento se basa en el interés legítimo de responder a las comunicaciones y mantener la seguridad del servicio. La conservación se limita al tiempo necesario para estas finalidades y para cumplir obligaciones legales o defender derechos.",
    "fr": "Les données des messages servent à répondre à votre demande. Les journaux techniques assurent le fonctionnement et la sécurité du site. Ces traitements reposent sur notre intérêt légitime à répondre aux communications et à sécuriser le service. La conservation est limitée à la durée nécessaire à ces finalités et au respect des obligations légales ou à la défense de droits.",
    "de": "Nachrichtendaten werden zur Beantwortung Ihrer Anfrage verwendet. Technische Protokolle dienen dem Betrieb und der Sicherheit der Website. Grundlage ist unser berechtigtes Interesse an der Beantwortung von Mitteilungen und am sicheren Betrieb. Die Aufbewahrung ist auf die für diese Zwecke sowie für gesetzliche Pflichten oder die Rechtsverteidigung erforderliche Dauer begrenzt."
  },
  "O alojamento é assegurado pela OVHcloud e o correio utiliza a Dynadot e uma caixa de gestão Gmail. Ao abrir WhatsApp ou AliExpress, passa a utilizar serviços externos sujeitos às respetivas políticas. Estes fornecedores podem tratar dados fora do Espaço Económico Europeu; consulte as informações sobre transferências internacionais e garantias nas suas políticas.": {
    "en": "Hosting is provided by OVHcloud and email uses Dynadot and a Gmail management mailbox. When you open WhatsApp or AliExpress, you use external services governed by their own policies. These providers may process data outside the European Economic Area; see their policies for information about international transfers and safeguards.",
    "es": "El alojamiento lo presta OVHcloud y el correo utiliza Dynadot y un buzón de gestión Gmail. Al abrir WhatsApp o AliExpress utiliza servicios externos sujetos a sus propias políticas. Estos proveedores pueden tratar datos fuera del Espacio Económico Europeo; consulte sus políticas sobre transferencias internacionales y garantías.",
    "fr": "L’hébergement est assuré par OVHcloud et la messagerie utilise Dynadot et une boîte de gestion Gmail. En ouvrant WhatsApp ou AliExpress, vous utilisez des services externes soumis à leurs propres politiques. Ces prestataires peuvent traiter des données hors de l’Espace économique européen ; consultez leurs politiques sur les transferts internationaux et les garanties.",
    "de": "Das Hosting erfolgt durch OVHcloud; E-Mails werden über Dynadot und ein Gmail-Verwaltungspostfach verarbeitet. Wenn Sie WhatsApp oder AliExpress öffnen, nutzen Sie externe Dienste mit eigenen Datenschutzregeln. Diese Anbieter können Daten außerhalb des Europäischen Wirtschaftsraums verarbeiten; Informationen zu internationalen Übermittlungen und Schutzmaßnahmen finden Sie in deren Richtlinien."
  },
  "Pode pedir acesso, retificação, apagamento, limitação, oposição e, quando aplicável, portabilidade dos seus dados através do e-mail indicado. Pode também apresentar reclamação à autoridade de proteção de dados competente, em Portugal a CNPD. O exercício de cada direito depende dos requisitos legais aplicáveis.": {
    "en": "You may request access, rectification, erasure, restriction, objection and, where applicable, portability of your data using the email address above. You may also complain to the competent data protection authority, the CNPD in Portugal. Each right is subject to the applicable legal requirements.",
    "es": "Puede solicitar acceso, rectificación, supresión, limitación, oposición y, cuando proceda, portabilidad de sus datos mediante el correo indicado. También puede reclamar ante la autoridad de protección de datos competente, la CNPD en Portugal. Cada derecho está sujeto a los requisitos legales aplicables.",
    "fr": "Vous pouvez demander l’accès, la rectification, l’effacement, la limitation, l’opposition et, le cas échéant, la portabilité de vos données à l’adresse e-mail indiquée. Vous pouvez également saisir l’autorité de protection des données compétente, la CNPD au Portugal. Chaque droit est soumis aux conditions légales applicables.",
    "de": "Über die angegebene E-Mail-Adresse können Sie Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch und gegebenenfalls Datenübertragbarkeit beantragen. Sie können sich auch bei der zuständigen Datenschutzbehörde beschweren, in Portugal der CNPD. Für jedes Recht gelten die jeweiligen gesetzlichen Voraussetzungen."
  }
})

def translate_ui(value, language):
    if not value:
        return value
    language = str(language or "pt-pt").lower().split("-")[0]
    if language == "pt":
        return value
    if language == "es":
        patterns = (
            (r"Estimativa indicada pela pesquisa: ([0-9]+) dias", "Estimación indicada en la búsqueda: {} días"),
            (r"Estimativa indicada no detalhe: ([0-9]+) dias", "Estimación indicada en el detalle: {} días"),
            (r"Pesquisa e detalhe indicaram ([0-9]+) dias", "La búsqueda y el detalle indicaron {} días"),
        )
        for pattern, translated in patterns:
            match = re.fullmatch(pattern, str(value))
            if match:
                return translated.format(match.group(1))
    return UI_TRANSLATIONS.get(str(value), {}).get(language, value)
