from django.template import Library

register = Library()


@register.simple_tag
def colname(list_display: list[str], index: int) -> str:
    """
    Return the name of the column identified by its index in the list_display
    list declared on the list view.
    """
    return list_display[index]


@register.simple_tag
def colclasses(classes: dict[str, str], list_display: list[str], index: int) -> str:
    """
    Return additional CSS classes for a result table column.

    The column is identified by its index in the list_display list declared on
    the list view.
    """
    col = colname(list_display, index)
    try:
        css = classes[col]
    except KeyError:
        return ""  # fail silently
    if css:
        # Add a space so the classes can be inserted into the class attribute
        # after other classes.
        return f" {css}"
    return css
