"""
core/templatetags/core_extras.py
Custom template filters for the LBYCPG3 system.
"""

from django import template

register = template.Library()


@register.filter(name="dict_key")
def dict_key(d, key):
    """
    Access a dictionary value by key inside a Django template.
    Usage:  {{ my_dict|dict_key:"some_key" }}
    """
    if isinstance(d, dict):
        return d.get(key, [])
    return []
