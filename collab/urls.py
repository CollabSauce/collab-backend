"""collab URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from inspect import isclass

import debug_toolbar
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from dynamic_rest.routers import DynamicRouter

from collab_app import views


# auto-register views
drest_router = DynamicRouter()

for name in dir(views):
    view = getattr(views, name)
    if isclass(view) and getattr(view, 'serializer_class', None):
        drest_router.register_resource(view, namespace='api')

rest_framework_auth_urls = include('rest_framework.urls', namespace='rest_framework')
urlpatterns = [
    path('', include(drest_router.urls)),
    path('admin/', admin.site.urls),  # admin site
    path('api-auth/', rest_framework_auth_urls),  # direct login through browseable api
]

# rest-auth urls
urlpatterns += [
    path('rest-auth/', include('dj_rest_auth.urls')),  # django-rest-auth library
    path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),  # registration
    # required so password reset works with djang-rest-auth TODO: DO I NEED THIS?
    path('', include('django.contrib.auth.urls')),
    # so allauth uses `verify-email` url in it's signup email.
    # (see allauth/account/adapter.py `get_email_confirmation_url` method)
    path('verify-email/<key>', TemplateView.as_view(), name='account_confirm_email')
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
