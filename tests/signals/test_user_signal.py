from model_mommy import mommy
from rest_framework.test import APITestCase

from collab_app.models import (
    Profile,
    User
)


class UserSignalTestCase(APITestCase):

    def test_user_creation(self):
        self.assertEqual(0, Profile.objects.count())
        user = mommy.make(User)

        self.assertEqual(1, Profile.objects.count())
        self.assertIsNotNone(user.profile)
