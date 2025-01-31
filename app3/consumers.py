import base64
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Room, Message, UserProfile
from django.contrib.auth.models import User
from urllib.parse import parse_qs
from django.db.models import Q
from django.utils.timezone import now

def find_room(user1, user2):
    """
    Find the chat room between two users.
    Ensures that the room is returned regardless of user order.
    """
    # Ensure user1 is always the first user and user2 is the second user
    if user1.id > user2.id:
        user1, user2 = user2, user1

    # Find the room where user1 and user2 are in the same room
    room = Room.objects.filter(
        Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
    ).first()

    return room


def decode_text(encoded_text):
    """Decodes the given Base64 encoded text."""
    decoded_text = base64.b64decode(encoded_text.encode('utf-8'))
    return decoded_text.decode('utf-8')  # Convert bytes to string

class ChatConsumer(WebsocketConsumer):
    """
    WebSocket consumer for managing user connections, sending and receiving messages.
    Handles user list updates and messaging between users.
    """

    def connect(self):
        """
        Handle WebSocket connection.
        Retrieves the user ID from query parameters and subscribes to the group.
        """
        query_string = self.scope["query_string"].decode("utf-8")
        query_params = parse_qs(query_string)
        self.user_id = query_params.get("user_id", [None])[0]
        self.room_group_name = f"user_list_for_{self.user_id}"

        if self.user_id:
            # Add user to the group
            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            self.accept()
            self.update_user_list()

    def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        Currently does nothing but can be extended for cleanup.
        """
        pass

    def receive(self, text_data):
        """
        Handle receiving messages from the WebSocket.
        This method processes actions like updating the user list.
        """
        data = json.loads(text_data)
        if data.get("action") == "update_user_list":
            self.update_user_list()

    def update_user_list(self, event=None):
        """
        Update and send the list of users, ordered by recent chat time.
        Each user’s last message is included with the timestamp.
        """
        recent_users = User.objects.exclude(is_superuser=True).distinct()
        receive_user = User.objects.filter(id=self.user_id).first()

        user_list = []
        for user in recent_users:
            # Find the chat room between the current user and the receiver
            room = find_room(receive_user, user)
            
            # If a room exists, get the last message
            if room:
                last_msg = Message.objects.filter(room=room).last()
                if last_msg:
                    formatted_time = last_msg.timestamp.isoformat()  # ISO format for timestamp
                    user_list.append({
                        "username": user.username,
                        "text": decode_text(last_msg.text),
                        "time": formatted_time
                    })

        # Sort the user list by message timestamp in descending order
        user_list = sorted(user_list, key=lambda x: x['time'], reverse=True)
        print(user_list)
        # Send the updated user list to the frontend
        self.send(text_data=json.dumps({"users": user_list}))
