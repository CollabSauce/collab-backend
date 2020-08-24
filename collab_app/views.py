from allauth.account.models import EmailAddress
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from collab_app.mixins.api import (
    ReadOnlyMixin,
    NoDeleteMixin,
    SaveMixin,
    AddCreatorMixin,
)
from collab_app.models import (
    Comment,
    Organization,
    Profile,
    Thread,
    User,
)
from collab_app.permissions import (
    GateKeeper,
)
from collab_app.serializers import (
    CommentSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    ThreadSerializer,
    UserSerializer,
)


class ApiViewSet(GateKeeper, AddCreatorMixin, SaveMixin, DynamicModelViewSet):
    pass


class CommentViewSet(NoDeleteMixin, ApiViewSet):
    model = Comment
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated, )


class OrganizationViewSet(NoDeleteMixin, ApiViewSet):
    model = Organization
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, )


class ProfileViewSet(ReadOnlyMixin, ApiViewSet):
    model = Profile
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, )


class ThreadViewSet(NoDeleteMixin, ApiViewSet):
    model = Thread
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer
    permission_classes = (IsAuthenticated, )


class UserViewSet(ReadOnlyMixin, ApiViewSet):
    """
    Users endpoint.

    Custom Behavior:
    * `GET /users/me`
        For the detail endpoint, passing `me` or `current` as the ID
        will return information about the current user.
    """
    model = User
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, )

    def retrieve(self, request, *args, **kwargs):
        # users/me behavior
        pk = self.kwargs.get('pk', None)
        if pk and (pk == 'current' or pk == 'me'):
            self.kwargs['pk'] = request.user.id

        return super(UserViewSet, self).retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def resend_verification_email(self, request, *args, **kwargs):
        if str(request.user.id) != kwargs['pk']:
            return Response({'detail': 'Not Found'}, status=404)

        email_address = EmailAddress.objects.get(email=request.user.email)
        email_address.send_confirmation(request=request)
        return Response({}, status=201)
