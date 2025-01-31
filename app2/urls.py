from django.urls import path
from .views import *

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("chat/", chat_view, name="chat"),
    path("chat/<int:room_id>/", chat_room, name="chat_room"),
    path("chat/history/<int:room_name>/", chat_history, name="chat_history"),
    path("chat/save_message/", save_message, name="save_message"),
]
