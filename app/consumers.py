import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message
from datetime import datetime,time

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']

        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "message": message,
            "username": username,
        }))




class UserListConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.send_user_list()  # Send the user list when the WebSocket connects

    def send_user_list(self):
        current_user = self.scope["user"]
        # print(current_user)
        if not current_user.is_authenticated:
            self.close()  # Close the connection if the user is not authenticated
            return

        users = User.objects.exclude(id=current_user.id)
        user_details = []
        chat_data = []
        nonchat_data = []
        for user_ in users:
            # Fetch or create the room
            room = Room.objects.filter(
                Q(user1=current_user, user2=user_) | Q(user2=current_user, user1=user_)
            ).first()
            if not room:
                room = Room.objects.create(user1=current_user, user2=user_)

            # Fetch the last message
            last_message = Message.objects.filter(room=room).last()
            last_chat_time = last_message.timestamp.time() if last_message else None
            last_chat_message = last_message.content if last_message else None
            if last_chat_time:
                chat_data.append(
                                {
                            "id": user_.id,
                            "username": user_.username,
                            "first_name": user_.first_name,
                            "last_name": user_.last_name,
                            "email": user_.email,
                            "room_id": room.id,
                            "last_message": last_chat_message,
                            "last_chat_time": last_chat_time.isoformat() if last_chat_time else None,
                        })
            else:
                chat_data.append(
                                {
                            "id": user_.id,
                            "username": user_.username,
                            "first_name": user_.first_name,
                            "last_name": user_.last_name,
                            "email": user_.email,
                            "room_id": room.id,
                            "last_message": last_chat_message,
                            "last_chat_time": last_chat_time.isoformat() if last_chat_time else None,
                        })
        sorted_chat_data = sorted(chat_data, key=lambda x: x["last_chat_time"] or "", reverse=True)
        user_details = sorted_chat_data + nonchat_data
        
        self.send(text_data=json.dumps({"type": "user_list", "users": user_details}))

    
    @staticmethod
    def get_user_list(user):
        # Fetch users excluding the current user
        users = User.objects.exclude(id=user.id)
        user_details = []
        chat_data = []
        nonchat_data = []

        for user_ in users:
            # Fetch or create the room
            room = Room.objects.filter(
                Q(user1=user, user2=user_) | Q(user2=user, user1=user_)
            ).first()
            if not room:
                room = Room.objects.create(user1=user, user2=user_)

            # Fetch the last message
            last_message = Message.objects.filter(room=room).last()
            last_chat_time = last_message.timestamp.time() if last_message else None

            if last_chat_time:
                chat_data.append(
                                {
                            "id": user_.id,
                            "username": user_.username,
                            "first_name": user_.first_name,
                            "last_name": user_.last_name,
                            "email": user_.email,
                            "room_id": room.id,
                            "last_chat_time": last_chat_time,
                        })
            else:
                chat_data.append(
                                {
                            "id": user_.id,
                            "username": user_.username,
                            "first_name": user_.first_name,
                            "last_name": user_.last_name,
                            "email": user_.email,
                            "room_id": room.id,
                            "last_chat_time": last_chat_time
                        })
        sorted_chat_data = sorted(chat_data, key=lambda x: x["last_chat_time"] or "", reverse=True)
        user_details = sorted_chat_data + nonchat_data

        return user_details


# class ChatListConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope["user"]
#         print(self.user)
#         self.group_name = f"chat_user_list_{self.user.id}"

#         # Join the group for this user
#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name,
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave the group for this user
#         await self.channel_layer.group_discard(
#             self.group_name,
#             self.channel_name,
#         )

#     async def send_user_list(self, event):
#         users = event["users"]

#         # Send the user list to the WebSocket client
#         await self.send(text_data=json.dumps({
#             "type": "user_list",
#             "users": users,
#         }))

#     @staticmethod
#     def get_user_list(self, user):
#         # Fetch the user list for the provided user
#         # Customize this logic as per your requirements
#         user_list = []
#         for profile in UserProfileRoom.objects.filter(online=True).exclude(user=user):
#             user_list.append({
#                 "username": profile.user.username,
#                 "online": profile.online,
#                 "last_chat_time": Message.objects.filter(
#                     sender=profile.user
#                 ).order_by("-timestamp").first().timestamp if Message.objects.filter(sender=profile.user).exists() else None,
#                 "room_id": Room.objects.filter(
#                     user1=profile.user
#                 ).first().id if Room.objects.filter(user1=profile.user).exists() else None,
#             })
#         return user_list

