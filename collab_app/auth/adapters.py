from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class AuthAccountAdapter(DefaultAccountAdapter):

    def get_email_confirmation_url(self, request, emailconfirmation):
        # overwrite this method to return 'company_url.com/verify-email?key=...'
        # instead of `company_url.com/verify-email/key...
        url = reverse(
            "account_confirm_email",
            args=[emailconfirmation.key])
        url = url.replace('verify-email/', 'verify-email?key=')
        ret = 'http://www.TBD_PLACEHOLDER.com' + url
        return ret
