# import the User object
from django.contrib.auth.models import User
from content.models import Authtoken

class AuthTokenBackend(object):
    """Custom token based authentication backend."""
    # Create an authentication method
    # This is called by the standard Django login procedure
    def authenticate(self, authtoken=None):
        try:
            # Check if there is valid authtoken
            token = Authtoken.objects.get(uid=authtoken)
        except Authtoken.DoesNotExist:
            return None
        return token.user

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
