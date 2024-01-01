from flask import render_template, url_for, redirect, flash, request
from werkzeug.utils import secure_filename
import os

from app import app, db
from app.forms import LoginForm, RegistrationForm, ArtistForm, CanvasForm
from app.models import User, Canvas, Artist, Comment, CanvasVote, CommentVote
from flask_login import login_user, logout_user, current_user, login_required

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
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.root_path, 'static/canvas_images', filename)
            image_file.save(filepath)
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
    return render_template('canvas_detail.html', canvas=canvas)

@app.route('/upload_canvas', methods=['POST'])
def upload_canvas():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']

@app.route('/add_comment/<int:canvas_id>', methods=['POST'])
def add_comment(canvas_id):
    # Assume 'comment' is the name of the form field for the comment content
    comment_content = request.form.get('comment')
    new_comment = Comment(content=comment_content, user_id=current_user.id, canvas_id=canvas_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=canvas_id))

@app.route('/vote_canvas/<int:canvas_id>/<int:vote>', methods=['POST'])
@login_required
def vote_canvas(canvas_id, vote):
    canvas_vote = CanvasVote.query.filter_by(user_id=current_user.id, canvas_id=canvas_id).first()
    
    if canvas_vote:
        canvas_vote.vote = vote
    else:
        new_vote = CanvasVote(user_id=current_user.id, canvas_id=canvas_id, vote=vote)
        db.session.add(new_vote)
    
    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=canvas_id))

@app.route('/vote_comment/<int:comment_id>/<int:vote>', methods=['POST'])
@login_required
def vote_comment(comment_id, vote):
    comment_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    
    if comment_vote:
        comment_vote.vote = vote
    else:
        new_vote = CommentVote(user_id=current_user.id, comment_id=comment_id, vote=vote)
        db.session.add(new_vote)
    
    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=Comment.query.get(comment_id).canvas_id))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))
