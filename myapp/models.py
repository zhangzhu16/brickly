import datetime
import time

from django.conf import settings
from django.db import models
from django.utils import timezone

from .managers import EmailManager, EmailConfirmationManager
#  from brickly.utils.crypto import Crypto  #未提供
#  from brickly.utils.logger import Logger  #未提供

#  logger = Logger.get_logger(__name__)


class Email(models.Model):
    address = models.EmailField('address')
    is_verified = models.BooleanField("is_verified", default=False)
    is_primary = models.BooleanField("is_primary", default=False)
    label = models.CharField('label', max_length=255, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='users')

    objects = EmailManager()

    class Meta:
        verbose_name = "email"
        verbose_name_plural = "emails"
        unique_together = [("user", "address")]

    def __init__(self, *args, **kwargs):
        super(Email, self).__init__(*args, **kwargs)
        self.confirmation = None

    def __str__(self):
        return "{0} ({1})".format(self.address, self.user)

    def set_as_primary(self):
        emails = Email.objects.filter(user=self.user).filter(is_primary=True).exclude(address=self.address).all()
        for email in emails:
            email.is_primary = False
            email.save()
        self.is_primary = True
        self.save()
        self.user.set_email(self.address)
        self.user.save()
        return True

    def verify(self):
        if not self.is_verified:
            self.is_verified = True
            if self.is_primary:
                self.set_as_primary()
            self.save()
        return self

    #  def create_confirmation(self, digits):
        #  code = None
        #  while True:
            #  code = Crypto.get_random_string(length=digits, allowed_chars=r'0123456789')
            #  email_ids = Email.objects.filter(user=self.user).values_list('id', flat=True)
            #  if not EmailConfirmation.objects.filter(token=code, email_id__in=email_ids).exists():
                #  break
        #  defaults = {'token': code}
        #  return EmailConfirmation.objects.get_or_create(email=self, defaults=defaults)[0]


class EmailConfirmation(models.Model):
    created = models.DateTimeField(default=timezone.now)
    sent = models.DateTimeField(null=True)
    token = models.CharField(max_length=64, unique=True)
    email = models.ForeignKey(Email, on_delete=models.CASCADE)

    objects = EmailConfirmationManager()

    class Meta:
        verbose_name = "email confirmation"
        verbose_name_plural = "email confirmations"

    def __str__(self):
        return "confirmation for {0}".format(self.email)

    @classmethod
    def get_checked(cls, user, token, confirm_expire_secs):
        try:
            email_ids = Email.objects.filter(user=user).values_list('id', flat=True)
            record = cls.objects.get(token=token, email_id__in=email_ids)
        except cls.DoesNotExist:
            return None
        else:
            return None if record.token_expired(confirm_expire_secs) else record

    def token_expired(self, confirm_expire_secs):
        expiration_date = self.sent + datetime.timedelta(seconds=confirm_expire_secs)
        return expiration_date <= timezone.now()

    token_expired.boolean = True


