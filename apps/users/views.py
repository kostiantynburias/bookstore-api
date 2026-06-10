from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from apps.users.serializers import RegisterSerializer

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary="Register new user",
    description="Takes user credentials, validates them, creates a new active user in the system, and returns their account details.",
    responses={
        201: OpenApiResponse(
            response=RegisterSerializer,
            description="User successfully registered.",
            examples=[
                OpenApiExample(
                    name="Successful registration",
                    value={
                        "id": 12,
                        "username": "new_bookworm",
                        "email": "user@example.com"
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Validation error (e.g., username already exists, weak password, or invalid email format)."
        )
    }
)
class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user. Accessible to everyone.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]