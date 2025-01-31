from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .data_genaretor import create_fake_users
from .models import Room, Message, User
import json


def logout_view(request):
    logout(request)
    return redirect(reverse("login"))


def login_view(request):
    if request.user.is_authenticated:
        return redirect(reverse("chat"))

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse("chat"))
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


@login_required
def chat_view(request):
    return render(request, "chat.html")


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    receiver_user = room.user2 if room.user1 == request.user else room.user1
    print(receiver_user)
    messages = Message.objects.filter(room=room)
    return render(request, "chat_room.html", {"room_name": room_id, "messages": messages, "receiver_user": receiver_user})


@csrf_exempt
@login_required
def save_message(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message")
            room_name = data.get("room_name")
            room = get_object_or_404(Room, id=int(room_name))
            Message.objects.create(room=room, sender=request.user, content=message)
            return JsonResponse({"status": "success", "message": "Message saved successfully."})
        except (ValueError, Room.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Invalid room ID."}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)


"""
@login_required
def get_or_create_room(user1, user2):
    room = Room.objects.filter(
        Q(users=user1) & Q(users=user2)
    ).first()
    if not room:
        room = Room.objects.create()
        room.users.add(user1, user2)
    return room

@login_required
def get_messages(request, room_id):
    messages = Message.objects.filter(room_id=room_id).order_by("timestamp")
    data = {
        "messages": [
            {
                "sender": message.sender.username,
                "content": message.content,
                "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for message in messages
        ]
    }
    return JsonResponse(data)

@csrf_exempt
@login_required
def send_message(request):
    print("call")
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        content = request.POST.get('content')
        room = get_object_or_404(Room, id=room_id)
        message = Message.objects.create(room=room, sender=request.user, content=content)
        return JsonResponse({'status': 'Message sent'})

"""