from django.contrib import admin
from .models import Email, EmailConfirmation

admin.site.register((Email, EmailConfirmation))
