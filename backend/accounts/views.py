from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, SetPasswordSerializer,
)
from .permissions import IsManagerOrAbove, IsOwner


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current authenticated user's profile."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_me(request):
    """Update the current user's profile."""
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change the current user's password."""
    serializer = PasswordChangeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.check_password(serializer.validated_data['old_password']):
        return Response({'old_password': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response({'message': 'Password changed successfully.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_password(request):
    """Set a new password on first login (must_change_password=True). No old password required."""
    if not request.user.must_change_password:
        return Response({'error': 'Password change not required.'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = SetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.must_change_password = False
    request.user.save(update_fields=['password', 'must_change_password'])
    return Response({'message': 'Password set successfully.'})


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def user_list(request):
    """List all users (managers/owners only). Supports ?role= filter."""
    users = User.objects.all()
    role = request.query_params.get('role')
    if role:
        users = users.filter(role=role)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsOwner])
def user_create(request):
    """Create a new user (owners only)."""
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsManagerOrAbove])
def user_detail(request, user_id):
    """Get a user's profile (managers/owners only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsOwner])
def user_update_role(request, user_id):
    """Update a user's role (owners only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    new_role = request.data.get('role')
    if new_role not in dict(User.ROLE_CHOICES):
        return Response({'error': f'Invalid role. Choose from: {", ".join(dict(User.ROLE_CHOICES).keys())}'}, status=status.HTTP_400_BAD_REQUEST)

    if user == request.user and new_role != 'owner':
        return Response({'error': 'Cannot demote yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    user.role = new_role
    user.save(update_fields=['role'])
    return Response(UserSerializer(user).data)


@api_view(['POST'])
@permission_classes([IsOwner])
def user_deactivate(request, user_id):
    """Deactivate a user (owners only)."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if user == request.user:
        return Response({'error': 'Cannot deactivate yourself.'}, status=status.HTTP_400_BAD_REQUEST)

    user.is_active = False
    user.save(update_fields=['is_active'])
    return Response({'message': f'User {user.username} deactivated.'})
