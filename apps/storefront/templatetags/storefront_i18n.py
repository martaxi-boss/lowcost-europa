"""Presentation-only translation helpers; never mutate catalogue data."""

from django import template
from django.utils.translation import get_language

from apps.storefront.ui_translations import translate_ui
from apps.storefront.seo_locales import family_page_url, home_page_url

register = template.Library()


@register.simple_tag(takes_context=True)
def family_seo_url(context, family):
    request = context["request"]
    return family_page_url(request, family.slug)


@register.simple_tag(takes_context=True)
def storefront_home_url(context):
    return home_page_url(context["request"])


@register.filter
def ui_t(value):
    return translate_ui(value, get_language())


# Preserve the source category name as the authority. Only exact known
# names have curated translations; unknown or renamed families stay unchanged.
@register.filter
def family_label(family):
    return translate_ui(family.name, get_language())


# Read by the existing same-origin comparison JS. No tracker or paid translation API.
JS_TEXTS = (
    "Preço observado",
    "Não disponível",
    "Logística observada",
    "Prazo não confirmado",
    "Ver no AliExpress",
    "Retirar",
    "Comparar equipamento",
    "Na comparação",
    "Equipamento",
    "de 3 equipamentos selecionados",
    "ofertas nesta lista",
    "de",
    "Limite de três equipamentos. Retire um para acrescentar outro.",
    "O limite aplica-se só a preços em EUR; valores de outras moedas não são convertidos.",
    ("Preços de moedas diferentes não são comparados nem convertidos. "
     "Ofertas sem preço ficam no fim."),
    "+ Comparar equipamento",
)


@register.simple_tag
def storefront_js_labels():
    lang = get_language()
    return {text: translate_ui(text, lang) for text in JS_TEXTS}

@register.filter
def ui_og_locale(language):
    """Open Graph expects region-qualified locale identifiers."""
    return {
        "pt-pt": "pt_PT",
        "es": "es_ES",
        "en": "en_GB",
        "fr": "fr_FR",
        "de": "de_DE",
    }.get(str(language).lower(), "pt_PT")
