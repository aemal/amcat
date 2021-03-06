from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from datetime import timedelta, datetime
# Inspired by
# http://stackoverflow.com/questions/14567586/token-authentication-for-restful-api-should-the-token-be-periodically-changed
class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super(ExpiringTokenAuthentication, self).authenticate_credentials(key)

        valid_until = token.created + timedelta(hours=48)
        if valid_until < datetime.now():
            raise exceptions.AuthenticationFailed('The token expired on {valid_until}. Please request a new token.'.format(**locals()))

        token.created = datetime.now()
        token.save()

        return token.user, token
