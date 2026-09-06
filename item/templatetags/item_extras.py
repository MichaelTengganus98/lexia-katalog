import re

from django import template

register = template.Library()

_LINE = re.compile(r"\s*(.+?)\s*:\s*(.+?)\s*$")


@register.filter
def specs(text, limit=0):
    """Parse an Item.specification blob ("Label : value" per line) into a list
    of (label, value) tuples. `limit` (>0) caps how many are returned."""
    pairs = []
    for line in (text or "").splitlines():
        m = _LINE.match(line)
        if m:
            pairs.append((m.group(1), m.group(2)))
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 0
    return pairs[:limit] if limit > 0 else pairs


@register.filter
def pictures(item):
    """Non-empty picture1..picture10 image fields of an Item, in order."""
    out = []
    for n in range(1, 11):
        f = getattr(item, "picture%d" % n, None)
        if f:
            out.append(f)
    return out
