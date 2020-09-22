from django.core.mail.message import EmailMultiAlternatives
from django.db import IntegrityError
from django.db.utils import DataError
from django.shortcuts import _get_queryset
from django.utils.html import strip_tags

from rest_framework import exceptions


# Note: copied from django-annoying repo
def get_object_or_none(klass, *args, **kwargs):
    """
    Uses get() to return an object or None if the object does not exist.
    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.
    Note: Like with get(), a MultipleObjectsReturned will be raised if more than one
    object is found.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def catch_failures(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            raise exceptions.ValidationError(e)
        except DataError as e:
            raise exceptions.ValidationError(e.message)

    return wrapper
