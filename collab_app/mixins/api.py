from django.db.transaction import atomic
from rest_framework import exceptions

from collab_app.utils import catch_failures


class ReadOnlyMixin(object):

    """Makes a ViewSet read-only."""

    allowed_methods = ('GET', 'OPTIONS')

    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('POST')

    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('PUT')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('PATCH')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('DELETE')


class NoCreateMixin(object):

    """Prevents CREATE."""

    allowed_methods = ('GET', 'PUT', 'PATCH', 'OPTIONS')

    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('POST')


class NoUpdateMixin(object):

    """Prevents UPDATE."""

    allowed_methods = ('GET', 'POST', 'OPTIONS')

    def update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('PUT')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('PATCH')


class NoDeleteMixin(object):

    """Prevents DELETE."""

    allowed_methods = ('GET', 'POST', 'PUT', 'PATCH', 'OPTIONS')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed('DELETE')


class SaveMixin(object):

    """Allow a ViewSet to handle pre/post update/create/destroy."""

    def pre_create(self, serializer):
        pass

    def post_create(self, serializer):
        pass

    def pre_update(self, serializer):
        pass

    def post_update(self, serializer):
        pass

    def pre_destroy(self, serializer):
        pass

    def post_destroy(self, serializer):
        pass

    @catch_failures
    @atomic
    def perform_create(self, serializer):
        self.pre_create(serializer)
        result = super(SaveMixin, self).perform_create(serializer)
        self.post_create(serializer)
        return result

    @catch_failures
    @atomic
    def perform_update(self, serializer):
        self.pre_update(serializer)
        result = super(SaveMixin, self).perform_update(serializer)
        self.post_update(serializer)
        return result

    @catch_failures
    @atomic
    def perform_destroy(self, serializer):
        self.pre_destroy(serializer)
        result = super(SaveMixin, self).perform_destroy(serializer)
        self.post_destroy(serializer)
        return result


class AddCreatorMixin(object):

    """Automatically set the request.user in the creator field.
    Attributes:
        CREATOR_FIELD: Can be set to over-ride the name of the field or
            opt-out of this feature.
    """
    CREATOR_FIELD = 'creator'

    def _add_creator_to_record(self, request, field, data):
        creator = data.get(field)
        if not creator:
            data[field] = request.user.pk

    def create(self, request, *args, **kwargs):
        field = self.CREATOR_FIELD
        if field:
            data = request.data
            singular_name = self.serializer_class().get_name()
            plural_name = self.serializer_class().get_plural_name()
            if isinstance(data, list):
                for d in data:
                    self._add_creator_to_record(request, field, d)
            elif plural_name in data and len(data) == 1:
                data = data[plural_name]
                for d in data:
                    self._add_creator_to_record(request, field, d)
            else:
                if singular_name in data and len(data.keys()) == 1:
                    data = data[singular_name]
                self._add_creator_to_record(request, field, data)
        return super(AddCreatorMixin, self).create(request, *args, **kwargs)
