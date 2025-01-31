from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message, Room
from .consumers import UserListConsumer

@receiver(post_save, sender=Message)
def notify_user_list_update(sender, instance, **kwargs):
    # Get the room where the message was sent
    room = instance.room
    channel_layer = get_channel_layer()

    # Fetch the updated user list for both users in the room
    for user in [room.user1, room.user2]:
        # Use the custom get_user_list function
        user_list = UserListConsumer.get_user_list(user)

        # Send the updated user list to the WebSocket group of the user
        async_to_sync(channel_layer.group_send)(
            f"chat_user_list_{user.id}",
            {
                "type": "send_user_list",
                "users": user_list,
            }
        )
