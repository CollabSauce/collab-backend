import json

from model_mommy import mommy

from collab_app.models import (
    User
)
from tests.mixins import BaseApiSetUp


class UserPermissionTestCase(BaseApiSetUp):

    def setUp(self):
        super(UserPermissionTestCase, self).setUp()

        # create extra user
        self.u2 = mommy.make(User)

    def test_super_user_can_view_all_users(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/users')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(content['users']), 3)

    def test_regular_user_cannot_view_all_users(self):
        response = self.client.get('/api/users')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(content['users']), 1)
        self.assertEqual(content['users'][0]['id'], self.user.id)

    def test_super_user_viewing_a_single_user(self):
        # superuser should be able to retrieve itself
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get('/api/users/%s' % self.superuser.id)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['user']['id'], self.superuser.id)

        # staff user should be able to retrieve anyone else as well
        response = self.client.get('/api/users/%s' % self.user.id)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['user']['id'], self.user.id)

    def test_regular_user_viewing_a_single_user(self):
        # user should be able to retrieve itself
        response = self.client.get('/api/users/%s' % self.user.id)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['user']['id'], self.user.id)

        # user should not be able to retrieve anyone else
        response = self.client.get('/api/users/%s' % self.superuser.id)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(content['detail'], 'Not found.')

    def test_retrieving_users_me_endpoint(self):
        # user should be able to retrieve itself from api/users/me
        response = self.client.get('/api/users/me')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(content['user']['id'], self.user.id)

    def test_user_endpoint_is_readonly(self):
        response = self.client.patch('/api/users/%s' % self.user.id, {'first_name': 'new_name'})
        self.assertEqual(response.status_code, 405)

        response = self.client.post('/api/users/')
        self.assertEqual(response.status_code, 405)

        response = self.client.delete('/api/users/%s' % self.user.id)
        self.assertEqual(response.status_code, 405)

    def test_sideload_filtering(self):
        # this user should not be readable
        # nothing to test for now
        pass
