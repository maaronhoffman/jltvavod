import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///site.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback_secret_key')
    UPLOAD_FOLDER = 'app/static/uploads'
