"""Presentation-only translation helpers; never mutate catalogue data."""

from django import template
from django.utils.translation import get_language

from apps.storefront.ui_translations import translate_ui

register = template.Library()


@register.filter
def ui_t(value):
    return translate_ui(value, get_language())


# Translation is based on the stable catalogue slug, not a guessed seller title.
FAMILY_LABELS = {
    "cavitacao-rf-vacuum-corpo": "Cavitação + RF + Vacuum (corpo)",
    "hydrodermoabrasao-aqua-facial-multifuncoes": (
        "Hydrodermoabrasão / Aqua Facial / Multifunções faciais"
    ),
    "pressoterapia-vacuum-drenagem": "Pressoterapia / Vacuum / Drenagem",
    "hifu": "HIFU profissional",
    "diodo-laser-remocao-tatuagens-pigmentacao": (
        "Diodo Laser / Remoção de Tatuagens / Pigmentação"
    ),
}


@register.filter
def family_label(family):
    name = family.name
    if (get_language() or "pt-pt").lower().startswith("pt"):
        return name
    label = FAMILY_LABELS.get(family.slug)
    return translate_ui(label, get_language()) if label else name


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
