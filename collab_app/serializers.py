from allauth.account.models import EmailAddress
from dynamic_rest.serializers import (
    DynamicModelSerializer,
)
from dynamic_rest.fields import (
    DynamicMethodField,
    DynamicRelationField
)

from collab_app.models import (
    Comment,
    Membership,
    Organization,
    Profile,
    Thread,
    User,
)
from collab_app.permissions import (
    SideGateKeeper,
)


class ApiSerializer(SideGateKeeper, DynamicModelSerializer):
    pass


class CommentSerializer(ApiSerializer):

    class Meta:
        model = Comment
        name = 'comment'
        fields = (
            'id',
            'bodytext',
            'creator',
            'thread',
        )
        deferred_fields = (
            'creator',
            'thread',
        )

    creator = DynamicRelationField('UserSerializer')
    thread = DynamicRelationField('ThreadSerializer')


class MembershipSerializer(ApiSerializer):

    class Meta:
        model = Membership
        name = 'membership'
        fields = (
            'id',
            'organization',
            'user',
            'is_admin',
        )
        deferred_fields = (
            'user',
            'organization'
        )

    user = DynamicRelationField('UserSerializer')
    organization = DynamicRelationField('OrganizationSerializer')


class OrganizationSerializer(ApiSerializer):

    class Meta:
        model = Organization
        name = 'organization'
        fields = (
            'id',
            'name',
            'threads',
            'memberships',
        )
        deferred_fields = (
            'threads',
            'memberships',
        )

    memberships = DynamicRelationField('UserSerializer', many=True)
    threads = DynamicRelationField('ThreadSerializer', many=True)


class ProfileSerializer(ApiSerializer):

    class Meta:
        model = Profile
        name = 'profile'
        fields = (
            'id',
            'user'
        )
        deferred_fields = (
            'user',
        )

    user = DynamicRelationField('UserSerializer')


class ThreadSerializer(ApiSerializer):

    class Meta:
        model = Thread
        name = 'thread'
        fields = (
            'id',
            'comments',
            'is_resolved',
            'organization',
            'target_id',
            'target_dom_path',
        )
        deferred_fields = (
            'comments',
            'organization'
        )

    organization = DynamicRelationField('OrganizationSerializer')
    comments = DynamicRelationField('CommentSerializer', many=True)


class UserSerializer(ApiSerializer):

    class Meta:
        model = User
        name = 'user'
        fields = (
            'email_verified',
            'email',
            'id',
            'is_active',
            'is_staff',
            'is_superuser',
            'first_name',
            'last_name',
            'memberships',
            'profile',
            'comments',
        )
        deferred_fields = (
            'email_verified',
            'memberships',
            'profile',
            'comments',
        )

    email_verified = DynamicMethodField()
    memberships = DynamicRelationField('MembershipSerializer', many=True)
    profile = DynamicRelationField('ProfileSerializer')
    comments = DynamicRelationField('CommentSerializer', many=True)

    def get_email_verified(self, user):
        return EmailAddress.objects.filter(user=user, verified=True).exists()
