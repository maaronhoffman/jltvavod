from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config
from app.models import db, User
import os
from datetime import datetime

def time_to_12hour(time_str):
    try:
        time_obj = datetime.strptime(time_str, '%H:%M')
        return time_obj.strftime('%I:%M %p').lstrip('0')
    except ValueError:
        return time_str

def format_air_time(air_time):
    parts = air_time.split()
    if len(parts) >= 5:
        day = parts[0] + 's'
        et_time = time_to_12hour(parts[1])
        pt_time = time_to_12hour(parts[4])
        
        if et_time == pt_time:
            return f"{day}|{et_time} ET/PT"
        else:
            return f"{day}|{et_time} ET / {pt_time} PT"
    return air_time



def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config.from_object(Config)
    app.jinja_env.filters['time_to_12hour'] = time_to_12hour
    app.jinja_env.filters['format_air_time'] = format_air_time  
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main, admin, auth
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(auth.bp)

    return app

app=create_app()