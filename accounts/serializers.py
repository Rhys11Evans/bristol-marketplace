from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Accepts: username, password, password_confirm, role
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )
        # Only allow CUSTOMER or PRODUCER
        role = attrs.get('role', User.Role.CUSTOMER)
        if role not in [User.Role.CUSTOMER, User.Role.PRODUCER, User.Role.ADMIN]:
            raise serializers.ValidationError(
                {'role': 'Role must be CUSTOMER, PRODUCER, or ADMIN.'}
            )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer to return user info (GET /me)."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'date_joined']
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Serializer for login request."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AdminUserSerializer(serializers.ModelSerializer):
    """Full user details visible to admin."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'username', 'email', 'date_joined', 'last_login']


class UpdateRoleSerializer(serializers.ModelSerializer):
    """Admin can update a user's role or active status."""

    class Meta:
        model = User
        fields = ['role', 'is_active']

    def validate_role(self, value):
        if value not in [User.Role.CUSTOMER, User.Role.PRODUCER, User.Role.ADMIN]:
            raise serializers.ValidationError('Invalid role.')
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    S2-T1: Custom JWT token that includes user role in the response.
    Returns access token, refresh token, AND user info.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the token payload
        token['role'] = user.role
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user info to the response body
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }
        return data
