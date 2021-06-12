from django import template

register = template.Library()


@register.filter
def get_dict(value, namespace):
    return value.get(namespace, None)


@register.filter
def get_list(_list, index):
    try:
        return _list[index]
    except IndexError:
        return None


@register.filter
def get_attr(value, attr):
    return getattr(value, attr)
