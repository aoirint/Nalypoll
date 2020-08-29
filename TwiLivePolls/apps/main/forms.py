from django.core.exceptions import ValidationError
from django.core import validators
from django import forms
from urllib.parse import urlparse

from validateutil import TWEET_ID_OR_URL_PATTERN

validator = validators.RegexValidator(
    regex=TWEET_ID_OR_URL_PATTERN,
    message='Invalid value',
    code='invalid'
)

class TweetIdOrUrlField(forms.CharField):
    default_validators = [ validator, ]

class RegisterForm(forms.Form):
    tweet_id_or_url = TweetIdOrUrlField(
        label='Tweet ID or URL',
        max_length=255,
        widget=forms.widgets.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tweet ID or URL'
        }),
    )
