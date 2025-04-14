from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class CorreoBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        Usuario = get_user_model()
        try:
            user = Usuario.objects.get(correo=username)
        except Usuario.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
