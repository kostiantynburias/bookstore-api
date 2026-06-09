from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration using the CustomUser model.
    """

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'phone_number', 'avatar']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'write_only': True, 'min_length': 8}
        }

    def validate_password(self, value):
        """
        Ensure the password meets the minimum length requirement.
        """
        if len(value) < 8:
            raise serializers.ValidationError('Пароль має складатися мінімум з 8 символів.')
        return value

    def create(self, validated_data):
        """
        Create and return a new CustomUser instance with a securely hashed password.
        """
        return User.objects.create_user(**validated_data)