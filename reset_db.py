import os
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    # Create all tables
    db.create_all()

    # Create a default user
    username = 'admin'
    password = 'password'  # Change this to a secure password
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    print(f"Created default user with username: {username} and password: {password}")
    print("Database has been reset.")
