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
            'tasks',
            'task_columns',
        )
        deferred_fields = (
            'organization',
            'tasks',
            'task_columns',
        )

    tasks = DynamicRelationField('TaskSerializer', many=True)
    task_columns = DynamicRelationField('TaskColumnSerializer', many=True)
    organization = DynamicRelationField('OrganizationSerializer')


class TaskSerializer(ApiSerializer):

    class Meta:
        model = Task
        name = 'task'
        fields = (
            'id',
            'assigned_to',
            'assigned_to_full_name',
            'description',
            'design_edits',
            'window_screenshot_url',
            'element_screenshot_url',
            'task_number',
            'is_resolved',
            'has_text_copy_changes',
            'target_id',
            'target_dom_path',
            'has_target',
            'text_copy_changes',
            'creator',
            'creator_full_name',
            'project',
            'order',
            'task_column',
            'task_comments',
            'task_metadata',
            'title',
        )
        deferred_fields = (
            'assigned_to',
            'assigned_to_full_name',
            'creator',
            'creator_full_name',
            'project',
            'task_column',
            'task_comments',
            'task_metadata',
        )

    assigned_to = DynamicRelationField('UserSerializer')
    assigned_to_full_name = DynamicMethodField(requires=['assigned_to.'])
    creator = DynamicRelationField('UserSerializer')
    creator_full_name = DynamicMethodField(requires=['creator.'])
    project = DynamicRelationField('ProjectSerializer')
    task_column = DynamicRelationField('TaskColumnSerializer')
    task_comments = DynamicRelationField('TaskCommentSerializer', many=True)
    task_metadata = DynamicRelationField('TaskMetadataSerializer')

    def get_assigned_to_full_name(self, task):
        assigned_to = task.assigned_to
        if assigned_to:
            return f'{task.assigned_to.first_name} {task.assigned_to.last_name}'
        return ''

    def get_creator_full_name(self, task):
        if task.creator:
            return f'{task.creator.first_name} {task.creator.last_name}'
        else:
            return task.one_off_email_set_by


class TaskCommentSerializer(ApiSerializer):
    class Meta:
        model = TaskComment
        name = 'task_comment'
        fields = (
            'id',
            'creator',
            'creator_full_name',
            'task',
            'text',
        )
        deferred_fields = (
            'creator',
            'task',
        )

    creator = DynamicRelationField('UserSerializer')
    creator_full_name = DynamicMethodField(requires=['creator.'])
    task = DynamicRelationField('TaskSerializer')

    def get_creator_full_name(self, task_comment):
        return f'{task_comment.creator.first_name} {task_comment.creator.last_name}'


class TaskColumnSerializer(ApiSerializer):
    class Meta:
        model = TaskColumn
        name = 'task_column'
        fields = (
            'id',
            'name',
            'order',
            'project',
            'tasks',
        )
        deferred_fields = (
            'project',
            'tasks',
        )

    project = DynamicRelationField('ProjectSerializer')
    tasks = DynamicRelationField('TaskSerializer', many=True)


class TaskMetadataSerializer(ApiSerializer):
    class Meta:
        model = TaskMetadata
        name = 'task_metadata'
        fields = (
            'id',
            'url_origin',
            'os_name',
            'os_version',
            'os_version_name',
            'browser_name',
            'browser_version',
            'selector',
            'screen_height',
            'screen_width',
            'device_pixel_ratio',
            'browser_window_width',
            'browser_window_height',
            'color_depth',
            'pixel_depth',
            'created',
            'task',
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
