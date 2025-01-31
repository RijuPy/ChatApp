from django.contrib.auth.models import User
from django.db import models
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync


class Room(models.Model):
    user1 = models.ForeignKey(User, related_name='room_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='room_user2', on_delete=models.CASCADE)

    def __str__(self):
        return f"Room between {self.user1.username} and {self.user2.username}"

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    # def save(self, *args, **kwargs):
    #     is_new = self._state.adding
    #     super(Message, self).save(*args, **kwargs)
    #     self.send_notification()

    # def send_notification(self):
    #     from .consumers import UserListConsumer
    #     channel_layer = get_channel_layer()
        
    #     if self.sender.id:
    #         group_name = f"{self.sender.id}"
    #         async_to_sync(channel_layer.group_send)(
    #         group_name,
    #          {
    #              "type":"user_list",
    #              "users": UserListConsumer.get_user_list(self.sender)
    #          } 
    #     )
    #     else:
    #         pass
        
        


class UserProfileRoom(models.Model):
    room_name = models.CharField(max_length=100, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    online = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Generate a unique room name if it is not already set
        if not self.room_name:
            self.room_name = f"room_{self.user.username}_{self.pk or ''}"
        
        # Call the parent save method to ensure `pk` is available
        super().save(*args, **kwargs)

        # Re-generate room_name with the primary key if needed
        if not self.room_name.endswith(str(self.pk)):
            self.room_name = f"room_{self.user.username}_{self.pk}"
            super().save(update_fields=['room_name'])

    def __str__(self):
        return f"{self.user.username} {self.online}"

