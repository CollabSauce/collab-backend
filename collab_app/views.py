from datetime import datetime

from allauth.account.models import EmailAddress
import boto3
from django.conf import settings
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework import exceptions
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
    Invite,
    Membership,
    Organization,
    Profile,
    Project,
    Task,
    TaskColumn,
    TaskComment,
    TaskMetadata,
    User,
)
from collab_app.permissions import (
    GateKeeper,
)
from collab_app.serializers import (
    InviteSerializer,
    MembershipSerializer,
    OrganizationSerializer,
    ProfileSerializer,
    ProjectSerializer,
    TaskSerializer,
    TaskColumnSerializer,
    TaskCommentSerializer,
    TaskMetadataSerializer,
    UserSerializer,
)


class ApiViewSet(GateKeeper, AddCreatorMixin, SaveMixin, DynamicModelViewSet):
    pass


class InviteViewSet(ReadOnlyMixin, ApiViewSet):
    model = Invite
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['post'])
    def create_invite(self, request, *args, **kwargs):
        org_id = request.data.get('organization')
        email = request.data.get('email')
        organization = Organization.objects.get(id=org_id)
        inviter = request.user
        state = Invite.InviteState.CREATED

        # make sure inviter is an admin of the org
        if not organization.memberships.filter(user=inviter, is_admin=True).exists():
            raise exceptions.ValidationError('You must be an admin of this organization to send invites.')

        invite = Invite.objects.create(
            email=email,
            organization=organization,
            inviter=inviter,
            state=state
        )
        return Response(InviteSerializer(invite).data, status=201)

    @action(detail=False, methods=['post'])
    def accept_invite(self, request, *args, **kwargs):
        invite_id = request.data.get('invite')
        invite = Invite.objects.get(id=invite_id)

        if invite.state != Invite.InviteState.CREATED:
            raise exceptions.ValidationError('Can no longer accept this invitation.')
        if invite.email != request.user.email:
            raise exceptions.ValidationError('This invite does not belong to you.')

        invite.state = Invite.InviteState.ACCEPTED
        invite.save()

        return Response(InviteSerializer(invite).data, status=200)

    @action(detail=False, methods=['post'])
    def deny_invite(self, request, *args, **kwargs):
        invite_id = request.data.get('invite')
        invite = Invite.objects.get(id=invite_id)

        if invite.state != Invite.InviteState.CREATED:
            raise exceptions.ValidationError('Can no longer deny this invitation.')
        if invite.email != request.user.email:
            raise exceptions.ValidationError('This invite does not belong to you.')

        invite.state = Invite.InviteState.DENIED
        invite.save()

        return Response(InviteSerializer(invite).data, status=200)

    @action(detail=False, methods=['post'])
    def cancel_invite(self, request, *args, **kwargs):
        invite_id = request.data.get('invite')
        invite = Invite.objects.get(id=invite_id)

        if invite.state != Invite.InviteState.CREATED:
            raise exceptions.ValidationError('Can no longer cancel this invitation.')
        if not invite.organization.memberships.filter(user=request.user, is_admin=True).exists():
            raise exceptions.ValidationError('You must be an admin of this organization to cancel invites.')

        invite.state = Invite.InviteState.CANCELED
        invite.save()

        return Response(InviteSerializer(invite).data, status=200)


class MembershipViewSet(ReadOnlyMixin, ApiViewSet):
    model = Membership
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = (IsAuthenticated, )


class OrganizationViewSet(ReadOnlyMixin, ApiViewSet):
    model = Organization
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, )


class ProfileViewSet(ReadOnlyMixin, ApiViewSet):
    model = Profile
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, )


class ProjectViewSet(ReadOnlyMixin, ApiViewSet):
    model = Project
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, )


class TaskViewSet(ReadOnlyMixin, ApiViewSet):
    model = Task
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['get'])
    def signature(self, request, *args, **kwargs):
        s3_bucket = getattr(settings, 'S3_BUCKET')
        organization = request.query_params.get('organization', None)

        if not organization:
            raise exceptions.ValidationError(
                'Must provide organization query-param'
            )

        file_name = f'{organization}__{datetime.now().isoformat()}.png'
        s3 = boto3.client('s3')

        presigned_post = s3.generate_presigned_post(
            s3_bucket,
            file_name,
            Fields={'acl': 'public-read', 'Content-Type': 'png'},
            Conditions=[
                {'acl': 'public-read'},
                {'Content-Type': file_type}
            ],
            ExpiresIn=120
        )

        return Response({
          'data': presigned_post,
          'url': f'https://{s3_bucket}.s3.amazonaws.com/{file_name}'
        })


class TaskColumnViewSet(ReadOnlyMixin, ApiViewSet):
    model = TaskColumn
    queryset = TaskColumn.objects.all()
    serializer_class = TaskColumnSerializer
    permission_classes = (IsAuthenticated, )


class TaskCommentViewSet(ReadOnlyMixin, ApiViewSet):
    model = TaskComment
    queryset = TaskComment.objects.all()
    serializer_class = TaskCommentSerializer
    permission_classes = (IsAuthenticated, )


class TaskMetadataViewSet(ReadOnlyMixin, ApiViewSet):
    model = TaskMetadata
    queryset = TaskMetadata.objects.all()
    serializer_class = TaskMetadataSerializer
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
