
import requests

class TokenAPI:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def new_token(self):
        url = 'https://api.twitter.com/oauth2/token'
        params = {
            'grant_type': 'client_credentials',
        }

        auth = ( self.api_key, self.api_secret )

        r = requests.post(url, params=params, auth=auth)
        if r.status_code != 200:
            raise Exception(r.text)

        data = r.json()
        token_type = data['token_type']
        assert token_type == 'bearer', 'Invalid token_type: %s' % token_type

        access_token = data['access_token']
        return access_token

    def revoke_token(self, access_token):
        url = 'https://api.twitter.com/oauth2/invalidate_token'
        params = {
            'access_token': access_token,
        }

        auth = ( self.api_key, self.api_secret )

        r = requests.post(url, params=params, auth=auth)
        if r.status_code != 200:
            raise Exception(r.text)

        data = r.json()
        revoked_token = data['access_token']

        assert revoked_token == access_token

        return revoked_token

if __name__ == '__main__':
    import os
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('type', type=str, choices=[ 'new', 'revoke', ])
    args = parser.parse_args()

    api_key = os.environ.get('API_KEY')
    api_secret = os.environ.get('API_SECRET')

    if not api_key:
        api_key = input('API Key: ')
    if not api_secret:
        api_secret = input('API Secret: ')

    api = TokenAPI(api_key=api_key, api_secret=api_secret)

    if args.type == 'new':
        token = api.new_token()
        print('New Access Token: %s' % token)

    elif args.type == 'revoke':
        token = os.environ.get('ACCESS_TOKEN')
        if not token:
            token = input('Token to revoke: ')

        revoked_token = api.revoke_token(access_token=token)
        print('Revoked Token: %s' % revoked_token)
