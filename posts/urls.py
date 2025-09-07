from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_create_posts, name='post-list-create'),
    path('<int:pk>/', views.retrieve_update_delete_post, name='post-detail'),
    path('<int:pk>/like/', views.toggle_like, name='post-like'),
    path('<int:pk>/comments/', views.list_create_comments, name='post-comments'),
    path('<int:pk>/share/', views.create_share, name='post-share'),
    # Stories
    path('stories/', views.list_stories, name='story-list'),
    path('stories/create/', views.create_story, name='story-create'),
]
