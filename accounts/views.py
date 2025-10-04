from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.middleware.csrf import get_token
from .serializers import UserSerializer
from .models import ConnectionRequest
from .validators import validate_password_strength
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.core.mail import send_mail
from urllib.parse import urlencode
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session authentication that skips CSRF enforcement (for specific views)."""
    def enforce_csrf(self, request):
        return

User = get_user_model()

def send_verification_email(user):
    """Send email verification to user"""
    try:
        signer = TimestampSigner()
        token = signer.sign(str(user.pk))
        
        # Build verification URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        verify_url = f"{frontend_url}/verify-email?token={token}"
        
        subject = 'Verify your HoriZonix account'
        message = f"""
        Hi {user.first_name},
        
        Welcome to HoriZonix! Please verify your email address by clicking the link below:
        
        {verify_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        The HoriZonix Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"Verification email sent to {user.email}")
    except Exception as e:
        print(f"Failed to send verification email: {e}")

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
    try:
        print(f"Profile update request from: {request.META.get('HTTP_ORIGIN', 'No origin')}")
        print(f"Profile update data: {request.data}")
        print(f"Profile update files: {request.FILES}")
        print(f"User: {request.user}")
        
        user = request.user
        # Handle simple JSON fields via serializer
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            print("Serializer validation passed")
        else:
            print(f"Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Handle optional image files
        profile_picture = request.FILES.get('profile_picture')
        if profile_picture and profile_picture.size > 0:
            print(f"Updating profile picture: {profile_picture}")
            user.profile_picture = profile_picture
            user.save(update_fields=['profile_picture'])
            print("Profile picture updated successfully")
            
        cover_photo = request.FILES.get('cover_photo')
        if cover_photo and cover_photo.size > 0:
            print(f"Updating cover photo: {cover_photo}")
            user.cover_photo = cover_photo
            user.save(update_fields=['cover_photo'])
            print("Cover photo updated successfully")

        return Response(UserSerializer(user, context={'request': request}).data)
    except Exception as e:
        print(f"Profile update error: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Profile update failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        # Auto-verify email for direct signup (no email confirmation)
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        
        # TODO: Uncomment when you want email verification
        # # Send email verification
        # try:
        #     send_verification_email(user)
        # except Exception as email_error:
        #     print(f"Email sending failed: {email_error}")
        #     # Don't fail registration if email fails, but log it
        #     pass
        
    except Exception as e:
        print(f"Register error: {e}")  # Debug log
        return Response({'error': f'Registration failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'message': 'Registration successful. You can now sign in.',
        'user': UserSerializer(user).data
    }, status=status.HTTP_201_CREATED)


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

    # TODO: Uncomment when you want email verification
    # # Check if email is verified
    # if not user.is_email_verified:
    #     return Response({
    #         'error': 'Please verify your email address before logging in.',
    #         'email_verified': False
    #     }, status=status.HTTP_400_BAD_REQUEST)

    login(request, user)
    return Response({
        'message': 'Logged in successfully.',
        'user': UserSerializer(user, context={'request': request}).data
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([CsrfExemptSessionAuthentication])
@csrf_exempt
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out successfully.'})


@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):
    if not request.user.is_authenticated:
        return Response({'user': None})
    return Response({'user': UserSerializer(request.user, context={'request': request}).data})


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf(request):
    # Return CSRF token in JSON so frontend can use it cross-site
    token = get_token(request)
    return Response({'csrftoken': token, 'detail': 'CSRF cookie set'})


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint to test connection"""
    return Response({
        'status': 'ok',
        'message': 'Backend is running',
        'timestamp': request.META.get('HTTP_DATE', 'unknown'),
        'origin': request.META.get('HTTP_ORIGIN', 'unknown')
    })


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


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """Resend verification email"""
    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        if user.is_email_verified:
            return Response({'error': 'Email is already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        send_verification_email(user)
        return Response({'message': 'Verification email sent'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)