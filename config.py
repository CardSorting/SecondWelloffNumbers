import os
import secrets

class Config:
    SHOPIFY_CLIENT_ID = os.environ.get('SHOPIFY_CLIENT_ID')
    SHOPIFY_CLIENT_SECRET = os.environ.get('SHOPIFY_CLIENT_SECRET')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', secrets.token_bytes(32))
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(16))

config = Config()