from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_attr(obj, attr):
    # Позволяет достать вложенный атрибут, например 'outfit.id'
    try:
        for bit in attr.split('.'):
            obj = getattr(obj, bit)
        return obj
    except:
        return None