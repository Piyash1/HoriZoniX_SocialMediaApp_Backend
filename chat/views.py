from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Message


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_messages(request, user_id: int):
    """List messages between current user and another user (most recent first)."""
    User = get_user_model()
    try:
        other = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    qs = Message.objects.filter(
        sender=request.user, receiver=other
    ).union(
        Message.objects.filter(sender=other, receiver=request.user)
    ).order_by('created_at')
    data = [
        {
            'id': m.id,
            'from_user': {'id': m.sender_id},
            'to_user': {'id': m.receiver_id},
            'text': m.text,
            'message_type': m.message_type,
            'media_url': (request.build_absolute_uri(m.media.url) if m.media else None),
            'created_at': m.created_at,
        }
        for m in qs
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_message(request, user_id: int):
    """Send a text or image message to a user."""
    User = get_user_model()
    try:
        other = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    text = (request.data.get('text') or '').strip()
    file = request.FILES.get('image')

    if not text and not file:
        return Response({'error': 'Provide text or image'}, status=status.HTTP_400_BAD_REQUEST)

    msg = Message(sender=request.user, receiver=other)
    if file:
        msg.message_type = Message.MessageType.IMAGE
        msg.media = file
    else:
        msg.message_type = Message.MessageType.TEXT
        msg.text = text
    msg.save()

    return Response({
        'id': msg.id,
        'from_user': {'id': msg.sender_id},
        'to_user': {'id': msg.receiver_id},
        'text': msg.text,
        'message_type': msg.message_type,
        'media_url': (request.build_absolute_uri(msg.media.url) if msg.media else None),
        'created_at': msg.created_at,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_recent_threads(request):
    """Return latest message per counterpart for current user (most recent first)."""
    user = request.user
    qs = (
        Message.objects
        .filter(Q(sender=user) | Q(receiver=user))
        .select_related('sender', 'receiver')
        .order_by('-created_at')
    )
    threads = {}
    results = []

    def file_url(f):
        if not f:
            return None
        try:
            url = f.url
        except Exception:
            return None
        return request.build_absolute_uri(url)

    for m in qs[:200]:
        counterpart = m.receiver if m.sender_id == user.id else m.sender
        if counterpart.id in threads:
            continue
        threads[counterpart.id] = True
        results.append({
            'counterpart': {
                'id': counterpart.id,
                'username': counterpart.username,
                'first_name': getattr(counterpart, 'first_name', ''),
                'last_name': getattr(counterpart, 'last_name', ''),
                'profile_picture': file_url(getattr(counterpart, 'profile_picture', None)),
            },
            'text': m.text,
            'message_type': m.message_type,
            'media_url': file_url(getattr(m, 'media', None)),
            'created_at': m.created_at,
        })
        if len(results) >= 10:
            break

    return Response(results)
