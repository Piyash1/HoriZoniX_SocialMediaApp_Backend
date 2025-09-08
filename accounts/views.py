from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from .serializers import UserSerializer
from .models import ConnectionRequest
from .validators import validate_password_strength
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from urllib.parse import urlencode
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile_by_id(request, user_id: int):
    """Get another user's profile by id"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_user_profile(request):
    """Update current user profile. Accepts JSON or multipart for image uploads."""
    user = request.user
    # Handle simple JSON fields via serializer
    serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Handle optional image files
    profile_picture = request.FILES.get('profile_picture')
    if profile_picture:
        user.profile_picture = profile_picture
        user.save(update_fields=['profile_picture'])
    cover_photo = request.FILES.get('cover_photo')
    if cover_photo:
        user.cover_photo = cover_photo
        user.save(update_fields=['cover_photo'])

    return Response(UserSerializer(user, context={'request': request}).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    """Follow/unfollow a user"""
    try:
        target_user = User.objects.get(id=user_id)
        
        if request.user.following.filter(id=user_id).exists():
            request.user.following.remove(target_user)
            action = 'unfollowed'
        else:
            request.user.following.add(target_user)
            action = 'followed'
            
        return Response({
            'message': f'Successfully {action} {target_user.username}',
            'action': action
        })
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_connection_request(request, user_id: int):
    """Send a connection request to another user."""
    if request.user.id == user_id:
        return Response({'error': 'Cannot connect with yourself'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        receiver = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # If already connected
    if request.user.connections.filter(id=receiver.id).exists():
        return Response({'message': 'Already connected', 'status': 'accepted'})

    cr, created = ConnectionRequest.objects.get_or_create(
        sender=request.user, receiver=receiver,
        defaults={'status': ConnectionRequest.Status.PENDING}
    )
    if not created and cr.status == ConnectionRequest.Status.PENDING:
        return Response({'message': 'Request already pending', 'status': 'pending'})
    elif not created:
        # If previously rejected/canceled, reset to pending
        cr.status = ConnectionRequest.Status.PENDING
        cr.save(update_fields=['status'])
    return Response({'message': 'Connection request sent', 'status': 'pending'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_connection_request(request, request_id: int):
    """Accept or reject a connection request. Body: { action: 'accept'|'reject' }"""
    action = (request.data.get('action') or '').strip().lower()
    if action not in ('accept', 'reject'):
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cr = ConnectionRequest.objects.get(id=request_id, receiver=request.user)
    except ConnectionRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if action == 'accept':
        cr.status = ConnectionRequest.Status.ACCEPTED
        cr.save(update_fields=['status'])
        # Create mutual connection
        request.user.connections.add(cr.sender)
        return Response({'message': 'Connection accepted', 'status': 'accepted'})
    else:
        cr.status = ConnectionRequest.Status.REJECTED
        cr.save(update_fields=['status'])
        return Response({'message': 'Connection rejected', 'status': 'rejected'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_connection_request(request, user_id: int):
    """Cancel a pending connection request that current user sent."""
    try:
        cr = ConnectionRequest.objects.get(sender=request.user, receiver_id=user_id, status=ConnectionRequest.Status.PENDING)
    except ConnectionRequest.DoesNotExist:
        return Response({'error': 'Pending request not found'}, status=status.HTTP_404_NOT_FOUND)
    cr.status = ConnectionRequest.Status.CANCELED
    cr.save(update_fields=['status'])
    return Response({'message': 'Connection request canceled', 'status': 'canceled'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_connection_requests(request):
    """List pending connection requests for current user (received)."""
    pending = ConnectionRequest.objects.filter(receiver=request.user, status=ConnectionRequest.Status.PENDING)
    data = [
        {
            'id': cr.id,
            'sender': UserSerializer(cr.sender, context={'request': request}).data,
            'created_at': cr.created_at,
        }
        for cr in pending
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_followers(request, user_id=None):
    """Get followers list"""
    user = request.user if user_id is None else User.objects.get(id=user_id)
    followers = user.followers.all()
    serializer = UserSerializer(followers, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request, user_id=None):
    """Get following list"""
    user = request.user if user_id is None else User.objects.get(id=user_id)
    following = user.following.all()
    serializer = UserSerializer(following, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_connections(request, user_id=None):
    """Get connections list (mutual connections)."""
    user = request.user if user_id is None else User.objects.get(id=user_id)
    connections = user.connections.all()
    serializer = UserSerializer(connections, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """Search users by name, username, bio, or location (excludes self)."""
    query = request.query_params.get('q', '').strip()
    if not query:
        return Response([], status=status.HTTP_200_OK)

    qs = User.objects.filter(
        Q(username__icontains=query)
        | Q(first_name__icontains=query)
        | Q(last_name__icontains=query)
        | Q(bio__icontains=query)
        | Q(location__icontains=query)
    ).exclude(id=request.user.id)[:50]

    serializer = UserSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


# ---------- Django auth endpoints (session-based) ----------

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        email = request.data.get('email', '').strip().lower()
        username = request.data.get('username') or email
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password strength
        password_validation = validate_password_strength(password)
        if not password_validation['valid']:
            return Response({
                'error': 'Password does not meet requirements.',
                'password_errors': password_validation['errors']
            }, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        # Auto-verify email for now
        user.is_email_verified = True
        user.save()
    except Exception as e:
        print(f"Register error: {e}")  # Debug log
        return Response({'error': f'Registration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # Send verification email
    try:
        signer = TimestampSigner()
        token = signer.sign(user.pk)
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        send_mail(
            'Verify your HoriZonix email',
            f'Click to verify your email: {verify_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,  # Don't fail silently in production
        )
        print(f"Verification email sent to {user.email}")
    except Exception as e:
        print(f"Email sending failed: {e}")
        # In production, you might want to log this to a proper logging service
        # For now, we'll continue with registration even if email fails

    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password')
    if not email or not password:
        return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # ModelBackend expects 'username' param even if USERNAME_FIELD is 'email'
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

    if not user.is_email_verified:
        return Response({'error': 'Email not verified. Please check your inbox.'}, status=status.HTTP_403_FORBIDDEN)

    login(request, user)
    print(f"Login successful for user: {user.email}")
    print(f"Session key: {request.session.session_key}")
    print(f"User authenticated: {request.user.is_authenticated}")
    
    # Ensure session is saved
    request.session.save()
    
    response = Response({
        'message': 'Logged in successfully.',
        'user': UserSerializer(user).data
    })
    
    # Set session cookie explicitly
    response.set_cookie(
        'sessionid',
        request.session.session_key,
        max_age=86400,  # 24 hours
        httponly=True,
        samesite='None',
        secure=False
    )
    
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token
        return Response({
            'access': str(access_token),
            'refresh': str(refresh)
        })
    except Exception as e:
        return Response({'error': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out successfully.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    print(f"Me endpoint - User authenticated: {request.user.is_authenticated}")
    print(f"Session key: {request.session.session_key}")
    print(f"User: {request.user}")
    if not request.user.is_authenticated:
        return Response({'user': None})
    return Response({'user': UserSerializer(request.user, context={'request': request}).data})


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    return Response({'detail': 'CSRF cookie set'})


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Missing token'}, status=status.HTTP_400_BAD_REQUEST)
    signer = TimestampSigner()
    try:
        user_pk = signer.unsign(token, max_age=60 * 60 * 24)  # 24 hours
        user = User.objects.get(pk=user_pk)
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        return Response({'message': 'Email verified'})
    except SignatureExpired:
        return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
    except (BadSignature, User.DoesNotExist):
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)