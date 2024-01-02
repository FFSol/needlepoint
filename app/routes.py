from flask import render_template, url_for, redirect, flash, request
from werkzeug.utils import secure_filename
import os
import uuid

from app import app, db
from app.forms import LoginForm, RegistrationForm, ArtistForm, CanvasForm
from app.models import User, Canvas, Artist, Comment, CanvasVote, CommentVote
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import generate_csrf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/artists')
def artists():
    all_artists = Artist.query.all()
    return render_template('artists.html', artists=all_artists)

@app.route('/artist/<int:artist_id>')
def artist_detail(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    return render_template('artist_detail.html', artist=artist)

@app.route('/add_artist', methods=['GET', 'POST'])
def add_artist():
    form = ArtistForm()
    if form.validate_on_submit():
        new_artist = Artist(name=form.name.data, bio=form.bio.data)
        db.session.add(new_artist)
        db.session.commit()
        return redirect(url_for('artists'))
    return render_template('add_artist.html', form=form)

@app.route('/add_canvas', methods=['GET', 'POST'])
def add_canvas():
    form = CanvasForm()
    artists = Artist.query.all()

    if not artists:
        flash('No artists available. Please add an artist first.')
        return redirect(url_for('add_artist'))
    
    form.artist_id.choices = [(artist.id, artist.name) for artist in artists]

    if form.validate_on_submit():
        # Handle image file
        if form.image.data:
            image_file = form.image.data
            # Generate a random UUID filename
            ext = os.path.splitext(image_file.filename)[1]
            filename = str(uuid.uuid4()) + ext
            save_path = os.path.join(app.root_path, 'static/canvas_images', filename)
            image_file.save(save_path)

            # Use a relative path for the URL
            filepath = url_for('static', filename='canvas_images/' + filename)
        else:
            filepath = None

        new_canvas = Canvas(
            title=form.title.data,
            description=form.description.data,
            image_url=filepath,  # assuming you handle image uploads
            artist_id=form.artist_id.data  # Set the artist_id
        )

        # Add more fields as necessary, like artist_id
        db.session.add(new_canvas)
        db.session.commit()
        return redirect(url_for('canvases'))
    return render_template('add_canvas.html', form=form)

@app.route('/canvases')
def canvases():
    all_canvases = Canvas.query.all()
    return render_template('canvases.html', canvases=all_canvases)

@app.route('/canvas/<int:canvas_id>')
def canvas_detail(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    csrf_token = generate_csrf()
    
    # Calculate canvas votes
    canvas_vote_total = sum(vote.vote for vote in canvas.canvas_votes)

    # Calculate comment votes
    comment_vote_totals = {comment.id: sum(vote.vote for vote in comment.comment_votes) for comment in canvas.comments}

    return render_template('canvas_detail.html', canvas=canvas, csrf_token=csrf_token, canvas_vote_total=canvas_vote_total, comment_vote_totals=comment_vote_totals)

@app.route('/add_comment/<int:canvas_id>', methods=['POST'])
@login_required
def add_comment(canvas_id):
    # Assume 'comment' is the name of the form field for the comment content
    comment_content = request.form.get('comment')
    new_comment = Comment(content=comment_content, user_id=current_user.id, canvas_id=canvas_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=canvas_id))

@app.route('/vote_canvas/<int:canvas_id>/<vote>', methods=['POST'])
@login_required
def vote_canvas(canvas_id, vote):
    canvas_vote = CanvasVote.query.filter_by(user_id=current_user.id, canvas_id=canvas_id).first()

    if not canvas_vote:
        # User hasn't voted yet, create a new vote
        if vote == 'up':
            new_vote = 1
        elif vote == 'down':
            new_vote = -1
        else:
            return redirect(url_for('canvas_detail', canvas_id=canvas_id))  # Invalid vote

        canvas_vote = CanvasVote(user_id=current_user.id, canvas_id=canvas_id, vote=new_vote)
        db.session.add(canvas_vote)
    else:
        # User has already voted, update their vote
        if (vote == 'up' and canvas_vote.vote < 1) or (vote == 'down' and canvas_vote.vote > -1):
            canvas_vote.vote = 0 if canvas_vote.vote == (1 if vote == 'up' else -1) else (1 if vote == 'up' else -1)

    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=canvas_id))

@app.route('/vote_comment/<int:comment_id>/<vote>', methods=['POST'])
@login_required
def vote_comment(comment_id, vote):
    comment_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    comment = Comment.query.get_or_404(comment_id)

    if not comment_vote:
        # User hasn't voted yet, create a new vote
        if vote == 'up':
            new_vote = 1
        elif vote == 'down':
            new_vote = -1
        else:
            return redirect(url_for('canvas_detail', canvas_id=comment.canvas_id))  # Invalid vote

        comment_vote = CommentVote(user_id=current_user.id, comment_id=comment_id, vote=new_vote)
        db.session.add(comment_vote)
    else:
        # User has already voted, update their vote
        if (vote == 'up' and comment_vote.vote < 1) or (vote == 'down' and comment_vote.vote > -1):
            comment_vote.vote = 0 if comment_vote.vote == (1 if vote == 'up' else -1) else (1 if vote == 'up' else -1)

    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=comment.canvas_id))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))
