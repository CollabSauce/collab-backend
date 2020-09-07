from django.db.models import Q

from collab_app.models import (
    Invite,
    Organization,
    Membership,
    Profile,
    Project,
    Task,
    TaskMetadata,
    TaskComment,
    User,
)


class BaseObjectPermission(object):
    """
    Base Object Permission class.

    By default, a user can read or update on a model object.
    Update the appropriate method to apply permissions on the action.
    """
    def read(self, queryset, user):
        return queryset

    def update(self, queryset, user):
        return queryset


class InvitePermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(organization__memberships__user=user)


class MembershipPermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(organization__memberships__user=user)


class OrganizationPermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(memberships__user=user)

    def update(self, queryset, user):
        # you can update an org if you are the admin of the org
        return queryset.filter(
            Q(memberships__role=Membership.RoleType.ADMIN) &
            Q(memberships__user=user)
        )


class ProfilePermission(BaseObjectPermission):
    def read(self, queryset, user):
        # can read profile that belong to you
        return queryset.filter(user=user)

    def update(self, queryset, user):
        # can only update profile that belong to you
        return queryset.filter(user=user)


class ProjectPermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(organization__memberships__user=user)

    def update(self, queryset, user):
        return queryset.filter(organization__memberships__user=user)


class TaskPermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(project__organization__memberships__user=user)

    def update(self, queryset, user):
        return queryset.filter(creator=user)


class TaskMetadataPermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(task__project__organization__memberships__user=user)

    def update(self, queryset, user):
        return queryset.filter(task__creator=user)  # remove permission?


class TaskCommentPermission(BaseObjectPermission):
    def read(self, queryset, user):
        return queryset.filter(task__project__organization__memberships__user=user)

    def update(self, queryset, user):
        return queryset.filter(creator=user)  # remove permission?


class UserPermission(BaseObjectPermission):
    def read(self, queryset, user):
        # can read your own user, or other users of the orgs you belong to
        return queryset.filter(
            Q(id=user.id) |
            Q(memberships__organization__memberships__user=user)
        )

    def update(self, queryset, user):
        # can only update your own user
        return queryset.filter(id=user.id)


class BaseQuerySetPermission(object):
    object_perm_mapping = {
        Invite: InvitePermission(),
        Membership: MembershipPermission(),
        Organization: OrganizationPermission(),
        Profile: ProfilePermission(),
        Project: ProjectPermission(),
        Task: TaskPermission(),
        TaskMetadata: TaskMetadataPermission(),
        TaskComment: TaskCommentPermission(),
        User: UserPermission(),
    }

    # turn sideload filtering off for specifc models
    no_sideload_filtering = ()

    def queryset_filter(self, queryset, model, request, sideload=False):
        permission = self.object_perm_mapping.get(model)
        user = request.user

        # if the user is a superuser, permissions don't apply
        if user.is_superuser:
            return queryset

        # if a permission wasn't set up for a particular resource/model,
        # then permissions don't apply
        if permission is None:
            return queryset

        # If this is a sideload filter, and we turn sideload filtering off
        # for a particular model/resource, don't apply the sideload permissions
        if sideload and model in self.no_sideload_filtering:
            return queryset

        if request.method == 'GET':
            return permission.read(queryset, user)
        elif request.method == 'DELETE' and 'delete' in dir(permission):
            # If Delete, and the permission has a delete method, use the delete method.
            # Else just use the normal update method.
            return permission.delete(queryset, user)
        elif request.method in ('PUT', 'PATCH', 'DELETE'):
            return permission.update(queryset, user)
        else:
            return queryset


class GateKeeper(BaseQuerySetPermission):
    """
    Object level permissions on direct get, patch, put, or delete.
    """

    # Used by Rest Framework
    def get_queryset(self):
        queryset = super(GateKeeper, self).get_queryset()
        return self.queryset_filter(queryset, self.model, self.request)


class SideGateKeeper(BaseQuerySetPermission):
    """
    Object level sideload permissions on `get`
    """

    # Used by Dynamic Rest Framework to filter sideloads
    def filter_queryset(self, queryset):
        return self.queryset_filter(queryset, self.Meta.model, self.context['request'], sideload=True)
