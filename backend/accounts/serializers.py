from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT token to include role and tier claims."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['tier'] = user.tier
        token['name'] = user.get_full_name()
        token['email'] = user.email
        token['must_change_password'] = user.must_change_password
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    """Public user profile serializer."""
    tier = serializers.ReadOnlyField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'tier', 'phone', 'bio', 'avatar_initials', 'is_active_staff',
            'must_change_password', 'date_joined',
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'tier']

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (admin only)."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'phone', 'bio',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profiles."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'bio', 'avatar_initials']


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


class SetPasswordSerializer(serializers.Serializer):
    """Serializer for first-login password set (no old password needed)."""
    new_password = serializers.CharField(required=True, min_length=8)
