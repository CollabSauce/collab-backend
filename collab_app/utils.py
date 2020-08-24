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
            raise exceptions.ValidationError(e.message)
        except DataError as e:
            raise exceptions.ValidationError(e.message)

    return wrapper


# UNUSED?
def generate_email(subject, html_body, from_email, to_email, text_body='', cc=[], bcc=[], headers=None):
    # attempt converting HTML (template) into text for fallback
    if html_body and not text_body:
        text_body = strip_tags(html_body)

    email = EmailMultiAlternatives(
        subject=subject, body=text_body, from_email=from_email,
        to=to_email, cc=cc, bcc=bcc, headers=headers
    )

    if html_body:
        email.attach_alternative(html_body, 'text/html')

    return email


# UNUSED?
def send_email(
    subject, html_body, from_email, to_email, text_body='', cc=[], bcc=[], headers=None, fail_silently=False
):
    to_email = list(to_email)
    email = generate_email(subject, html_body, from_email, to_email, text_body, cc, bcc, headers)
    email.send(fail_silently=fail_silently)
