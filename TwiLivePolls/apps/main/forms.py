from django.core.exceptions import ValidationError
from django.core import validators
from django import forms
from urllib.parse import urlparse

from validateutil import TWEET_ID_OR_URL_PATTERN

validate_tweet_id_or_url = validators.RegexValidator(
    regex=TWEET_ID_OR_URL_PATTERN,
    message='Invalid value',
    code='invalid'
)

class TweetIdOrUrlField(forms.CharField):
    default_validators = [ validate_tweet_id_or_url, ]

class RegisterForm(forms.Form):
    tweet_id_or_url = TweetIdOrUrlField(
        label='Tweet ID or URL',
        max_length=255,
        widget=forms.widgets.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tweet ID or URL (https://twitter.com/USER/status/TWEET_ID)',
            'pattern': r'^((\d+)|https://(mobile\.)?twitter\.com/([^/]+)/status/(\d+))$',
            # 'pattern': TWEET_ID_OR_URL_PATTERN.pattern,
        }),
    )
