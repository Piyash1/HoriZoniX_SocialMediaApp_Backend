from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ConnectionRequest

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.ReadOnlyField()
    following_count = serializers.ReadOnlyField()
    is_following = serializers.SerializerMethodField()
    is_connected = serializers.SerializerMethodField()
    has_pending_request = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    cover_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile_picture', 'cover_photo', 'profile_picture_url', 'cover_photo_url',
            'bio', 'location', 'followers_count', 'following_count', 'is_email_verified',
            'is_following', 'is_connected', 'has_pending_request', 'is_private', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']

    def get_is_following(self, obj):
        """Check if current user follows this user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False

    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            url = obj.profile_picture.url
            
            # If it's already a full URL (Cloudinary), return as is
            if url.startswith('http'):
                return url
            
            # Otherwise, build absolute URI (for local development)
            return request.build_absolute_uri(url) if request else url
        return None

    def get_is_connected(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.connections.filter(id=obj.id).exists()
        return False

    def get_has_pending_request(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ConnectionRequest.objects.filter(
                sender=request.user, receiver=obj, status=ConnectionRequest.Status.PENDING
            ).exists() or ConnectionRequest.objects.filter(
                sender=obj, receiver=request.user, status=ConnectionRequest.Status.PENDING
            ).exists()
        return False

    def get_cover_photo_url(self, obj):
        if obj.cover_photo:
            request = self.context.get('request')
            url = obj.cover_photo.url
            
            # If it's already a full URL (Cloudinary), return as is
            if url.startswith('http'):
                return url
            
            # Otherwise, build absolute URI (for local development)
            return request.build_absolute_uri(url) if request else url
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile serializer"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile_picture', 'bio', 'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']