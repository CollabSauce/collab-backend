import datetime

from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone


def not_equal(a, b):
    if not isinstance(a, type(b)):
        return str(a) != str(b)
    if isinstance(a, datetime.datetime):
        if not timezone.is_aware(a):
            a = timezone.make_aware(a, timezone.utc)
        if not timezone.is_aware(b):
            b = timezone.make_aware(b, timezone.utc)
    return a != b


class ModelDiffMixin(object):

    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if not_equal(v, d2[k])]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        # ignore any deferred fields as reading from them
        # will cause this method to loop
        deferred_fields = self.get_deferred_fields()
        fields = [field.name for field in self._meta.fields if (
            field.name not in deferred_fields and
            field.attname not in deferred_fields)]
        return model_to_dict(self, fields=fields)


class CreatedUpdatedModel(ModelDiffMixin, models.Model):

    '''
    Base Model that includes updated and created fields which are
    automatically saved
    '''
    class Meta:
        abstract = True

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s' % self.id


class BaseModel(ModelDiffMixin, models.Model):

    '''
    Base Model that includes creator, updated and created fields which are
    automatically saved
    '''
    class Meta:
        abstract = True

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_related',
    )
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
