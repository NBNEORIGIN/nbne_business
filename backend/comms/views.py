from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from accounts.permissions import IsStaffOrAbove
from .models import Channel, Message, PushSubscription
from .serializers import (
    ChannelSerializer, ChannelCreateSerializer,
    MessageSerializer, MessageCreateSerializer,
)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def channel_list(request):
    """List channels the user is a member of (staff+)."""
    channels = Channel.objects.filter(is_archived=False)
    if not request.user.is_manager_or_above:
        channels = channels.filter(members=request.user)
    return Response(ChannelSerializer(channels, many=True).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def channel_create(request):
    """Create a new channel (staff+)."""
    serializer = ChannelCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    channel = serializer.save(created_by=request.user)
    channel.members.add(request.user)
    return Response(ChannelSerializer(channel).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def channel_detail(request, channel_id):
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(ChannelSerializer(channel).data)


@api_view(['GET'])
@permission_classes([IsStaffOrAbove])
def message_list(request, channel_id):
    """List messages in a channel (staff+)."""
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
    limit = int(request.query_params.get('limit', 50))
    messages = Message.objects.filter(channel=channel).select_related('sender').prefetch_related('attachments').order_by('-created_at')[:limit]
    messages = list(reversed(messages))
    return Response(MessageSerializer(messages, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def message_create(request, channel_id):
    """Send a message to a channel (staff+). Supports file attachments via multipart."""
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
    body = request.data.get('body', '').strip()
    files = request.FILES.getlist('files')
    if not body and not files:
        return Response({'error': 'Message body or file is required.'}, status=status.HTTP_400_BAD_REQUEST)
    parent = None
    parent_id = request.data.get('parent')
    if parent_id:
        try:
            parent = Message.objects.get(id=int(parent_id), channel=channel)
        except (Message.DoesNotExist, ValueError):
            return Response({'error': 'Parent message not found'}, status=status.HTTP_404_NOT_FOUND)
    msg = Message.objects.create(
        channel=channel, sender=request.user,
        body=body or '', parent=parent,
    )
    # Handle file attachments
    from .models import Attachment
    for f in files:
        Attachment.objects.create(
            message=msg, file=f, filename=f.name,
            content_type=f.content_type or '', size_bytes=f.size,
        )
    channel.save()  # bump updated_at
    return Response(MessageSerializer(msg, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def push_subscribe(request):
    """Register a push subscription."""
    endpoint = request.data.get('endpoint')
    p256dh = request.data.get('p256dh_key', '')
    auth = request.data.get('auth_key', '')
    if not endpoint:
        return Response({'error': 'endpoint required'}, status=status.HTTP_400_BAD_REQUEST)
    sub, created = PushSubscription.objects.get_or_create(
        user=request.user, endpoint=endpoint,
        defaults={'p256dh_key': p256dh, 'auth_key': auth}
    )
    return Response({'subscribed': True, 'created': created})


@api_view(['POST'])
@permission_classes([IsStaffOrAbove])
def push_unsubscribe(request):
    """Remove a push subscription."""
    endpoint = request.data.get('endpoint')
    if not endpoint:
        return Response({'error': 'endpoint required'}, status=status.HTTP_400_BAD_REQUEST)
    PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return Response({'unsubscribed': True})
