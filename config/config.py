import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///clima.db')
    PORT = int(os.environ.get('PORT', 8080))
