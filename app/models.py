from app import db
from flask_login import UserMixin
from . import login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    stitch_lists = db.relationship('StitchList', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    canvas_votes = db.relationship('CanvasVote', backref='user', lazy='dynamic')
    comment_votes = db.relationship('CommentVote', backref='user', lazy='dynamic')


class Canvas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    image_url = db.Column(db.String(250))  # URL to the image of the canvas
    stitch_lists = db.relationship('StitchList', backref='canvas', lazy='dynamic')
    comments = db.relationship('Comment', backref='canvas', lazy='dynamic')
    canvas_votes = db.relationship('CanvasVote', backref='canvas', lazy='dynamic')

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    canvases = db.relationship('Canvas', backref='artist', lazy='dynamic')

class StitchList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvas.id'))
    status = db.Column(db.String(50))  # e.g., 'Completed', 'In Progress', 'Want to Stitch'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvas.id'), nullable=False)
    comment_votes = db.relationship('CommentVote', backref='comment', lazy='dynamic')

class CanvasVote(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvas.id'), primary_key=True)
    vote = db.Column(db.Integer)  # -1, 0, or 1 for downvote, no vote, or upvote

class CommentVote(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), primary_key=True)
    vote = db.Column(db.Integer)  # -1, 0, or 1 for downvote, no vote, or upvote

    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))