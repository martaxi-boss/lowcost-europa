"""Reviewed Portuguese and Spanish buyer guidance for the five existing public category URLs.

This is editorial decision support, not a product review or an offer assertion.
Do not infer the price, stock, shipping origin, warranty or capabilities of any
individual seller/SKU from these category-level questions. Do not create new
URLs or show buyer guides in languages without reviewed translations.
"""

PT_CATEGORY_GUIDES = {
    "cavitacao-rf-vacuum-corpo": {
        "title": "Máquinas de Cavitação e Radiofrequência | Lowcost Europa",
        "description": (
            "Compare máquinas de cavitação, radiofrequência e vácuo: funções "
            "incluídas, acessórios e condições do vendedor antes de comprar."
        ),
        "heading": "Como comparar máquinas de cavitação e radiofrequência",
        "intro": (
            "Cavitação, radiofrequência e vácuo podem surgir no mesmo anúncio, "
            "mas isso não confirma que todas as funções estejam incluídas em "
            "cada equipamento. Consulte a configuração da oferta concreta."
        ),
        "checks": (
            "Funções: identifique na ficha do modelo quais as tecnologias "
            "incluídas e se podem ser utilizadas de forma independente.",
            "Aplicadores: confirme os manípulos, os acessórios e os consumíveis "
            "fornecidos, bem como a disponibilidade de reposição.",
            "Apoio pós-compra: verifique documentação, assistência e condições "
            "de devolução diretamente com o vendedor.",
        ),
    },
    "hydrodermoabrasao-aqua-facial-multifuncoes": {
        "title": "Hidrodermoabrasão e Aqua Facial | Lowcost Europa",
        "description": (
            "Explore equipamentos Aqua Facial e hidrodermoabrasão. Saiba "
            "comparar ponteiras, consumíveis, limpeza e assistência antes de "
            "consultar a oferta do parceiro."
        ),
        "heading": "O que verificar num equipamento Aqua Facial",
        "intro": (
            "Os anúncios de hidrodermoabrasão, Aqua Facial e multifunções "
            "podem incluir acessórios diferentes. A designação comercial, "
            "por si só, não comprova o conteúdo da embalagem."
        ),
        "checks": (
            "Ponteiras e consumíveis: veja quais acompanham o equipamento e "
            "quais exigem compra separada ou reposição frequente.",
            "Higienização: procure no manual as instruções de limpeza, "
            "manutenção e substituição dos componentes do modelo concreto.",
            "Compatibilidade: compare as referências de acessórios, as "
            "condições de assistência e os custos totais informados pelo vendedor.",
        ),
    },
    "pressoterapia-vacuum-drenagem": {
        "title": "Equipamentos de Pressoterapia e RF Tecar | Lowcost Europa",
        "description": (
            "Compare equipamentos de pressoterapia e radiofrequência Tecar. "
            "Identifique a tecnologia da oferta, os acessórios e as condições "
            "de assistência do vendedor."
        ),
        "heading": "Pressoterapia e RF Tecar: diferenças a confirmar",
        "intro": (
            "Pressoterapia e radiofrequência Tecar são tecnologias distintas. "
            "Esta família do catálogo pode apresentar opções diferentes; "
            "confirme a função efetiva de cada equipamento antes de comparar preços."
        ),
        "checks": (
            "Tipo de equipamento: identifique se a oferta corresponde a "
            "pressoterapia, radiofrequência Tecar ou outra configuração documentada.",
            "Componentes: confirme os acessórios e aplicadores incluídos, "
            "tamanhos, compatibilidade e peças de substituição.",
            "Utilização profissional: verifique documentação do fabricante, "
            "requisitos de operação e suporte prestado pelo vendedor.",
        ),
    },
    "hifu": {
        "title": "Máquinas HIFU e EMS para Estética | Lowcost Europa",
        "description": (
            "Explore equipamentos HIFU e EMS para estética profissional. "
            "Compare tecnologias, cartuchos, aplicadores, documentação e "
            "condições de compra em Portugal."
        ),
        "heading": "HIFU e EMS: como comparar tecnologias diferentes",
        "intro": (
            "HIFU (ultrassons focalizados) e EMS (estimulação muscular elétrica) "
            "são tecnologias diferentes. Uma oferta pode incluir só uma função "
            "ou várias: confirme as especificações do modelo e da variante "
            "antes de comparar preços."
        ),
        "checks": (
            "Tecnologia: confirme se a ficha técnica identifica HIFU, EMS ou "
            "ambas as funções no modelo exato; o nome da categoria não comprova "
            "as funcionalidades de cada anúncio.",
            "Acessórios: verifique cartuchos para HIFU, aplicadores e componentes "
            "para EMS, referências compatíveis e custos de substituição.",
            "Condições: consulte manuais, requisitos de utilização profissional, "
            "assistência, garantia e custo final de entrega para Portugal.",
        ),
    },
    "diodo-laser-remocao-tatuagens-pigmentacao": {
        "title": "Laser Díodo e Remoção de Pigmentos | Lowcost Europa",
        "description": (
            "Explore equipamentos laser de díodo e remoção de pigmentos. "
            "Distinga as finalidades, confirme especificações e formação, "
            "e consulte as condições do fornecedor."
        ),
        "heading": "Laser de díodo e remoção de pigmentos não são equivalentes",
        "intro": (
            "Equipamentos destinados à depilação por laser de díodo e os "
            "utilizados na remoção de pigmentos ou tatuagens têm finalidades "
            "distintas. O nome desta categoria não garante que um aparelho "
            "execute ambas as funções."
        ),
        "checks": (
            "Finalidade: confirme na ficha técnica do equipamento a aplicação "
            "indicada pelo fabricante para o modelo anunciado.",
            "Requisitos de segurança: verifique a documentação aplicável, "
            "os requisitos profissionais e a formação necessária à operação.",
            "Assistência e compra: compare componentes, consumíveis, suporte "
            "técnico e condições contratuais do vendedor.",
        ),
    },
}


# Perguntas editoriais específicas do mercado português: apoio à compra, não
# alegações sobre produtos, stock, segurança certificada ou envio garantido.
# Não criar páginas artificiais nem schema FAQPage para estas perguntas.
PT_BUYING_QUESTIONS = {
    "cavitacao-rf-vacuum-corpo": (
        (
            "A cavitação, a radiofrequência e o vácuo vêm sempre na mesma máquina?",
            "Não. São funções distintas e um anúncio pode apresentar configurações "
            "diferentes. Confirme na descrição da variante escolhida os aplicadores "
            "incluídos, os modos disponíveis e as condições de utilização.",
        ),
        (
            "Como comparar duas máquinas de cavitação para um espaço profissional?",
            "Compare a configuração exata, os consumíveis, a manutenção indicada "
            "pelo fabricante e a disponibilidade de peças e assistência. Um preço "
            "inferior não demonstra que as duas ofertas incluam o mesmo conjunto.",
        ),
        (
            "O preço apresentado já inclui entrega e impostos para Portugal?",
            "Não é possível garantir esse total a partir da ficha desta página. "
            "Na plataforma do vendedor, confirme o código postal de destino, "
            "transporte, impostos aplicáveis, eventuais taxas e condições de devolução.",
        ),
    ),
    "hydrodermoabrasao-aqua-facial-multifuncoes": (
        (
            "O que devo confirmar num equipamento Aqua Facial multifunções?",
            "Veja na variante anunciada quais as ponteiras, recipientes, acessórios "
            "e funções efetivamente incluídos. O nome Aqua Facial não identifica "
            "por si só o conteúdo da embalagem.",
        ),
        (
            "Que custos de utilização devo comparar além do preço inicial?",
            "Confirme o tipo e a frequência de substituição de ponteiras e outros "
            "consumíveis, as instruções de higienização e a disponibilidade de "
            "componentes compatíveis com o modelo concreto.",
        ),
        (
            "Como verificar se a oferta Aqua Facial serve para comprar em Portugal?",
            "Antes de pagar, confirme a entrega para a morada em Portugal, "
            "a alimentação elétrica indicada na ficha técnica, a documentação "
            "fornecida e as condições de assistência, devolução e garantia.",
        ),
    ),
    "pressoterapia-vacuum-drenagem": (
        (
            "Pressoterapia e radiofrequência Tecar são o mesmo equipamento?",
            "Não são a mesma tecnologia. A categoria reúne anúncios com "
            "características diferentes: consulte a ficha de cada oferta para "
            "identificar a função real, em vez de assumir que são equivalentes.",
        ),
        (
            "Como comparar acessórios de pressoterapia?",
            "Verifique as peças incluídas, os tamanhos disponíveis, as ligações "
            "e a compatibilidade com o equipamento anunciado. Considere também "
            "as instruções de limpeza e a reposição das peças.",
        ),
        (
            "Que condições confirmar para utilizar o equipamento em Portugal?",
            "Peça ao vendedor as especificações e documentação aplicáveis ao "
            "modelo, informação de assistência e as condições finais de envio "
            "e garantia. A presença na montra não constitui certificação técnica.",
        ),
    ),
    "hifu": (
        (
            "Uma máquina HIFU é o mesmo que um equipamento EMS?",
            "Não. HIFU utiliza ultrassons focalizados, enquanto EMS se refere "
            "à estimulação muscular elétrica. A categoria pode conter anúncios "
            "de tecnologias diferentes; confirme as funções documentadas "
            "do equipamento concreto.",
        ),
        (
            "Que acessórios devo comparar num equipamento HIFU ou EMS?",
            "Num equipamento HIFU, confirme os cartuchos e as referências "
            "compatíveis. Num EMS, verifique os aplicadores e componentes "
            "fornecidos, a reposição, a manutenção e o custo total informado.",
        ),
        (
            "Que condições devo confirmar antes de comprar HIFU ou EMS em Portugal?",
            "Verifique os requisitos de utilização profissional e de segurança, "
            "a documentação técnica, a compatibilidade elétrica, a assistência "
            "e a garantia, bem como o preço final para a morada de entrega.",
        ),
    ),
    "diodo-laser-remocao-tatuagens-pigmentacao": (
        (
            "Um laser de díodo anunciado para depilação também remove tatuagens?",
            "Não se pode concluir isso pelo título do anúncio. Remoção de pelos "
            "e remoção de pigmentos são aplicações distintas; confirme a finalidade "
            "declarada pelo fabricante para o modelo concreto.",
        ),
        (
            "Que informação técnica é importante comparar antes da compra?",
            "Verifique a finalidade prevista, as especificações do equipamento, "
            "os acessórios fornecidos e as instruções de segurança, formação "
            "e manutenção disponibilizadas pelo fabricante.",
        ),
        (
            "Que condições devo validar para encomendar em Portugal?",
            "Confirme requisitos aplicáveis ao equipamento e à sua utilização, "
            "documentação, compatibilidade elétrica, assistência e custos de "
            "entrega e devolução. Um anúncio de afiliado não substitui essa verificação.",
        ),
    ),
}


ES_CATEGORY_GUIDES = {
    "cavitacao-rf-vacuum-corpo": {
        "title": "Máquinas de Cavitación y Radiofrecuencia | Lowcost Europa",
        "description": (
            "Compara máquinas de cavitación, radiofrecuencia y vacío: funciones "
            "incluidas, accesorios y condiciones del vendedor antes de comprar."
        ),
        "heading": "Cómo comparar máquinas de cavitación y radiofrecuencia",
        "intro": (
            "La cavitación, la radiofrecuencia y el vacío pueden aparecer en un "
            "mismo anuncio, pero eso no confirma que todas las funciones estén "
            "incluidas en cada equipo. Consulta la configuración de la oferta "
            "concreta."
        ),
        "checks": (
            (
                "Funciones: identifica en la ficha del modelo las tecnologías "
                "incluidas y si pueden utilizarse de forma independiente."
            ),
            (
                "Aplicadores: confirma los cabezales, accesorios y consumibles "
                "suministrados, así como la disponibilidad de recambios."
            ),
            (
                "Servicio posventa: revisa la documentación, la asistencia y las "
                "condiciones de devolución directamente con el vendedor."
            ),
        ),
    },
    "hydrodermoabrasao-aqua-facial-multifuncoes": {
        "title": "Hidrodermoabrasión y Aqua Facial | Lowcost Europa",
        "description": (
            "Explora equipos Aqua Facial e hidrodermoabrasión. Compara cabezales, "
            "consumibles, limpieza y asistencia antes de consultar la oferta del "
            "socio."
        ),
        "heading": "Qué comprobar en un equipo Aqua Facial",
        "intro": (
            "Los anuncios de hidrodermoabrasión, Aqua Facial y equipos multifunción "
            "pueden incluir accesorios distintos. La denominación comercial, por sí "
            "sola, no confirma el contenido del paquete."
        ),
        "checks": (
            (
                "Cabezales y consumibles: comprueba cuáles se incluyen con el "
                "equipo y cuáles requieren compra por separado o reposición "
                "frecuente."
            ),
            (
                "Limpieza: consulta en el manual las instrucciones de limpieza, "
                "mantenimiento y sustitución de componentes del modelo concreto."
            ),
            (
                "Compatibilidad: compara las referencias de los accesorios, las "
                "condiciones de asistencia y los costes totales indicados por el "
                "vendedor."
            ),
        ),
    },
    "pressoterapia-vacuum-drenagem": {
        "title": "Equipos de Presoterapia y RF Tecar | Lowcost Europa",
        "description": (
            "Compara equipos de presoterapia y radiofrecuencia Tecar. Identifica la "
            "tecnología de cada oferta, sus accesorios y la asistencia del "
            "vendedor."
        ),
        "heading": "Presoterapia y RF Tecar: diferencias que debes confirmar",
        "intro": (
            "La presoterapia y la radiofrecuencia Tecar son tecnologías distintas. "
            "Esta familia del catálogo puede mostrar opciones diferentes; confirma "
            "la función de cada equipo antes de comparar precios."
        ),
        "checks": (
            (
                "Tipo de equipo: identifica si la oferta corresponde a "
                "presoterapia, radiofrecuencia Tecar u otra configuración "
                "documentada."
            ),
            (
                "Componentes: confirma los accesorios y aplicadores incluidos, los "
                "tamaños, la compatibilidad y los recambios."
            ),
            (
                "Uso profesional: revisa la documentación del fabricante, los "
                "requisitos de funcionamiento y el soporte ofrecido por el "
                "vendedor."
            ),
        ),
    },
    "hifu": {
        "title": "HIFU Profesional: Máquinas y Guía | Lowcost Europa",
        "description": (
            "Compara equipos HIFU profesionales: cartuchos, documentación, "
            "asistencia y precios observados. Confirma los detalles de cada modelo "
            "con el socio."
        ),
        "heading": "Cómo evaluar una máquina HIFU profesional",
        "intro": (
            "Las máquinas anunciadas como HIFU pueden tener configuraciones y "
            "accesorios distintos. Compara el modelo exacto y su documentación, sin "
            "dar por hecho que los cartuchos de otros fabricantes sean compatibles."
        ),
        "checks": (
            (
                "Cartuchos y aplicadores: confirma los componentes incluidos, las "
                "referencias compatibles y el coste de reposición."
            ),
            (
                "Documentación técnica: revisa los manuales, los requisitos de "
                "formación y las condiciones de mantenimiento antes de elegir."
            ),
            (
                "Condiciones reales: consulta directamente con el socio el precio "
                "final, la garantía, la disponibilidad y la entrega para España."
            ),
        ),
    },
    "diodo-laser-remocao-tatuagens-pigmentacao": {
        "title": "Láser de Diodo y Eliminación de Pigmentos | Lowcost Europa",
        "description": (
            "Explora equipos láser de diodo y eliminación de pigmentos. Distingue "
            "sus finalidades y confirma especificaciones, formación y condiciones "
            "del proveedor."
        ),
        "heading": "El láser de diodo y la eliminación de pigmentos no son equivalentes",
        "intro": (
            "Los equipos destinados a la depilación con láser de diodo y los "
            "utilizados para eliminar pigmentos o tatuajes tienen finalidades "
            "distintas. El nombre de esta categoría no garantiza que un aparato "
            "realice ambas funciones."
        ),
        "checks": (
            (
                "Finalidad: confirma en la ficha técnica del equipo la aplicación "
                "indicada por el fabricante para el modelo anunciado."
            ),
            (
                "Requisitos de seguridad: revisa la documentación aplicable, los "
                "requisitos profesionales y la formación necesaria para utilizarlo."
            ),
            (
                "Asistencia y compra: compara componentes, consumibles, soporte "
                "técnico y condiciones contractuales del vendedor."
            ),
        ),
    },
}


def guide_for_category(slug, language):
    """Return reviewed category copy only for the two supported SEO markets."""
    language = str(language).lower().replace("_", "-")
    if language in {"pt", "pt-pt"}:
        return PT_CATEGORY_GUIDES.get(slug)
    if language in {"es", "es-es"}:
        return ES_CATEGORY_GUIDES.get(slug)
    return None


def buying_questions_for_category(slug, language):
    """Show useful purchasing guidance only in PT; Spanish pages stay as-is."""
    language = str(language).lower().replace("_", "-")
    if language in {"pt", "pt-pt"}:
        return PT_BUYING_QUESTIONS.get(slug, ())
    return ()
