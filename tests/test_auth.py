import json

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework.test import APITestCase
from model_mommy import mommy

User = get_user_model()


class LoginTestCase(APITestCase):

    def setUp(self):
        User.objects.create_user(
            email='georgecastanza@seinfeld.com',
            password='marine_biologist'
        )

    def test_cannot_access_api_when_unauthenticated(self):
        response = self.client.get('/api/users/')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(content['detail'], 'Authentication credentials were not provided.')

    def test_can_login(self):
        credentials = {'email': 'georgecastanza@seinfeld.com', 'password': 'marine_biologist'}
        response = self.client.post('/rest-auth/login/', credentials, format='json')
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(content['key'])


class SignupTestCase(APITestCase):

    def setUp(self):
        # need to do User.Objects.create_user() (not mommy.make) so has_usable_password
        # is correctly set to True
        self.used_email = 'hi@hi.com'
        self.user = User.objects.create_user(
            email=self.used_email, password='hello'
        )
        mail.outbox = []

    def test_can_signup_and_login(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
        data = {
            'password1': 'hungryhippo',
            'password2': 'hungryhippo',
            'email': 'first@last.com'
        }
        # first create/register user
        response = self.client.post('/rest-auth/registration/', data)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(content['key'])
        self.assertEqual(User.objects.count(), 2)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [data['email']])
        self.assertEqual(mail.outbox[0].subject, 'Welcome to example.com!')
        self.assertTrue('Hello from example.com!' in mail.outbox[0].body)
        self.assertTrue(
            'You\'re receiving this e-mail because user first signed up for example.com' in mail.outbox[0].body
        )

        # now try logging in - test to make sure username and
        # password were saved properly
        credentials = {'email': 'first@last.com', 'password': 'hungryhippo'}
        response = self.client.post('/rest-auth/login/', credentials)
        content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(content['key'])

    def test_can_change_password(self):
        self.client.force_authenticate(user=self.user)
        self.user.set_password('existing_password')
        self.user.save()

        data = {
            'old_password': 'existing_password',
            'new_password1': 'new_password',
            'new_password2': 'new_password'
        }
        response = self.client.post('/rest-auth/password/change/', data)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(id=self.user.id)
        self.assertTrue(user.check_password('new_password'))

    def test_can_resend_confirmation_email(self):
        self.client.force_authenticate(user=self.user)
        mommy.make(EmailAddress, user=self.user, email=self.user.email)
        other_user = mommy.make(User)

        response = self.client.post('/api/users/%s/resend_verification_email' % other_user.id)
        self.assertEqual(response.status_code, 404)

        response = self.client.post('/api/users/%s/resend_verification_email' % self.user.id)
        self.assertEqual(response.status_code, 201)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Please Confirm Your E-mail Address')

    def test_can_verify_email(self):
        mommy.make(EmailAddress, user=self.user, email=self.user.email)
        self.assertFalse(EmailAddress.objects.filter(user=self.user, verified=True).exists())

        data = {'key': 'wrong_verification_key'}

        response = self.client.post('/rest-auth/registration/verify-email/', data)
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(content['detail'], 'Not found.')

        # resend verifcation email and get key
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/users/%s/resend_verification_email' % self.user.id)
        start_index = mail.outbox[0].body.find('key=') + 4
        end_index = mail.outbox[0].body.find('\n\nThank you from')
        data['key'] = mail.outbox[0].body[start_index:end_index]

        # # signout (shouldn't need to be authenticated to verify email)
        self.client.force_authenticate(user=None)

        response = self.client.post('/rest-auth/registration/verify-email/', data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(EmailAddress.objects.filter(user=self.user, verified=True).exists())

    def test_resets_password_and_sends_email_and_can_reset_password(self):
        data = {'email': self.user.email}

        old_password = 'hello'
        self.assertTrue(self.user.check_password(old_password))

        response = self.client.post('/rest-auth/password/reset/', data)
        self.assertEqual(response.status_code, 200)

        # password not yet changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(old_password))

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[0].subject, 'Password reset on example.com')
        self.assertTrue(
            'You\'re receiving this e-mail because you have requested ' +
            'a password reset for your CollabSauce user account' in mail.outbox[0].body
        )
        self.assertTrue('Please go to the following page and choose a new password:' in mail.outbox[0].body)

        # now actually reset the password from the info in the email
        start_index_uid = mail.outbox[0].body.find('uid=') + 4
        end_index_uid = start_index_uid + 2
        uid = mail.outbox[0].body[start_index_uid:end_index_uid]

        start_index_key = mail.outbox[0].body.find('token=') + 6
        end_index_key = mail.outbox[0].body.find('\n\n\n\nThanks for using CollabSauce!')
        key = mail.outbox[0].body[start_index_key: end_index_key]

        password_data = {
            'new_password1': 'mylilpassword',
            'new_password2': 'mylilpassword',
            'token': key,
            'uid': uid
        }

        response = self.client.post('/rest-auth/password/reset/confirm/', password_data)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(old_password))
        self.assertTrue(self.user.check_password('mylilpassword'))
