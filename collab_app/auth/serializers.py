from rest_framework import serializers
from dj_rest_auth.serializers import (
    PasswordResetSerializer as RestAuthPasswordResetSerializer,
)
from dj_rest_auth.registration.serializers import (
    RegisterSerializer as RestAuthRegisterSerializer,
)


class PasswordResetSerializer(RestAuthPasswordResetSerializer):

    def get_email_options(self):
        return {
            'email_template_name': 'password_reset_email.txt',
            'html_email_template_name': 'password_reset_email.html'
        }


class RegisterSerializer(RestAuthRegisterSerializer):
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)

    # overwrite this method to include first and last name
    def get_cleaned_data(self):
        data = super(RegisterSerializer, self).get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        return data
