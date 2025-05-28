from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField, IntegerField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional
from flask_wtf.file import FileAllowed
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class CreateRoomForm(FlaskForm):
    name = StringField('Room Name', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Room name must be between 3 and 50 characters')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=200, message='Description cannot be longer than 200 characters')
    ])
    submit = SubmitField('Create Room')

class TaskCreationForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Task Description', validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1)])
    week_number = IntegerField('Week Number', validators=[DataRequired(), NumberRange(min=1, max=52)])
    year = IntegerField('Year', validators=[DataRequired()])
    submit = SubmitField('Create Task')

class TaskSubmissionForm(FlaskForm):
    proof_text = TextAreaField('Proof of Completion')
    proof_file = FileField('Upload Proof (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'pdf', 'doc', 'docx'], 'Images and documents only!')
    ])
    submit = SubmitField('Submit Task') 