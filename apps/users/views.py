from django.contrib.auth.models import User
from rest_framework import generics, permissions

from apps.users.serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user. Accessible to everyone.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]