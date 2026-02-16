from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from .models import Channel, ChannelMember, Message, MessageAttachment


def _serialize_channel(ch):
    return {
        'id': ch.id,
        'name': ch.name,
        'channel_type': ch.channel_type,
        'member_count': ch.member_count,
        'created_at': ch.created_at.isoformat(),
    }


def _serialize_message(msg):
    return {
        'id': msg.id,
        'channel_id': msg.channel_id,
        'sender_id': msg.sender_id,
        'sender_name': msg.sender.get_full_name() or msg.sender.username,
        'body': msg.body,
        'attachments': [
            {
                'id': att.id,
                'filename': att.filename,
                'content_type': att.content_type,
                'url': att.url,
            }
            for att in msg.attachments.all()
        ],
        'created_at': msg.created_at.isoformat(),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_channels(request):
    """GET /api/comms/channels/ — list channels the user belongs to (or all for staff)."""
    tenant = getattr(request, 'tenant', None)
    channels = Channel.objects.filter(tenant=tenant)
    # Auto-join user to General channel if not already a member
    general = channels.filter(channel_type='GENERAL').first()
    if general and not general.members.filter(user=request.user).exists():
        ChannelMember.objects.create(channel=general, user=request.user)
    return Response([_serialize_channel(ch) for ch in channels])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_messages(request, channel_id):
    """GET /api/comms/channels/<id>/messages/ — list messages in a channel."""
    try:
        tenant = getattr(request, 'tenant', None)
        channel = Channel.objects.get(id=channel_id, tenant=tenant)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)

    limit = int(request.query_params.get('limit', 100))
    msgs = channel.messages.select_related('sender').prefetch_related('attachments').order_by('-created_at')[:limit]
    return Response([_serialize_message(m) for m in reversed(msgs)])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_message(request, channel_id):
    """POST /api/comms/channels/<id>/messages/create/ — send a message."""
    try:
        tenant = getattr(request, 'tenant', None)
        channel = Channel.objects.get(id=channel_id, tenant=tenant)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)

    body = request.data.get('body', '')
    files = request.FILES.getlist('files')

    if not body.strip() and not files:
        return Response({'error': 'Message body or files required'}, status=status.HTTP_400_BAD_REQUEST)

    msg = Message.objects.create(channel=channel, sender=request.user, body=body)

    for f in files:
        MessageAttachment.objects.create(
            message=msg,
            file=f,
            filename=f.name,
            content_type=f.content_type or '',
        )

    return Response(_serialize_message(msg), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ensure_general_channel(request):
    """POST /api/comms/ensure-general/ — create the General channel if it doesn't exist."""
    tenant = getattr(request, 'tenant', None)
    ch, created = Channel.objects.get_or_create(
        tenant=tenant, channel_type='GENERAL',
        defaults={'name': 'General'},
    )
    if not ch.members.filter(user=request.user).exists():
        ChannelMember.objects.create(channel=ch, user=request.user)
    return Response(_serialize_channel(ch))
