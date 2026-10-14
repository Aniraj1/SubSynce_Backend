from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()

NAV_ACTIVE = "bg-primary/10 text-primary"
NAV_IDLE = "text-ink-light hover:bg-surface-container hover:text-ink"


@register.simple_tag(takes_context=True)
def nav_class(context, *url_names):
    """Sidebar link classes: highlighted when the page's `active` value (if passed) or the current URL name matches."""
    match = getattr(context.get("request"), "resolver_match", None)
    current = context.get("active") or (match.url_name if match else "")
    return NAV_ACTIVE if current in url_names else NAV_IDLE


@register.filter
def money(value):
    """Format a number as AUD, e.g. 1280 -> $1,280.00 and -5 -> -$5.00."""
    if value in (None, ""):
        return "—"
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"


@register.filter
def percent(value):
    if value is None:
        return "—"
    return f"{value:.0%}"


@register.filter
def label(value):
    """IN_PROGRESS -> In Progress"""
    return str(value or "").replace("_", " ").title()
