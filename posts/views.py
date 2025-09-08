from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Post, PostImage, Like, Comment, Share, Story
from .serializers import PostSerializer, CommentSerializer, StorySerializer
from rest_framework.parsers import MultiPartParser, FormParser


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def list_create_posts(request):
    if request.method == 'GET':
        posts = Post.objects.select_related('author').prefetch_related('images', 'likes', 'comments', 'shares').order_by('-created_at')
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    # POST - create
    print(f"POST request from: {request.META.get('HTTP_ORIGIN', 'No origin')}")
    print(f"POST request headers: {dict(request.headers)}")
    print(f"POST request data: {request.data}")
    print(f"POST request files: {request.FILES}")
    
    content = request.data.get('content', '')
    post = Post.objects.create(author=request.user, content=content)
    # accept multiple files under 'images'
    files = request.FILES.getlist('images')
    for f in files:
        PostImage.objects.create(post=post, image=f)
    return Response(PostSerializer(post, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def retrieve_update_delete_post(request, pk: int):
    try:
        post = Post.objects.select_related('author').get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(PostSerializer(post, context={'request': request}).data)

    if request.method == 'PUT':
        if post.author_id != request.user.id:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        content = request.data.get('content', post.content)
        post.content = content
        post.save(update_fields=['content', 'updated_at'])
        # Optional: replace images if new files provided
        files = request.FILES.getlist('images')
        if files:
            post.images.all().delete()
            for f in files:
                PostImage.objects.create(post=post, image=f)
        return Response(PostSerializer(post, context={'request': request}).data)

    # DELETE
    if post.author_id != request.user.id:
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
    post.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, pk: int):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return Response({'liked': liked, 'likes_count': post.likes.count()})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def list_create_comments(request, pk: int):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        comments = post.comments.select_related('user').order_by('created_at')
        return Response(CommentSerializer(comments, many=True, context={'request': request}).data)

    text = (request.data.get('text') or '').strip()
    if not text:
        return Response({'error': 'Text is required'}, status=status.HTTP_400_BAD_REQUEST)
    comment = Comment.objects.create(post=post, user=request.user, text=text)
    return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_share(request, pk: int):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    Share.objects.create(post=post, user=request.user)
    return Response({'shared': True, 'shares_count': post.shares.count()})


# -------- Stories --------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_stories(request):
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(hours=24)
    me = request.user
    # Show my own stories, plus stories from people I follow, my followers, and my connections
    user_ids = {me.id}
    user_ids.update(me.following.values_list('id', flat=True))
    user_ids.update(me.followers.values_list('id', flat=True))
    user_ids.update(me.connections.values_list('id', flat=True))
    stories = (
        Story.objects
        .filter(user_id__in=list(user_ids), created_at__gte=cutoff)
        .select_related('user')
        .order_by('-created_at')
    )
    return Response(StorySerializer(stories, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_story(request):
    """Create a story with robust media type detection.
    - If a file is uploaded, infer media_type from content_type (image/video)
    - If no file, treat as text story and require non-empty content
    """
    content = request.data.get('content', '')
    background_color = request.data.get('background_color', '#4f46e5')
    media_file = request.FILES.get('media')

    if media_file:
        ct = (getattr(media_file, 'content_type', '') or '').lower()
        if not ct:
            import mimetypes
            guessed, _ = mimetypes.guess_type(getattr(media_file, 'name', ''))
            ct = (guessed or '').lower()
        if ct.startswith('image'):
            media_type = Story.MediaType.IMAGE
        elif ct.startswith('video'):
            media_type = Story.MediaType.VIDEO
        else:
            return Response({'error': 'Unsupported media type'}, status=status.HTTP_400_BAD_REQUEST)
        story = Story(user=request.user, content=content or '', background_color=background_color, media_type=media_type)
        story.media = media_file
        story.save()
    else:
        # Text story
        if not content.strip():
            return Response({'error': 'Content required for text story'}, status=status.HTTP_400_BAD_REQUEST)
        story = Story(user=request.user, content=content.strip(), background_color=background_color, media_type=Story.MediaType.TEXT)
        story.save()

    return Response(StorySerializer(story, context={'request': request}).data, status=status.HTTP_201_CREATED)
