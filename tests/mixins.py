from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from model_mommy import mommy

User = get_user_model()


class BaseApiSetUp(APITestCase):

    def setUp(self):
        self.user = mommy.make(User)
        self.superuser = mommy.make(User, is_superuser=True)
        self.client.force_authenticate(user=self.user)
