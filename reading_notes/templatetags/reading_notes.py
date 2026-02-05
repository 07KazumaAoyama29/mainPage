from django import template

register = template.Library()


@register.filter
def author_summary(author_str):
    """
    Format comma-separated author list as:
    - single: "A"
    - multiple: "A 他N名"
    """
    if not author_str:
        return ""

    parts = [p.strip() for p in author_str.split(",") if p.strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} 他{len(parts) - 1}名"
