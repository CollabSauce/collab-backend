import json

from django.contrib.auth import get_user_model
from model_mommy import mommy

from collab_app.models import (
    Invite,
    Membership,
    Organization,
)
from tests.mixins import BaseApiSetUp

User = get_user_model()


class InvitePermissionTestCase(BaseApiSetUp):

    def setUp(self):
        super(InvitePermissionTestCase, self).setUp()

        self.other_user = mommy.make(User, email='hi@hi.com')
        # self.third_user = mommy.make(User)

        self.organization1 = mommy.make(Organization)
        self.organization2 = mommy.make(Organization)
        self.organization3 = mommy.make(Organization)

        self.m1 = mommy.make(
            Membership,
            role=Membership.RoleType.ADMIN,
            user=self.user,
            organization=self.organization1
        )
        self.m2 = mommy.make(
            Membership,
            role=Membership.RoleType.DASHBOARD,
            user=self.other_user,
            organization=self.organization2
        )
        self.m3 = mommy.make(
            Membership,
            role=Membership.RoleType.DASHBOARD,
            user=self.user,
            organization=self.organization3
        )

        self.i1 = mommy.make(Invite, organization=self.organization1, email='hi@hi.com', key='abd')
        self.i2 = mommy.make(Invite, organization=self.organization2, key='aad')
        self.i3 = mommy.make(Invite, organization=self.organization3, key='arbd')

    def test_can_view_invites_if_member_of_org(self):
        response = self.client.get('/api/invites')
        content = json.loads(response.content)
        content_ids = [c['id'] for c in content['invites']]
        self.assertEqual(len(content_ids), 2)
        self.assertTrue(self.i1.id in content_ids)
        self.assertTrue(self.i3.id in content_ids)

    def test_create_invite(self):
        data = {
            'organization': self.organization3.id,
            'email': 'hello@hi.com',
        }
        response = self.client.post('/api/invites/create_invite', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'You must be an admin of this organization to send invites.')

        # change user to admin role and it should work
        self.m3.role = Membership.RoleType.ADMIN
        self.m3.save()
        response = self.client.post('/api/invites/create_invite', data)
        self.assertEqual(response.status_code, 201)

    def test_accept_invite(self):
        data = {'invite': self.i1.id}
        response = self.client.post('/api/invites/accept_invite/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'This invite does not belong to you.')

        self.client.force_authenticate(user=self.other_user)
        response = self.client.post('/api/invites/accept_invite/', data)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/invites/accept_invite/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'Can no longer accept this invitation.')

    def test_deny_invite(self):
        data = {'invite': self.i1.id}
        response = self.client.post('/api/invites/deny_invite/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'This invite does not belong to you.')

        self.client.force_authenticate(user=self.other_user)
        response = self.client.post('/api/invites/deny_invite/', data)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/invites/deny_invite/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'Can no longer deny this invitation.')

    def test_cancel_invite(self):
        data = {'invite': self.i3.id}
        response = self.client.post('/api/invites/cancel_invite/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'You must be an admin of this organization to cancel invites.')

        # change user to admin role and it should work
        self.m3.role = Membership.RoleType.ADMIN
        self.m3.save()

        response = self.client.post('/api/invites/cancel_invite/', data)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/invites/cancel_invite/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(content[0], 'Can no longer cancel this invitation.')
