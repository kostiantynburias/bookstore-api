from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from apps.users.serializers import RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user. Accessible to everyone.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]