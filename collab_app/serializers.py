from allauth.account.models import EmailAddress
from dynamic_rest.serializers import (
    DynamicModelSerializer,
)
from dynamic_rest.fields import (
    DynamicMethodField,
    DynamicRelationField
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
    SideGateKeeper,
)


class ApiSerializer(SideGateKeeper, DynamicModelSerializer):
    pass


class InviteSerializer(ApiSerializer):

    class Meta:
        model = Invite
        name = 'invite'
        fields = (
            'id',
            'inviter',
            'organization',
            'email',
            'state',
        )
        deferred_fields = (
            'inviter',
            'organization',
        )

    inviter = DynamicRelationField('UserSerializer')
    organization = DynamicRelationField('OrganizationSerializer')


class MembershipSerializer(ApiSerializer):

    class Meta:
        model = Membership
        name = 'membership'
        fields = (
            'id',
            'organization',
            'user',
            'role',
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
            'invites',
            'name',
            'memberships',
            'projects',
        )
        deferred_fields = (
            'invites',
            'memberships',
            'projects',
        )

    invites = DynamicRelationField('InviteSerializer', many=True)
    memberships = DynamicRelationField('MembershipSerializer', many=True)
    projects = DynamicRelationField('ProjectSerializer', many=True)


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


class ProjectSerializer(ApiSerializer):

    class Meta:
        model = Project
        name = 'project'
        fields = (
            'id',
            'name',
            'key',
            'url',
            'organization',
        )
        deferred_fields = (
            'organization',
        )

    organization = DynamicRelationField('OrganizationSerializer')


class TaskSerializer(ApiSerializer):

    class Meta:
        model = Task
        name = 'task'
        fields = (
            'id',
            'description',
            'design_edits',
            'window_screenshot_url',
            'element_screenshot_url',
            'task_number',
            'is_resolved',
            'target_id',
            'target_dom_path',
            'creator',
            'project',
            'task_column',
            'task_comments',
            'task_metadata',
        )
        deferred_fields = (
            'creator',
            'project',
            'task_column',
            'task_comments',
            'task_metadata',
        )

    creator = DynamicRelationField('UserSerializer')
    project = DynamicRelationField('ProjectSerializer')
    task_column = DynamicRelationField('TaskColumnSerializer')
    task_comments = DynamicRelationField('TaskCommentSerializer', many=True)
    task_metadata = DynamicRelationField('TaskMetadataSerializer')


class TaskCommentSerializer(ApiSerializer):
    class Meta:
        model = TaskComment
        name = 'task_comment'
        fields = (
            'id',
            'creator',
            'task',
            'text',
        )
        deferred_fields = (
            'creator',
            'task',
        )

    creator = DynamicRelationField('UserSerializer')
    task = DynamicRelationField('TaskSerializer')


class TaskColumnSerializer(ApiSerializer):
    class Meta:
        model = TaskColumn
        name = 'task_column'
        fields = (
            'id',
            'name',
            'tasks',
        )
        deferred_fields = (
            'tasks',
        )

    tasks = DynamicRelationField('TaskSerializer', many=True)


class TaskMetadataSerializer(ApiSerializer):
    class Meta:
        model = TaskMetadata
        name = 'task_metadata'
        fields = (
            'id',
            'url_origin',
            'operating_system',
            'browser',
            'selector',
            'resolution',
            'browser_window',
            'color_depth',
            'task'
        )
        deferred_fields = (
            'task',
        )

    task = DynamicRelationField('TaskSerializer')


class UserSerializer(ApiSerializer):

    class Meta:
        model = User
        name = 'user'
        fields = (
            'email_verified',
            'email',
            'id',
            'invites_sent',
            'is_active',
            'is_staff',
            'is_superuser',
            'first_name',
            'last_name',
            'memberships',
            'profile',
            'created_tasks',
            'created_task_comments',
        )
        deferred_fields = (
            'email_verified',
            'invites_sent',
            'memberships',
            'profile',
            'created_tasks',
            'created_task_comments',
        )

    email_verified = DynamicMethodField()
    invites_sent = DynamicRelationField('InviteSerializer', many=True)
    memberships = DynamicRelationField('MembershipSerializer', many=True)
    profile = DynamicRelationField('ProfileSerializer')
    created_tasks = DynamicRelationField('TaskSerializer', many=True)
    created_task_comments = DynamicRelationField('TaskCommentSerializer', many=True)

    def get_email_verified(self, user):
        return EmailAddress.objects.filter(user=user, verified=True).exists()
