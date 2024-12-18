from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Config:
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    MAIL_CLIENT_ID = os.getenv('MAIL_CLIENT_ID')
    MAIL_CLIENT_SECRET = os.getenv('MAIL_CLIENT_SECRET')
    MAIL_REDIRECT_URI = os.getenv('MAIL_REDIRECT_URI')
    MAIL_SCOPE = os.getenv('MAIL_SCOPE')
    TOKEN_URL = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    GRAPH_API_URL = 'https://graph.microsoft.com/v1.0/'
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    JWT_SECRET = os.getenv('JWT_SECRET')
    REDIS_URL = os.getenv('REDIS_URL')

# Handle missing configuration
if not all((Config.MAIL_CLIENT_ID, Config.MAIL_CLIENT_SECRET, Config.MAIL_REDIRECT_URI, Config.MAIL_SCOPE, Config.REDIS_URL, Config.GOOGLE_API_KEY)):
    raise RuntimeError("Missing one or more configuration variables. Please check the .env file.")