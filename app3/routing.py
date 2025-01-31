from django.urls import path, re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
   path('ws/chat/', ChatConsumer.as_asgi()),
]