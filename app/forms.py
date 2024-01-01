from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ArtistForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    bio = TextAreaField('Biography')
    submit = SubmitField('Submit Artist')

class CanvasForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    artist_id = SelectField('Artist', coerce=int)
    image = FileField('Canvas Image')  # Assuming you handle image uploads
    submit = SubmitField('Submit Canvas')