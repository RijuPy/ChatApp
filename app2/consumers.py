import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message, UserProfileRoom
from datetime import datetime,time

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope['url_route']['kwargs']['room_name']
#         self.room_group_name = f"chat_{self.room_name}"

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']
#         username = data['username']

#         # Broadcast message to room group
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat_message",
#                 "message": message,
#                 "username": username,
#             }
#         )

#     async def chat_message(self, event):
#         message = event['message']
#         username = event['username']

#         # Send message to WebSocket
#         await self.send(text_data=json.dumps({
#             "message": message,
#             "username": username,
#         }))

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

from urllib.parse import parse_qs
from asgiref.sync import async_to_sync

class UserListConsumer(WebsocketConsumer):
    def connect(self):
        query_params = parse_qs(self.scope['query_string'].decode())
        self.user_id = query_params.get('user_id', [None])[0]
        self.room_group_name = f"{self.user_id}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()
        self.user_online()  # Update user online status
        self.send_user_list()  # Send the user list when the WebSocket connects

    def disconnect(self, close_code):
        self.user_offline()  # Update user offline status
        print(f"Disconnected: {self.scope['user']}")  # Optional logging

    def send_user_list(self):
        current_user = User.objects.get(id=self.user_id)
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
            last_chat_time = last_message.timestamp if last_message else None
            last_chat_message = last_message.content if last_message else None
            online_status_ins = UserProfileRoom.objects.filter(user=user_)
            online_status = "Offline"
            if online_status_ins.exists():
                if online_status_ins.first().online:
                    online_status = "Online"

            

            if last_chat_time:
                chat_data.append(
                    {
                        "id": user_.id,
                        "username": user_.username,
                        "first_name": user_.first_name,
                        "last_name": user_.last_name,
                        "online_status": online_status,
                        "email": user_.email,
                        "room_id": room.id,
                        "last_message":last_chat_message,
                        "last_chat_time": last_chat_time,
                    }
                )
            else:
                nonchat_data.append(
                    {
                        "id": user_.id,
                        "username": user_.username,
                        "first_name": user_.first_name,
                        "last_name": user_.last_name,
                        "email": user_.email,
                        "online_status": online_status,
                        "room_id": room.id,
                        "last_message":last_chat_message,
                        "last_chat_time": last_chat_time,
                    }
                )
        sorted_chat_data = sorted(chat_data, key=lambda x: x["last_chat_time"] or "", reverse=True)
        for i in sorted_chat_data:
            i["last_chat_time"] = str(i["last_chat_time"])
        user_details = sorted_chat_data + nonchat_data

        self.send(text_data=json.dumps({"type": "user_list", "users": user_details}))

    def user_online(self):
        try:
            user = User.objects.get(id=self.user_id)
            user_profile_room, created = UserProfileRoom.objects.get_or_create(user=user)
            user_profile_room.online = True
            user_profile_room.save()
            return True
        except Exception as e:
            print(f"Error in user_online: {e}")
            return False

    def user_offline(self):
        try:
            user = User.objects.get(id=self.user_id)
            user_profile_room, created = UserProfileRoom.objects.get_or_create(user=user)
            user_profile_room.online = False
            user_profile_room.save()
            return True
        except Exception as e:
            print(f"Error in user_offline: {e}")
            return False

    @staticmethod
    def get_user_list(user):
        users = User.objects.exclude(id=user.id)
        user_details = []
        chat_data = []
        nonchat_data = []

        for user_ in users:
            room = Room.objects.filter(
                Q(user1=user, user2=user_) | Q(user2=user, user1=user_)
            ).first()
            if not room:
                room = Room.objects.create(user1=user, user2=user_)

            last_message = Message.objects.filter(room=room).last()
            last_chat_time = last_message.timestamp if last_message else None
            online_status_ins = UserProfileRoom.objects.filter(user=user_)
            online_status = "Offline"
            if online_status_ins.exists():
                if online_status_ins.first().online:
                    online_status = "Online"

            

            if last_chat_time:
                chat_data.append(
                    {
                        "id": user_.id,
                        "username": user_.username,
                        "first_name": user_.first_name,
                        "last_name": user_.last_name,
                        "online_status": online_status,
                        "email": user_.email,
                        "room_id": room.id,
                        "last_chat_time": last_chat_time,
                    }
                )
            else:
                nonchat_data.append(
                    {
                        "id": user_.id,
                        "username": user_.username,
                        "first_name": user_.first_name,
                        "last_name": user_.last_name,
                        "email": user_.email,
                        "online_status": online_status,
                        "room_id": room.id,
                        "last_chat_time": last_chat_time,
                    }
                )
        # print(chat_data)
        sorted_chat_data = sorted(chat_data, key=lambda x: x["last_chat_time"] or "", reverse=True)
        for i in sorted_chat_data:
            i["last_chat_time"] = str(i["last_chat_time"])
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

