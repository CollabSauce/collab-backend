from datetime import datetime

from allauth.account.models import EmailAddress
import boto3
from django.conf import settings
from django.utils.crypto import get_random_string
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework import exceptions
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from collab_app.mixins.api import (
    ReadOnlyMixin,
    NoCreateMixin,
    NoUpdateMixin,
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
        if not organization.memberships.filter(user=inviter, role=Membership.RoleType.ADMIN).exists():
            raise exceptions.ValidationError('You must be an admin of this organization to send invites.')
        if Invite.objects.filter(email=email, organization=organization, state=Invite.InviteState.CREATED).exists():
            # 1) We have db validation on this, but do manual validation for better exception message to user
            # 2) TODO: Update when multiple orgs??
            raise exceptions.ValidationError('This email has already been invited to Collabsauce.')

        invite = Invite.objects.create(
            email=email,
            organization=organization,
            inviter=inviter,
            state=state,
            key=get_random_string(length=32)
        )
        return Response({
            'invite': InviteSerializer(
                invite,
                include_fields=InviteSerializer.Meta.deferred_fields).data
            },
            status=201
        )

    @action(detail=False, methods=['post'])
    def accept_invite(self, request, *args, **kwargs):

        invite = Invite.objects.get(email=request.user.email)
        key = request.data.get('key')

        if not request.user.is_authenticated:
            raise exceptions.ValidationError('You must be logged in to accept an invite.')
        if invite.state != Invite.InviteState.CREATED:
            raise exceptions.ValidationError('Can no longer accept this invitation.')
        if invite.email != request.user.email:
            raise exceptions.ValidationError('This invite does not belong to you.')
        if invite.key != key:
            raise exceptions.ValidationError('This invite is not longer valid. Ask your admin to resend an invite.')

        invite.state = Invite.InviteState.ACCEPTED
        invite.save()

        Membership.objects.create(organization=invite.organization, user=request.user)

        return Response({
            'invite': InviteSerializer(
                invite,
                include_fields=InviteSerializer.Meta.deferred_fields).data
            },
            status=200
        )

    # @action(detail=False, methods=['post'])
    # def deny_invite(self, request, *args, **kwargs):
    #     invite_id = request.data.get('invite')
    #     invite = Invite.objects.get(id=invite_id)

    #     if invite.state != Invite.InviteState.CREATED:
    #         raise exceptions.ValidationError('Can no longer deny this invitation.')
    #     if invite.email != request.user.email:
    #         raise exceptions.ValidationError('This invite does not belong to you.')

    #     invite.state = Invite.InviteState.DENIED
    #     invite.save()

    #     return Response({
    #         'invite': InviteSerializer(
    #             invite,
    #             include_fields=InviteSerializer.Meta.deferred_fields).data
    #         },
    #         status=200
    #     )

    @action(detail=False, methods=['post'])
    def cancel_invite(self, request, *args, **kwargs):
        invite_id = request.data.get('invite')
        invite = Invite.objects.get(id=invite_id)

        if invite.state != Invite.InviteState.CREATED:
            raise exceptions.ValidationError('Can no longer cancel this invitation.')
        if not invite.organization.memberships.filter(user=request.user, role=Membership.RoleType.ADMIN).exists():
            raise exceptions.ValidationError('You must be an admin of this organization to cancel invites.')

        invite.state = Invite.InviteState.CANCELED
        invite.save()

        return Response({
            'invite': InviteSerializer(
                invite,
                include_fields=InviteSerializer.Meta.deferred_fields).data
            },
            status=200
        )


class MembershipViewSet(NoCreateMixin, NoUpdateMixin, ApiViewSet):
    model = Membership
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = (IsAuthenticated, )

    def destroy(self, request, *args, **kwargs):
        membership_to_delete = self.get_object()
        membership_of_current_user = membership_to_delete.organization.memberships.get(user=request.user)

        if membership_to_delete == membership_of_current_user:
            raise exceptions.ValidationError('Cannot remove yourself from an organization')
        if membership_of_current_user.role != Membership.RoleType.ADMIN:
            raise exceptions.ValidationError('You must be an admin of the org to remove members')

        return super(MembershipViewSet, self).destroy(request, *args, **kwargs)


class OrganizationViewSet(NoUpdateMixin, NoDeleteMixin, ApiViewSet):
    model = Organization
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        # For now, only allow a user to belong to one organization (even though
        # we have DB modeling as being able to belong to many orgs).
        # Verify that the user is not a member in any other organization yet.
        if Membership.objects.filter(user=request.user).exists():
            raise exceptions.ValidationError(
                'You already belong to an organization.'
            )
        response = super(OrganizationViewSet, self).create(request, *args, **kwargs)
        # create a membership for the user after create of org.
        Membership.objects.create(
            organization_id=response.data['organization']['id'],
            user=request.user,
            role=Membership.RoleType.ADMIN
        )
        return response


class ProfileViewSet(ReadOnlyMixin, ApiViewSet):
    model = Profile
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticated, )


class ProjectViewSet(NoUpdateMixin, NoDeleteMixin, ApiViewSet):
    model = Project
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):
        # For now, user can only belong to one organization (hence one membership). Get that organization.
        membership = Membership.objects.filter(user=request.user).select_related('organization').first()
        if membership.role != Membership.RoleType.ADMIN:
            raise exceptions.ValidationError(
                'You must be an admin to create a project.'
            )

        request.data['key'] = get_random_string(length=32)
        request.data['organization'] = membership.organization.id
        return super(ProjectViewSet, self).create(request, *args, **kwargs)


class TaskViewSet(ReadOnlyMixin, ApiViewSet):
    model = Task
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['get'])
    def signature(self, request, *args, **kwargs):
        s3_bucket = getattr(settings, 'S3_BUCKET')
        organization = request.query_params.get('organization', None)
        file_type = 'png'  # TODO: other img file-types?

        if not organization:
            raise exceptions.ValidationError(
                'Must provide organization query-param'
            )

        file_name = f'{organization}__{datetime.now().isoformat()}.{file_type}'
        s3 = boto3.client('s3')

        presigned_post = s3.generate_presigned_post(
            s3_bucket,
            file_name,
            Fields={'acl': 'public-read', 'Content-Type': file_type},
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
