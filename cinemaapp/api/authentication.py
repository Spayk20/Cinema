from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.utils import timezone
from datetime import timedelta
from cinemaapp.models import MyToken


class CustomTokenAuthentication(TokenAuthentication):

    def authenticate_credentials(self, key):
        try:
            token = MyToken.objects.get(key=key)
        except MyToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid Token")
        if not token.user.is_superuser:
            if token.time_to_die + timedelta(minutes=5) < timezone.now():
                token.delete()
                raise exceptions.AuthenticationFailed("Invalid Token")
            else:
                token.time_to_die = timezone.now()
                token.save()
        return token.user, token
