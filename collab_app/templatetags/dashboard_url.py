from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def dashboard_url():
    dashboard_url = 'https://app.collabsauce.com'
    if settings.ENVIRONMENT == 'staging':
        dashboard_url = 'https://app.staging.collabsauce.com'

    return dashboard_url
