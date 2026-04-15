from datetime import datetime, date
from decimal import Decimal
from app import db

class PaymentSchedule(db.Model):
    """Modèle échéancier pour la gestion des plans de remboursement"""
    __tablename__ = 'payment_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    principal_amount = db.Column(db.Numeric(12, 2), nullable=False)
    interest_amount = db.Column(db.Numeric(12, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'paid', 'partial', 'overdue', name='schedule_status'), 
                      default='pending', nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    paid_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relations
    payments = db.relationship('Payment', backref='related_schedule', lazy='dynamic')
    
    @property
    def is_overdue(self):
        """Vérifier si l'échéance est en retard"""
        if self.status != 'pending':
            return False
        return date.today() > self.due_date
    
    @property
    def overdue_days(self):
        """Nombre de jours de retard"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def remaining_amount(self):
        """Montant restant à payer pour cette échéance"""
        return float(self.total_amount) - float(self.paid_amount)
    
    def mark_as_paid(self, amount, payment_date=None):
        """Marquer l'échéance comme payée"""
        self.paid_amount = min(amount, self.total_amount)
        if payment_date:
            self.paid_date = payment_date
        else:
            self.paid_date = date.today()
        
        if float(self.paid_amount) >= float(self.total_amount):
            self.status = 'paid'
        else:
            self.status = 'partial'
    
    def __repr__(self):
        return f'<PaymentSchedule {self.installment_number} - {self.loan.code}>'
