from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
#  from user_agents import parse

from .models import Email, EmailConfirmation
from .ownView import RestView, StatusCode
from .datetime import Datetime


from .serializers import EmailSerializer


class Index:
    def index(request):
        return  HttpResponse('hello')


class EmailList(RestView):
    def _get(self):
        return self.success(EmailSerializer(Email.objects.filter(user=self._user).all(), many=True).data)


class EmailDelete(RestView):
    def _delete(self):
        email_id = self.get_int_param('id', required=True)
        try:
            email = Email.objects.get(pk=email_id, user=self._user)
        except Email.DoesNotExist:
            return self.error(StatusCode.ERROR_NOT_FOUND, _("Email not associated with account"))

        if email.is_primary:
            return self.error(StatusCode.ERROR_NOT_ALLOWED, _("Cannot remove account primary email"))

        email.delete()
        return self.success({}, _("Email successfully removed"))


class EmailAdd(RestView):
    def _post(self):
        email_address = self.get_email_param('email', required=True)
        if Email.objects.filter(address__iexact=email_address).exists():
            return self.error(StatusCode.ERROR_CONFLICT, _("Email already in use."))
        Email.objects.get_or_create(user=self._user, address=email_address,
                                    defaults={'is_verified': False, 'is_primary': False})
        return self.success({}, _("Email successfully added."))


#  class EmailSendConfirmation(TokenBase):
class EmailSendConfirmation(RestView):
    def _get(self):
        email_address = self.get_email_param('email', required=True)
        try:
            email = Email.objects.get(user=self._user, address__iexact=email_address)
        except Email.DoesNotExist:
            return self.error(StatusCode.ERROR_NOT_FOUND, _("Email not associated with any account."))

        if email.is_verified:
            return self.error(StatusCode.ERROR_NOT_ALLOWED, _("Email address already confirmed."))

        email.confirmation = email.create_confirmation(settings.WEBSITE['confirmation_digits'])
        email.confirmation.sent = Datetime.utcnow()
        email.confirmation.save()

        user_agent = parse(self._request.META.get('HTTP_USER_AGENT', ''))
        context = {
            'website_url': settings.WEBSITE['url'],
            'support_url': settings.WEBSITE['support_url'],
            'first_name': self._user.first_name,
            'token': email.confirmation.token,
            'operating_system': user_agent.os.family,
            'browser_name': user_agent.browser.family,
        }

        translation.activate(self._user.language)
        subject = render_to_string('emails/confirm_subject.txt', context)
        text = render_to_string('emails/confirm.txt', context)
        html = render_to_string('emails/confirm.html', context)
        from_email = settings.WEBSITE['support_email']
        send_mail(
            subject=subject.replace('\n', ''),
            message=text,
            from_email=from_email,
            recipient_list=(email.address,),
            html_message=html,
        )
        logger.info('Sent email confirmation email to user %d (%s)', self._user.id, email.address)

        api_token = self._generate_token('email_confirm')['token']

        results = {
            "confirm": {
                "duration": settings.WEBSITE['confirmation_timeout'] * 1000,
                "message": _("Email verification code sent successfully."),
                "object": {
                    'id': email.id,
                    'label': email.label,
                    'address': email.address,
                    'is_verified': email.is_verified,
                    'is_primary': email.is_primary,
                },
                "title": "Confirm Email",
                "type": "m_email",
                "service": "signup",
                "resend": {
                    "key": "email",
                    "text": "Resend",
                    "url": "account/email/send_confirmation",
                    "value": email.address,
                    "method": "GET"
                },
                "submit": {
                    "text": "Confirm",
                    "url": "account/email/confirm_primary",
                    "key": 'token',
                    "method": "GET"
                },
            },
            'token': api_token,
        }
        return self.success(results, _("Email confirmation sent successfully."), status_code=StatusCode.SUCCESS_CONFIRM)


class EmailConfirm(RestView):
    def _get(self):
        token = self.get_string_param('token', required=True).strip()
        if not token:
            return self.error(StatusCode.ERROR_NOT_FOUND, _('Please enter confirmation code.'))

        confirmation = EmailConfirmation.get_checked(self._user, token, settings.WEBSITE['confirmation_timeout'])
        if not confirmation:
            return self.error(StatusCode.ERROR_FORBIDDEN, _('Incorrect confirmation code.'))

        email = confirmation.email
        email.is_verified = True
        email.set_as_primary()

        return self.success({}, _('User email confirmed successfully and set as primary email.'))


class EmailSetPrimary(RestView):
    def _post(self):
        email_id = self.get_int_param('id', required=True)
        try:
            email = Email.objects.get(user=self._user, pk=email_id)
        except Email.DoesNotExist:
            return self.error(StatusCode.ERROR_NOT_FOUND, _("Email not associated with account."))

        if not email.is_verified:
            return self.error(StatusCode.ERROR_NOT_ALLOWED, _("Cannot set primary email to unverified address."))
        email.set_as_primary()

        return self.success(EmailSerializer(email), _("Successfully set account primary email address"))
