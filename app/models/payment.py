from datetime import datetime
from decimal import Decimal
from app import db

class Payment(db.Model):
    """Modèle paiement pour le suivi des remboursements"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    payment_method = db.Column(db.Enum('cash', 'mobile_money', 'bank_transfer', name='payment_method'), 
                              default='cash', nullable=False)
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'paid', 'cancelled', name='payment_status'), 
                      default='paid', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('payment_schedules.id'))
    
    # Relations
    schedule = db.relationship('PaymentSchedule', backref='payment')
    
    @property
    def is_late(self):
        """Vérifier si le paiement est en retard"""
        if not self.schedule:
            return False
        return self.payment_date > self.schedule.due_date
    
    @property
    def late_days(self):
        """Nombre de jours de retard"""
        if not self.is_late:
            return 0
        return (self.payment_date - self.schedule.due_date).days
    
    def __repr__(self):
        return f'<Payment {self.code} - {self.amount}>'
