from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional
from app.models.loan import LoanType, RepaymentFrequency

class LoanForm(FlaskForm):
    """Formulaire de création de prêt"""
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Montant du prêt', places=2, validators=[DataRequired(), NumberRange(min=1000)])
    interest_rate = DecimalField('Taux d\'intérêt (%)', places=2, validators=[DataRequired(), NumberRange(min=0, max=100)])
    duration_months = IntegerField('Durée (mois)', validators=[DataRequired(), NumberRange(min=1, max=60)])
    loan_type = SelectField('Type de prêt', 
                           choices=[(LoanType.CASH.value, 'Prêt en espèces'), 
                                   (LoanType.INPUTS.value, 'Prêt en intrants')],
                           validators=[DataRequired()])
    repayment_frequency = SelectField('Fréquence de remboursement',
                                     choices=[('daily', 'Journalier'), 
                                             ('weekly', 'Hebdomadaire'), 
                                             ('monthly', 'Mensuel')],
                                     validators=[DataRequired()])
    input_value = DecimalField('Valeur des intrants', places=2,
                              validators=[Optional(), NumberRange(min=0)])
    purpose = TextAreaField('Objet du prêt', validators=[Optional(), Length(max=500)])
    first_payment_date = DateField('Date première échéance', validators=[Optional()])
    submit = SubmitField('Créer le prêt')
    
    def validate_input_value(self, input_value):
        if self.loan_type.data == LoanType.INPUTS.value and not input_value.data:
            raise ValidationError('La valeur des intrants est obligatoire pour un prêt en intrants.')

class LoanApprovalForm(FlaskForm):
    """Formulaire d'approbation de prêt"""
    approved = SelectField('Décision', 
                          choices=[('approved', 'Approuver'), ('rejected', 'Rejeter')],
                          validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Valider la décision')
