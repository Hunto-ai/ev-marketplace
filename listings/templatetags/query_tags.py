from django import template

register = template.Library()

@register.simple_tag
def remove_filter_from_query(request, key, value):
    updated_query = request.GET.copy()
    if key in updated_query:
        values = updated_query.getlist(key)
        if value in values:
            values.remove(value)
            updated_query.setlist(key, values)
    return updated_query.urlencode()