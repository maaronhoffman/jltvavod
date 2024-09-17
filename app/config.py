import os


class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SECRET_KEY = 'your_secret_key_here'  # Change this to a random secret key
    UPLOAD_FOLDER = 'app/static/uploads'
