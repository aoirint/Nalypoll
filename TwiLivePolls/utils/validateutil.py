import re

TWEET_ID_OR_URL_PATTERN = re.compile(
    r'^((?P<id>\d+)|https://(mobile\.)?twitter\.com/(?P<user>[^/]+)/status/(?P<id_in_url>\d+))$'
)
