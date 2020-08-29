from django.shortcuts import render
from django.conf import settings
import requests

# Create your views here.
def index(request):
    return render(request, 'index.html', {
    })

def view(request, tweet_id):
    return render(request, 'view.html', {
        'tweet_id': tweet_id,
    })
