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
)


@register.simple_tag
def storefront_js_labels():
    lang = get_language()
    return {text: translate_ui(text, lang) for text in JS_TEXTS}
