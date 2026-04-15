from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email
from app.models.client import Client

class ClientForm(FlaskForm):
    """Formulaire de création/modification de client"""
    first_name = StringField('Prénom', validators=[DataRequired(), Length(1, 50)])
    last_name = StringField('Nom', validators=[DataRequired(), Length(1, 50)])
    phone = StringField('Téléphone', validators=[DataRequired(), Length(1, 20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(1, 120)])
    address = TextAreaField('Adresse', validators=[Optional(), Length(max=500)])
    activity = StringField('Activité', validators=[DataRequired(), Length(1, 100)])
    id_card_number = StringField('Numéro pièce d\'identité', validators=[Optional(), Length(1, 50)])
    id_card_type = SelectField('Type pièce d\'identité', 
                              choices=[('CNI', 'CNI'), ('Passeport', 'Passeport'), 
                                      ('Permis', 'Permis de conduire'), ('Autre', 'Autre')],
                              validators=[Optional()])
    birth_date = DateField('Date de naissance', validators=[Optional()])
    gender = SelectField('Sexe', 
                        choices=[('M', 'Masculin'), ('F', 'Féminin')],
                        validators=[Optional()])
    marital_status = SelectField('Situation matrimoniale',
                                choices=[('Célibataire', 'Célibataire'), 
                                        ('Marié(e)', 'Marié(e)'),
                                        ('Divorcé(e)', 'Divorcé(e)'),
                                        ('Veuf(ve)', 'Veuf(ve)')],
                                validators=[Optional()])
    number_of_children = IntegerField('Nombre d\'enfants', 
                                     validators=[Optional(), NumberRange(min=0, max=20)])
    monthly_income = DecimalField('Revenu mensuel', places=2,
                                 validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Enregistrer')
    
    def __init__(self, original_phone=None, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.original_phone = original_phone
    
    def validate_phone(self, phone):
        if phone.data != self.original_phone:
            client = Client.query.filter_by(phone=phone.data).first()
            if client:
                raise ValidationError('Ce numéro de téléphone est déjà utilisé.')

class ClientSearchForm(FlaskForm):
    """Formulaire de recherche de client"""
    query = StringField('Recherche', validators=[DataRequired()])
    submit = SubmitField('Rechercher')
