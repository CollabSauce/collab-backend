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


class OrganizationSerializer(ApiSerializer):

    class Meta:
        model = Organization
        name = 'organization'
        fields = (
            'id',
            'name',
            'threads',
            'users',
        )
        deferred_fields = (
            'threads',
            'users',
        )

    users = DynamicRelationField('OrganizationSerializer', many=True)
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
            'organization',
            'profile',
            'comments',
        )
        deferred_fields = (
            'email_verified',
            'organization',
            'profile',
            'comments',
        )

    email_verified = DynamicMethodField()
    organization = DynamicRelationField('OrganizationSerializer')
    profile = DynamicRelationField('ProfileSerializer')
    comments = DynamicRelationField('CommentSerializer', many=True)

    def get_email_verified(self, user):
        return EmailAddress.objects.filter(user=user, verified=True).exists()
