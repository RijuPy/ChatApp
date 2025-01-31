from django.urls import path
from .views import *

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("chat/", chat_view, name="chat"),
    path("chat/<int:room_id>/", chat_room, name="chat_room"),
    path("save_message/", save_message, name="save_message")
]
