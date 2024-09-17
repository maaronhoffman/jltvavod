from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType
import uuid

db = SQLAlchemy()


custom_row_shows = db.Table('custom_row_shows',
    db.Column('custom_row_id', db.String(36), db.ForeignKey('custom_row.id'), primary_key=True),
    db.Column('show_id', db.Integer, db.ForeignKey('show.id'), primary_key=True)
)

class CustomRow(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    shows = db.relationship('Show', secondary=custom_row_shows, backref='custom_rows')
    show_order = db.Column(MutableList.as_mutable(PickleType), default=[])
    order = db.Column(db.Integer, nullable=False, default=0)
    row_type = db.Column(db.String(20), default='poster')  # 'poster' or 'card'
    custom_text = db.Column(db.Text)  # For the customizable text blob
    show_custom_text = db.Column(db.JSON, default={})

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    

class Show(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    poster_url = db.Column(db.String(200), nullable=False)
    logo_url = db.Column(db.String(200))
    banner_poster_url = db.Column(db.String(200)) 
    air_time = db.Column(db.String(50)) 
    seasons = db.relationship('Season', backref='show', lazy=True)
    theme_color = db.Column(db.String(7))
    card_image_url = db.Column(db.String(200))
    
class Season(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    episodes = db.relationship('Episode', backref='season', cascade='all, delete-orphan')


class Episode(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.Integer) 
    url = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.String(200), nullable=True)
    keywords = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    thumbnail_url = db.Column(db.String(200), nullable=True)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)





