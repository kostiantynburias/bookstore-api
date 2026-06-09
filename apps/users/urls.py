from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from apps.users.views import RegisterView

decorated_token_obtain = method_decorator(
    name='post',
    decorator=extend_schema(
        tags=["Authentication"],
        summary="Obtain JWT token pair",
        description="Takes user credentials (username and password) and returns access and refresh tokens.",
        responses={
            200: OpenApiResponse(
                description="Successfully generated tokens.",
                examples=[
                    OpenApiExample(
                        name="Valid credentials response",
                        value={
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Incorrect username or password.")
        }
    )
)(TokenObtainPairView)

decorated_token_refresh = method_decorator(
    name='post',
    decorator=extend_schema(
        tags=["Authentication"],
        summary="Refresh access token",
        description="Takes a valid refresh JWT token and returns a new access token.",
        responses={
            200: OpenApiResponse(
                description="Successfully refreshed access token.",
                examples=[
                    OpenApiExample(
                        name="Valid refresh response",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Token is invalid or expired.")
        }
    )
)(TokenRefreshView)


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', decorated_token_obtain.as_view(), name='token_obtain_pair'),
    path('token/refresh/', decorated_token_refresh.as_view(), name='token_refresh'),
]