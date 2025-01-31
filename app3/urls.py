from django.urls import path
from .views import *

urlpatterns = [
    path('', login_view, name="login"),
    path('home/', home, name="home"),
    path('logout/', logout, name="logout"),
    
    path('test/api/', hello_world, name="hello_world")
]
