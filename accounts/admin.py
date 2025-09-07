from django.contrib import admin
from .models import User, ConnectionRequest


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name',
        'is_email_verified', 'is_private', 'created_at'
    )
    list_filter = ('is_email_verified', 'is_private', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'bio', 'location')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('followers', 'connections')


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = (
        'sender__email', 'sender__username', 'sender__first_name', 'sender__last_name',
        'receiver__email', 'receiver__username', 'receiver__first_name', 'receiver__last_name',
    )
    raw_id_fields = ('sender', 'receiver')
    readonly_fields = ('created_at', 'updated_at')

