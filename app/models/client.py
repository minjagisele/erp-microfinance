from datetime import datetime
from app import db

class Client(db.Model):
    """Modèle client pour la gestion des clients de microfinance"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False, index=True)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    activity = db.Column(db.String(100), nullable=False)
    id_card_number = db.Column(db.String(50), unique=True)
    id_card_type = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.Enum('M', 'F', name='gender'))
    marital_status = db.Column(db.String(20))
    number_of_children = db.Column(db.Integer, default=0)
    monthly_income = db.Column(db.Numeric(12, 2))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relations
    loans = db.relationship('Loan', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        """Nom complet du client"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def active_loans(self):
        """Prêts actifs du client"""
        return self.loans.filter_by(status='approved').all()
    
    @property
    def total_loan_amount(self):
        """Montant total des prêts"""
        return sum(loan.amount for loan in self.loans if loan.status == 'approved')
    
    @property
    def total_paid_amount(self):
        """Montant total remboursé"""
        total = 0
        for loan in self.loans:
            total += sum(payment.amount for payment in loan.payments if payment.status == 'paid')
        return total
    
    @property
    def outstanding_balance(self):
        """Solde restant dû"""
        return self.total_loan_amount - self.total_paid_amount
    
    def __repr__(self):
        return f'<Client {self.code} - {self.full_name}>'
