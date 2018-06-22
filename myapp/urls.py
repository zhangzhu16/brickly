from django.urls import path

from .views import (EmailList, EmailDelete, EmailAdd, EmailSendConfirmation,
                    EmailConfirm, EmailSetPrimary, Index)

app_name = "myapp"

urlpatterns = [
    path('get/', EmailList.as_view()),
    path('remove/', EmailDelete.as_view()),
    path('add/', EmailAdd.as_view()),
    path('send_confirmation/', EmailSendConfirmation.as_view()),
    path('confirm_primary/', EmailConfirm.as_view()),
    path('set_primary/', EmailSetPrimary.as_view()),
    path('index/', Index.index),
]



