from flask import render_template, url_for, redirect, flash, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, ArtistForm, CanvasForm
from app.models import User, Canvas, Artist
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
    if form.validate_on_submit():
        # Handle file upload here if 'image' field is used
        new_canvas = Canvas(title=form.title.data, description=form.description.data)
        # Set artist_id and image_url for the new canvas
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

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))
