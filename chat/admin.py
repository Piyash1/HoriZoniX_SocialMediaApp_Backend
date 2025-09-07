from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'message_type', 'created_at')
    list_filter = ('message_type', 'created_at')
    search_fields = ('sender__email', 'sender__username', 'receiver__email', 'receiver__username', 'text')
