from dj_rest_auth.serializers import (
    PasswordResetSerializer as RestAuthPasswordResetSerializer,
)


class PasswordResetSerializer(RestAuthPasswordResetSerializer):

    def get_email_options(self):
        return {
            'email_template_name': 'password_reset_email.txt',
            'html_email_template_name': 'password_reset_email.html'
        }
