from rest_framework import serializers
from .models import Post, PostImage, Like, Comment, Share, Story
from django.contrib.auth import get_user_model


class AuthorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'full_name']

    def get_full_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return name or obj.username

    def get_profile_picture(self, obj):
        pic = getattr(obj, 'profile_picture', None)
        if not pic:
            return None
        try:
            url = pic.url
        except Exception:
            return None
        
        # If it's already a full URL (Cloudinary), return as is
        if url.startswith('http'):
            return url
        
        # Otherwise, build absolute URI (for local development)
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class StorySerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'user', 'content', 'media_type', 'media_url', 'background_color',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_media_url(self, obj):
        if not obj.media:
            return None
        url = obj.media.url
        
        # If it's already a full URL (Cloudinary), return as is
        if url.startswith('http'):
            return url
        
        # Otherwise, build absolute URI (for local development)
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class PostImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        fields = ['id', 'url']

    def get_url(self, obj):
        url = obj.image.url
        
        # If it's already a full URL (Cloudinary), return as is
        if url.startswith('http'):
            return url
        
        # Otherwise, build absolute URI (for local development)
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class PostSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(source='author', read_only=True)
    image_urls = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    shares_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'image_urls', 'is_pinned',
            'likes_count', 'comments_count', 'shares_count', 'liked_by_me',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_image_urls(self, obj):
        images = obj.images.all()
        return [PostImageSerializer(img, context=self.context).data['url'] for img in images]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_shares_count(self, obj):
        return obj.shares.count()

    def get_liked_by_me(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        return obj.likes.filter(user=request.user).exists()


class CommentSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'text', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
