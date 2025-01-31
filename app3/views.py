from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from app3.data_genaretor import create_fake_users
from django.contrib.auth.models import User
# from .models import Room, Message, User
import json


def logout_view(request):
    logout(request)
    return redirect(reverse("login"))


def login_view(request):
    # create_fake_users(20)
    if request.user.is_authenticated:
        return redirect(reverse("home"))

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse("home"))
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")

@login_required
def home(request):
    return render(request, 'side/home.html')


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # Override permissions for this view
def hello_world(request):
    if request.method == 'POST':
        return Response({"message": "Got some data!", "data": request.data})
    return Response({"message": "Hello, world!"})

