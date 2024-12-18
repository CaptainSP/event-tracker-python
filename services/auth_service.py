import requests
import jwt
from flask import current_app as app,session
from datetime import datetime, timedelta

class AuthService:
    def __init__(self, pg_conn):
        self.pg_conn = pg_conn
    
    def sign_in(self):
        params = {
            'client_id': app.config['MAIL_CLIENT_ID'],
            'response_type': 'code',
            'redirect_uri': app.config['MAIL_REDIRECT_URI'],
            'response_mode': 'query',
            'scope': app.config['MAIL_SCOPE']
        }
        authorize_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        # redirect to authorize_url
        
        return { 'url': f"{authorize_url}?{requests.compat.urlencode(params)}" }

    def callback(self, code):
        try:
            token_response = requests.post(
                app.config['TOKEN_URL'],
                data={
                    'client_id': app.config['MAIL_CLIENT_ID'],
                    'client_secret': app.config['MAIL_CLIENT_SECRET'],
                    'code': code,
                    'redirect_uri': app.config['MAIL_REDIRECT_URI'],
                    'grant_type': 'authorization_code'
                },
                headers={ 'Content-Type': 'application/x-www-form-urlencoded' }
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            jwt_token, user = self.complete_login(tokens['access_token'])
            return jwt_token, user, tokens['access_token']
        except requests.RequestException as e:
            app.logger.error(f"Error during token exchange: {e}")
            return { 'error': 'Failed to perform token exchange' }

    def fetch_email_of_user(self, access_token):
        try:
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={ 'Authorization': f'Bearer {access_token}' }
            )
            response.raise_for_status()
            return response.json().get('mail')
        except requests.RequestException as e:
            app.logger.error(f"Error fetching user email: {e}")
            raise e

    def complete_login(self, access_token):
        email = self.fetch_email_of_user(access_token)
        user = self.find_or_create_user(email, access_token)
        return self.create_jwt_by_user(user), user

    def find_or_create_user(self, email, access_token):
        # Implement your database logic to find or create user here
        user = self.find_user_by_email(email)
        if not user:
            user = self.create_user(email, access_token)
        else:
            user['access_token'] = access_token
            # Update user in database
        return user

    def find_user_by_email(self, email):
        # Implement database search logic
        cursor = self.pg_conn.cursor()
        cursor.execute('SELECT * FROM "user" WHERE "email" = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        print(user)
        if user:
            return { 'id': user[0], 'email': user[1], 'access_token': user[2] }
        return None

    def create_user(self, email, access_token):
        # Implement user creation logic with database
        cursor = self.pg_conn.cursor()
        cursor.execute('INSERT INTO "user" (email, access_token) VALUES (%s, %s)', (email, access_token))
        self.pg_conn.commit()
        cursor.close()
        cursor = self.pg_conn.cursor()
        cursor.execute('SELECT * FROM "user" WHERE "email" = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        
        return { 'id': user[0], 'email': user[1], 'access_token': user[2] }

    def create_jwt_by_user(self, user):
        payload = {
            'sub': user['id'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(weeks=4) # Token expires in 4 weeks
        }
        
        token = jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')
        # Ensure proper string formatting for compatibility
        return token if isinstance(token, str) else token.decode('utf-8')
    def decode_jwt(self, token):
        try:
            return jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return { 'error': 'Token has expired' }
        except jwt.InvalidTokenError:
            return { 'error': 'Invalid token' }
        except jwt.JWTError as e:
            return { 'error': f'Error decoding token: {e}' }