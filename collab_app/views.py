from allauth.account.models import EmailAddress
from django.db import transaction
from django.utils.crypto import get_random_string
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.decorators import action
from rest_framework import exceptions
from rest_framework.permissions import (
    AllowAny,
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
    TaskHtml,
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
from collab_app.tasks import (
    create_screenshots_for_task,
    notify_participants_of_task_column_change
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

        invite = Invite.objects.filter(email=request.user.email, state=Invite.InviteState.CREATED).first()
        key = request.data.get('key')

        if not request.user.is_authenticated:
            raise exceptions.ValidationError('You must be logged in to accept an invite.')
        if not invite or invite.state != Invite.InviteState.CREATED:
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
        if Project.objects.filter(name=request.data['name'], organization=membership.organization).exists():
            raise exceptions.ValidationError(
                'This project name already exists for your organization.'
            )

        request.data['key'] = get_random_string(length=32)
        request.data['organization'] = membership.organization.id
        return super(ProjectViewSet, self).create(request, *args, **kwargs)


class TaskViewSet(ReadOnlyMixin, ApiViewSet):
    model = Task
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, )
    # permission_classes = []
    # authentication_classes = []

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_task(self, request, *args, **kwargs):
        project_id = request.data['project']
        task_column_id = request.data['task_column']

        # make sure user has access to this project
        if not Project.objects.filter(
            id=project_id,
            organization__memberships__user=request.user
        ).exists():
            raise exceptions.ValidationError(
                'You do not have access to this project.'
            )

        # make sure the task column is part of the project
        if not TaskColumn.objects.filter(project_id=project_id, id=task_column_id):
            raise exceptions.ValidationError(
                'Invalid task column.'
            )

        next_number = Task.objects.filter(project_id=project_id).count() + 1
        last_task_in_column = Task.objects.filter(
            project_id=project_id,
            task_column_id=task_column_id
        ).order_by('-order').first()
        task = Task.objects.create(
            title=request.data['title'],
            target_dom_path=request.data['target_dom_path'],
            order=last_task_in_column.order + 1 if last_task_in_column else 1,
            project_id=project_id,
            task_column_id=task_column_id,
            creator=request.user,
            task_number=next_number
        )

        return Response({
            'task': TaskSerializer(
                task,
                include_fields=TaskSerializer.Meta.deferred_fields).data
            },
            status=201
        )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def reorder_tasks(self, request, *args, **kwargs):
        task_data = request.data
        task_ids = [task['id'] for task in task_data]

        # TODO: check task_column field is valid too

        # get the specified tasks. make sure they belong to the correct specified project
        # and that the user has access to those tasks.
        tasks = Task.objects.filter(
            id__in=task_ids,
            project_id=task_data[0]['project'],
            project__organization__memberships__user=request.user
        )

        if len(tasks) != len(task_ids):
            raise exceptions.ValidationError('Moving card invalid. Please contact support')

        # create task map
        task_map = {}
        for json_task in task_data:
            task_map[json_task['id']] = json_task

        # there should only be one task that changed columns.
        # but just incase, make it a list
        tasks_that_changed_columns = []

        # now for each django-task, update order and task column
        for task in tasks:
            json_task = task_map[task.id]
            task.order = json_task['order']
            prev_task_column_id = task.task_column_id
            new_task_column_id = json_task['task_column']
            if prev_task_column_id != new_task_column_id:
                task.task_column_id = new_task_column_id
                tasks_that_changed_columns.append({
                    'task_id': task.id,
                    'prev_task_column_id': prev_task_column_id,
                    'new_task_column_id': new_task_column_id
                })

        Task.objects.bulk_update(tasks, ['order', 'task_column'])

        # now, for each task that changed columns, notify particpanta
        # As mentioned above, there should only be one task changed,
        # but just incase, loop through the list.
        # Also note: we can't do this in a signal because of the `bulk_update`.
        for moved_task_data in tasks_that_changed_columns:
            notify_participants_of_task_column_change.delay_on_commit(
                moved_task_data['task_id'],
                moved_task_data['prev_task_column_id'],
                moved_task_data['new_task_column_id'],
                request.user.id
            )

        return Response({
            'tasks': TaskSerializer(
                tasks,
                many=True,
                include_fields=TaskSerializer.Meta.deferred_fields).data
            },
            status=200
        )

    def _widget_create_task(self, request, *args, **kwargs):
        # NOTE: `is_authed` means the user is authenticated and has access to the project.
        # If they don't, the `creator` will be None and we will set the `one_off_email_set_by` field.

        task_request_data = request.data['task']
        task_metadata_request_data = request.data['task_metadata']
        html = request.data['html']

        is_authed = request.user.is_authenticated and task_request_data['project']

        # if the user is_authed, then they will have access to the project.
        # But if they are sending this method as non-authed, then they will only
        # send the `project_key`. We need to get the project_id based off this key.
        project_id = task_request_data['project']
        if not project_id:
            project_key = task_request_data['project_key']
            project = Project.objects.filter(key=project_key).first()
            if not project:
                raise exceptions.ValidationError(
                    'The project key is not implemented correctly on this website.'
                )
            else:
                project_id = project.id

        # make sure user has access to this project (if `is_authed`)
        if is_authed:
            if not Project.objects.filter(
                id=project_id,
                organization__memberships__user=request.user
            ).exists():
                raise exceptions.ValidationError(
                    'You do not have access to this project.'
                )

        assigned_to_id = task_request_data.get('assigned_to', None)
        if assigned_to_id:
            # make sure the assignee is part of this user's organization
            if not Membership.objects.filter(
                user_id=assigned_to_id,
                organization__memberships__user=request.user
            ).exists():
                raise exceptions.ValidationError(
                    'This member does not belong to your organization.'
                )

        task_column = TaskColumn.objects.get(project_id=project_id, name=TaskColumn.TASK_COLUMN_RAW_TASK)
        next_number = Task.objects.filter(project_id=project_id).count() + 1
        last_task_in_column = Task.objects.filter(
            project_id=project_id,
            task_column=task_column
        ).order_by('-order').first()
        task = Task.objects.create(
            title=task_request_data['title'],
            target_dom_path=task_request_data['target_dom_path'],
            design_edits=task_request_data['design_edits'],
            order=last_task_in_column.order + 1 if last_task_in_column else 1,
            project_id=project_id,
            task_column=task_column,
            assigned_to_id=assigned_to_id,
            creator=request.user if is_authed else None,
            one_off_email_set_by=task_request_data['one_off_email_set_by'],
            task_number=next_number
        )
        task_metadata = TaskMetadata.objects.create(
            task=task,
            url_origin=task_metadata_request_data['url_origin'],
            os_name=task_metadata_request_data['os_name'],
            os_version=task_metadata_request_data['os_version'],
            os_version_name=task_metadata_request_data['os_version_name'],
            browser_name=task_metadata_request_data['browser_name'],
            browser_version=task_metadata_request_data['browser_version'],
            selector=task_metadata_request_data['selector'],
            screen_height=task_metadata_request_data['screen_height'],
            screen_width=task_metadata_request_data['screen_width'],
            device_pixel_ratio=task_metadata_request_data['device_pixel_ratio'],
            browser_window_width=task_metadata_request_data['browser_window_width'],
            browser_window_height=task_metadata_request_data['browser_window_height'],
            color_depth=task_metadata_request_data['color_depth'],
            pixel_depth=task_metadata_request_data['pixel_depth'],
        )

        task_id = task.id
        browser_name = task_metadata.browser_name
        device_scale_factor = task_metadata.device_pixel_ratio
        window_width = task_metadata.browser_window_width
        window_height = task_metadata.browser_window_height
        task_html = TaskHtml.objects.create(task=task, html=html)

        # wrap in transaction.on_commit. see below links:
        # https://browniebroke.com/blog/making-celery-work-nicely-with-django-transactions/
        # https://docs.celeryproject.org/en/latest/userguide/tasks.html?highlight=on_commit#database-transactions
        create_screenshots_for_task.delay_on_commit(
            task_id, task_html.id, browser_name, device_scale_factor, window_width, window_height
        )

        return Response({
            'task': TaskSerializer(
                task,
                include_fields=TaskSerializer.Meta.deferred_fields).data,
            'task_metadata': TaskMetadataSerializer(
                task_metadata,
                include_fields=TaskMetadataSerializer.Meta.deferred_fields).data
            },
            status=201
        )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_task_from_widget(self, request, *args, **kwargs):
        return self._widget_create_task(request, *args, **kwargs)

    @action(detail=False, methods=['post'], permission_classes=(AllowAny,), authentication_classes=())
    @transaction.atomic
    def create_task_from_widget_anonymous(self, request, *args, **kwargs):
        return self._widget_create_task(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def change_column_from_widget(self, request, *args, **kwargs):
        task_id = request.data['task_id']
        task_column_id = request.data['task_column_id']

        # verify that the current user can update this task
        if not Task.objects.filter(
            id=task_id,
            project__organization__memberships__user=request.user
        ).exists():
            raise exceptions.ValidationError(
                'You do not have permission to update this task.'
            )

        task = Task.objects.get(id=task_id)
        task_column = TaskColumn.objects.get(id=task_column_id)
        last_task_in_column = task_column.tasks.order_by('order').all().last()

        # verify that the task_column belongs to the same project as the task
        if not Project.objects.filter(
            tasks=task,
            task_columns=task_column
        ).exists():
            raise exceptions.ValidationError(
                'This task column does not share the same project as the task.'
            )

        prev_task_column_id = task.task_column.id
        task.task_column = task_column
        task.order = last_task_in_column.order + 1 if last_task_in_column else 1
        task.save()

        # for consistency with `reorder` task method, manually call
        # the `notify_participants_of_task_column_change` method.
        notify_participants_of_task_column_change.delay_on_commit(
            task_id,
            prev_task_column_id,
            task_column_id,
            request.user.id
        )

        return Response({
            'task': TaskSerializer(
                task,
                include_fields=TaskSerializer.Meta.deferred_fields).data
            }, status=200
        )

    @action(detail=False, methods=['post'])
    def update_assignee(self, request, *args, **kwargs):
        assigned_to_id = request.data['assigned_to_id']
        task_id = request.data['task_id']

        # verify that the current user can update this task
        if not Task.objects.filter(
            id=task_id,
            project__organization__memberships__user=request.user
        ).exists():
            raise exceptions.ValidationError(
                'You do not have permission to update this task.'
            )

        # make sure the assignee is part of the current user's organization
        if assigned_to_id:
            if not Membership.objects.filter(
                user_id=assigned_to_id,
                organization__memberships__user=request.user
            ).exists():
                raise exceptions.ValidationError(
                    'This member does not belong to your organization.'
                )

        task = Task.objects.get(id=task_id)
        user = User.objects.get(id=assigned_to_id) if assigned_to_id else None
        task.assigned_to = user
        task.save()
        return Response({
            'task': TaskSerializer(
                task,
                include_fields=TaskSerializer.Meta.deferred_fields).data
            }, status=200
        )


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

    @action(detail=False, methods=['post'])
    def create_task_comment(self, request, *args, **kwargs):
        task_id = request.data['task']
        text = request.data['text']

        # make sure user has access to this task
        if not Task.objects.filter(
            id=task_id,
            project__organization__memberships__user=request.user
        ):
            raise exceptions.ValidationError(
                'You do not have access to comment on this task.'
            )

        task_comment = TaskComment.objects.create(
            text=text,
            task_id=task_id,
            creator=request.user,
        )

        return Response({
            'task_comment': TaskCommentSerializer(
                task_comment,
                include_fields=TaskCommentSerializer.Meta.deferred_fields).data
            },
            status=201
        )


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
