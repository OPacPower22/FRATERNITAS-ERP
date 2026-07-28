from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def moneda(valor):

    if valor is None:
        valor = Decimal("0.00")

    return "${:,.2f}".format(valor)