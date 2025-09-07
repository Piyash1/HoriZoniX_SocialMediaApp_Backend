from django.urls import path
from . import views

urlpatterns = [
    path('<int:user_id>/', views.list_messages, name='list-messages'),
    path('<int:user_id>/send/', views.send_message, name='send-message'),
    path('recent/', views.list_recent_threads, name='list-recent-threads'),
]
