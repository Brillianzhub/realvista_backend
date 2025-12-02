from django import template

register = template.Library()


@register.filter(name='format_currency')
def format_currency(value, currency_symbol='$'):
    try:
        value = float(value)
        return f"{currency_symbol}{value:,.2f}"
    except (ValueError, TypeError):
        return value
