import hashlib
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import base64

def hash_text(text):
    """Encodes the given text into Base64."""
    encoded_text = base64.b64encode(text.encode('utf-8'))
    return encoded_text.decode('utf-8')  # Convert bytes to string


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to="profile_images", null=True, blank=True)
    is_online = models.BooleanField(default=False)
    room_name = models.CharField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.room_name:
            self.room_name = f"{self.user.username}_{get_random_string(8)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile of {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically creates a UserProfile for each new User."""
    if created:
        UserProfile.objects.create(user=instance)

class Room(models.Model):
    name = models.CharField(max_length=255, blank=True)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.user2.username[:2]}_{self.user1.username[:3]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Room {self.name}"

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    reciver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reciver')
    text = models.TextField(editable=False)  # Stored as a hash
    original_text = models.TextField(null=True, blank=True)  # Optional for debugging or admin use
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.text:
            if not self.original_text:
                raise ValidationError("Original text must be provided.")
            self.text = hash_text(self.original_text)
        super().save(*args, **kwargs)
        self.send_updateuser_list()

    def send_updateuser_list(self):
        """Send an update to the WebSocket group of the recipient."""
        channel_layer = get_channel_layer()
        group_name = f"user_list_for_{self.reciver.id}"

        # Send a message to the group to update the user list
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "update_user_list",
            }
        )

    def __str__(self):
        return f"Message from {self.sender.username} in Room {self.room.id} at {self.timestamp}"


