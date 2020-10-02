from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from collab_app.tasks import (
    send_email
)


"""
Send email on invite creation, acceptance, cancelation, or deny
"""


@receiver(post_save, sender='collab_app.Invite')
def email_on_invite_change(sender, instance, created, **kwargs):
    invite = instance  # readability
    state_changed = invite.get_field_diff('state')

    if created:
        organization_name = invite.organization.name
        subject = f'You have been invited to join {organization_name} organization on Collab Sauce!'
        inviter = invite.inviter
        body = render_to_string('emails/invites/created.html', {
            'email': invite.email,
            'key': invite.key,
            'inviter_name': f'{inviter.first_name} {inviter.last_name}',
            'organization_name': organization_name
        })
        send_email(subject, body, settings.EMAIL_HOST_USER, [invite.email], fail_silently=False)

    # TODO: send emails on user acceptance?
    # elif state_changed and invite.state == invite.ACCEPTED:
    #     subject = 'Invite for %s has been accepted!' % invite.email
    #     body = render_to_string('emails/invites/accepted.html', {
    #         'potential_player_username': invite.potential_player.username,
    #         'potential_player_email': invite.email,
    #         'league_name': invite.league.name
    #     })
    #     send_email(subject, body, 'fakeemail@gmail.com', [invite.inviter.email], fail_silently=True)

    #     # also send email to the user accepting the invite, welcoming them to the website
    #     subject = 'Welcome to WEBSITE_NAME!'
    #     body = render_to_string('emails/users/email_verification.html', {
    #         'unique_key': invite.potential_player.confirmed_email.key,
    #         'created': True
    #     })
    #     send_email(subject, body, 'fakeemail@gmail.com', [invite.email], fail_silently=True)

    # TODO: send emails on user denial?
    # elif state_changed and invite.state == invite.DENIED:
    #     subject = 'Invite for %s has been denied' % invite.email
    #     body = render_to_string('emails/invites/denied.html', {
    #         'potential_player_username': invite.potential_player.username,
    #         'potential_player_email': invite.email,
    #         'league_name': invite.league.name
    #     })
    #     send_email(subject, body, 'fakeemail@gmail.com', [invite.inviter.email], fail_silently=True)

    elif state_changed and invite.state == invite.InviteState.CANCELED:
        organization_name = invite.organization.name
        inviter = invite.inviter
        subject = f'Your invitation to join {organization_name} organization has been canceled'
        body = render_to_string('emails/invites/canceled.html', {
            'inviter_name': f'{inviter.first_name} {inviter.last_name}',
            'organization_name': organization_name
        })
        send_email(subject, body, settings.EMAIL_HOST_USER, [invite.email], fail_silently=False)
