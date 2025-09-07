from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Social media specific fields
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following', blank=True)
    # Mutual connections (e.g., friends)
    connections = models.ManyToManyField('self', symmetrical=True, blank=True)
    is_private = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    cover_photo = models.ImageField(upload_to='covers/', blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    @property
    def following_count(self):
        return self.following.count()


class ConnectionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        CANCELED = 'canceled', 'Canceled'

    sender = models.ForeignKey(User, related_name='sent_connection_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_connection_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender_id} -> {self.receiver_id} ({self.status})"