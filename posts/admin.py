from django.contrib import admin
from .models import Post, PostImage, Like, Comment, Share, Story


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    fields = ("image",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "is_pinned", "created_at")
    search_fields = ("content",)
    list_filter = ("is_pinned", "created_at")
    fields = ("author", "content", "is_pinned")
    inlines = [PostImageInline]
    list_editable = ("is_pinned",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("post__id", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "short_text", "created_at")
    list_filter = ("created_at",)
    search_fields = ("text", "user__username")

    def short_text(self, obj):
        return (obj.text or "")[:50]
    short_text.short_description = "Text"


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("post__id", "user__username")


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "media_type", "created_at")
    list_filter = ("media_type", "created_at")
    search_fields = ("user__email", "user__username", "content")
