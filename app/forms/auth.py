from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """Formulaire de connexion"""
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(1, 80)])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember_me = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')

class RegistrationForm(FlaskForm):
    """Formulaire d'inscription"""
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(1, 80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 120)])
    first_name = StringField('Prénom', validators=[DataRequired(), Length(1, 50)])
    last_name = StringField('Nom', validators=[DataRequired(), Length(1, 50)])
    phone = StringField('Téléphone', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField('Confirmer le mot de passe', 
                             validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà utilisé.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé.')
