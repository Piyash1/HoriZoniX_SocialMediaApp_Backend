from django.urls import path
from . import views

urlpatterns = [
    # Django auth endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('refresh/', views.refresh_token_view, name='refresh-token'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me, name='me'),
    path('csrf/', views.csrf, name='csrf'),
    path('verify-email/', views.verify_email, name='verify-email'),

    path('profile/', views.get_user_profile, name='user-profile'),
    path('profile/<int:user_id>/', views.get_user_profile_by_id, name='user-profile-by-id'),
    path('profile/update/', views.update_user_profile, name='update-profile'),
    path('follow/<int:user_id>/', views.follow_user, name='follow-user'),
    path('followers/', views.get_followers, name='get-followers'),
    path('followers/<int:user_id>/', views.get_followers, name='get-user-followers'),
    path('following/', views.get_following, name='get-following'),
    path('following/<int:user_id>/', views.get_following, name='get-user-following'),
    path('connections/', views.get_connections, name='get-connections'),
    path('connections/<int:user_id>/', views.get_connections, name='get-user-connections'),
    path('search/', views.search_users, name='search-users'),
    # Connections
    path('connections/requests/', views.list_connection_requests, name='list-connection-requests'),
    path('connections/request/<int:user_id>/', views.send_connection_request, name='send-connection-request'),
    path('connections/respond/<int:request_id>/', views.respond_connection_request, name='respond-connection-request'),
    path('connections/cancel/<int:user_id>/', views.cancel_connection_request, name='cancel-connection-request'),
]