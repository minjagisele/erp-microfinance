from datetime import datetime, date
from decimal import Decimal
from app import db
from enum import Enum

class LoanType(Enum):
    """Types de prêts"""
    CASH = 'cash'  # Prêt en espèces
    INPUTS = 'inputs'  # Prêt en intrants

class RepaymentFrequency(Enum):
    """Fréquences de remboursement"""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

class Loan(db.Model):
    """Modèle prêt pour la gestion des prêts de microfinance"""
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # Taux d'intérêt en %
    duration_months = db.Column(db.Integer, nullable=False)
    loan_type = db.Column(db.Enum(LoanType), nullable=False)
    repayment_frequency = db.Column(db.Enum(RepaymentFrequency), nullable=False)
    input_value = db.Column(db.Numeric(12, 2))  # Valeur des intrants si applicable
    purpose = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'completed', 'defaulted', name='loan_status'), 
                       default='pending', nullable=False)
    disbursement_date = db.Column(db.Date)
    first_payment_date = db.Column(db.Date)
    maturity_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Relations
    payments = db.relationship('Payment', backref='loan', lazy='dynamic', cascade='all, delete-orphan')
    schedules = db.relationship('PaymentSchedule', backref='loan', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_interest(self):
        """Calcul du total des intérêts"""
        return float(self.amount * (self.interest_rate / 100) * (self.duration_months / 12))
    
    @property
    def total_amount_due(self):
        """Montant total dû (capital + intérêts)"""
        return float(self.amount) + self.total_interest
    
    @property
    def total_paid(self):
        """Montant total remboursé"""
        return sum(payment.amount for payment in self.payments if payment.status == 'paid')
    
    @property
    def outstanding_balance(self):
        """Solde restant dû"""
        return self.total_amount_due - self.total_paid
    
    @property
    def next_payment_amount(self):
        """Montant de la prochaine échéance"""
        if self.repayment_frequency == RepaymentFrequency.DAILY:
            return self.total_amount_due / (self.duration_months * 30)
        elif self.repayment_frequency == RepaymentFrequency.WEEKLY:
            return self.total_amount_due / (self.duration_months * 4)
        else:  # MONTHLY
            return self.total_amount_due / self.duration_months
    
    @property
    def is_overdue(self):
        """Vérifier si le prêt est en retard"""
        if self.status != 'approved':
            return False
        today = date.today()
        unpaid_schedules = self.schedules.filter_by(status='pending').all()
        return any(schedule.due_date < today for schedule in unpaid_schedules)
    
    @property
    def overdue_days(self):
        """Nombre de jours de retard"""
        if not self.is_overdue:
            return 0
        today = date.today()
        unpaid_schedules = self.schedules.filter_by(status='pending').all()
        overdue_schedules = [s for s in unpaid_schedules if s.due_date < today]
        if not overdue_schedules:
            return 0
        earliest_overdue = min(overdue_schedules, key=lambda x: x.due_date)
        return (today - earliest_overdue.due_date).days
    
    def __repr__(self):
        return f'<Loan {self.code} - {self.client.full_name}>'
