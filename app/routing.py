from django.urls import path, re_path
from .consumers import ChatConsumer, UserListConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r"ws/chat_user_list/$", UserListConsumer.as_asgi()),
]
