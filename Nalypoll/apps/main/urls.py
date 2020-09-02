"""Nalypoll URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include, re_path

from main import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('poll/<int:tweet_id>', views.poll, name='poll'),
    path('poll/remove/<int:tweet_id>', views.remove_poll, name='remove_poll'),
    # path('update/<int:tweet_id>', views.update, name='update'),
    path('me', views.me, name='me'),
    path('menu', views.menu, name='menu'),
    path('menu/remove_user_polls', views.remove_user_polls, name='remove_user_polls'),
    path('oauth', views.oauth, name='oauth'),
    path('oauth/callback', views.oauth_callback, name='oauth_callback'),
    path('oauth/remove', views.oauth_remove, name='oauth_remove'),
    path('oauth/logout', views.oauth_logout, name='oauth_logout'),
]
