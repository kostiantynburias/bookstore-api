from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration. Accepts username, email and password."""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_password(self, value):
        """Ensure password is at least 8 characters long."""
        if len(value) < 8:
            raise serializers.ValidationError('Пароль має складатися мінімум з 8 символів.')
        return value
    
    def create(self, validated_data):
        """Create and return a new user with hashed password."""
        user = User.objects.create_user(**validated_data)
        return user