from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class PaymentForm(FlaskForm):
    """Formulaire d'enregistrement de paiement"""
    amount = DecimalField('Montant', places=2, validators=[DataRequired(), NumberRange(min=100)])
    payment_method = SelectField('Méthode de paiement',
                                choices=[('cash', 'Espèces'), 
                                        ('mobile_money', 'Mobile Money'), 
                                        ('bank_transfer', 'Virement bancaire')],
                                validators=[DataRequired()])
    payment_date = DateField('Date de paiement', validators=[Optional()])
    reference_number = StringField('Numéro de référence', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Enregistrer le paiement')
