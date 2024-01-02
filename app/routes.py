from flask import render_template, url_for, redirect, flash, request
from werkzeug.utils import secure_filename
import os, uuid, random

from app import app, db
from app.forms import LoginForm, RegistrationForm, ArtistForm, CanvasForm
from app.models import User, Canvas, Artist, Comment, CanvasVote, CommentVote
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import generate_csrf

@app.route('/')
def index():
    all_canvases = Canvas.query.all()
    featured_canvases = random.sample(all_canvases, min(len(all_canvases), 4))  # Select 7 random canvases
    return render_template('index.html', featured_canvases=featured_canvases)

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

@app.route('/delete_canvas/<int:canvas_id>', methods=['POST'])
@login_required
def delete_canvas(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)

    # Check if current user is the artist who created the canvas or an admin
    if canvas.artist.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this canvas.', 'danger')
        return redirect(url_for('canvas_detail', canvas_id=canvas_id))

    # Proceed with deletion
    db.session.delete(canvas)
    db.session.commit()
    flash('Canvas has been deleted', 'success')
    return redirect(url_for('canvases'))

@app.route('/edit_canvas/<int:canvas_id>', methods=['GET', 'POST'])
@login_required
def edit_canvas(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)

    # Check if current user is the artist who created the canvas or an admin
    if canvas.artist.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this canvas.', 'danger')
        return redirect(url_for('canvas_detail', canvas_id=canvas_id))

    form = CanvasForm(obj=canvas)
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
            canvas.image_url = filepath
        else:
            filepath = None

        canvas.title = form.title.data
        canvas.description = form.description.data
        canvas.artist_id = form.artist_id.data

        db.session.commit()
        return redirect(url_for('canvas_detail', canvas_id=canvas_id))

    return render_template('edit_canvas.html', form=form, canvas=canvas)


@app.route('/canvases')
def canvases():
    all_canvases = Canvas.query.all()
    csrf_token = generate_csrf()
    return render_template('canvases.html', canvases=all_canvases, csrf_token=csrf_token)

@app.route('/canvas/<int:canvas_id>')
def canvas_detail(canvas_id):
    canvas = Canvas.query.get_or_404(canvas_id)
    csrf_token = generate_csrf()

    canvas_vote_total = sum(vote.vote for vote in canvas.canvas_votes)
    comment_vote_totals = {comment.id: sum(vote.vote for vote in comment.comment_votes) for comment in canvas.comments}

    user_canvas_vote = None
    user_comment_votes = {}

    if current_user.is_authenticated:
        user_canvas_vote = CanvasVote.query.filter_by(user_id=current_user.id, canvas_id=canvas_id).first()
        user_comment_votes = {comment.id: CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment.id).first() for comment in canvas.comments}

    return render_template('canvas_detail.html', 
                           canvas=canvas, 
                           csrf_token=csrf_token, 
                           canvas_vote_total=canvas_vote_total, 
                           comment_vote_totals=comment_vote_totals,
                           user_canvas_vote=user_canvas_vote,
                           user_comment_votes=user_comment_votes)



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
        new_vote = 1 if vote == 'up' else -1
        canvas_vote = CanvasVote(user_id=current_user.id, canvas_id=canvas_id, vote=new_vote)
        db.session.add(canvas_vote)
    else:
        # User has already voted
        if (vote == 'up' and canvas_vote.vote == 1) or (vote == 'down' and canvas_vote.vote == -1):
            # Remove vote
            canvas_vote.vote = 0
        else:
            # Change vote
            canvas_vote.vote = 1 if vote == 'up' else -1

    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=canvas_id))


@app.route('/vote_comment/<int:comment_id>/<vote>', methods=['POST'])
@login_required
def vote_comment(comment_id, vote):
    comment_vote = CommentVote.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    comment = Comment.query.get_or_404(comment_id)

    if not comment_vote:
        # User hasn't voted yet, create a new vote
        new_vote = 1 if vote == 'up' else -1
        comment_vote = CommentVote(user_id=current_user.id, comment_id=comment_id, vote=new_vote)
        db.session.add(comment_vote)
    else:
        # User has already voted
        if (vote == 'up' and comment_vote.vote == 1) or (vote == 'down' and comment_vote.vote == -1):
            # Remove vote
            comment_vote.vote = 0
        else:
            # Change vote
            comment_vote.vote = 1 if vote == 'up' else -1

    db.session.commit()
    return redirect(url_for('canvas_detail', canvas_id=comment.canvas_id))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))
