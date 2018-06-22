from django.db import models


class EmailManager(models.Manager):
    def add_email(self, user, address, **kwargs):
        confirm = kwargs.pop("confirm", False)
        email_address = self.create(user=user, address=address, **kwargs)
        if confirm and not email_address.verified:
            email_address.send_confirmation()
        return email_address

    def get_primary(self, user, verify_check=True):
        obj = self.filter(user=user, primary=True)
        if verify_check:
            obj = obj.filter(verified=True)

        obj = obj.first()
        if obj:
            return obj
        else:
            return None

    def get_users_for(self, address):
        # this is a list rather than a generator because we probably want to do a len() on it right away
        return [address.user for address in self.filter(verified=True, address=address)]


class EmailConfirmationManager(models.Manager):
    def delete_expired_confirmations(self):
        for confirmation in self.all():
            if confirmation.key_expired():
                confirmation.delete()
