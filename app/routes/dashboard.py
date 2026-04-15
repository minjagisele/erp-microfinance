from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models.client import Client
from app.models.loan import Loan
from app.models.payment import Payment
from app.models.schedule import PaymentSchedule
from app.services.client_service import ClientService
from app.services.payment_service import PaymentService
from app.services.schedule_service import ScheduleService

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Tableau de bord principal"""
    # Statistiques globales
    total_clients = Client.query.filter_by(is_active=True).count()
    total_loans = Loan.query.count()
    active_loans = Loan.query.filter_by(status='approved').count()
    completed_loans = Loan.query.filter_by(status='completed').count()
    
    # Statistiques financières
    total_loan_amount = db.session.query(db.func.sum(Loan.amount)).filter(Loan.status == 'approved').scalar() or 0
    total_paid_amount = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'paid').scalar() or 0
    outstanding_balance = float(total_loan_amount) - float(total_paid_amount)
    
    # Statistiques du mois
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    new_clients_this_month = Client.query.filter(
        db.extract('month', Client.created_at) == current_month,
        db.extract('year', Client.created_at) == current_year,
        Client.is_active == True
    ).count()
    
    new_loans_this_month = Loan.query.filter(
        db.extract('month', Loan.created_at) == current_month,
        db.extract('year', Loan.created_at) == current_year
    ).count()
    
    payments_this_month = db.session.query(db.func.sum(Payment.amount)).filter(
        db.extract('month', Payment.payment_date) == current_month,
        db.extract('year', Payment.payment_date) == current_year,
        Payment.status == 'paid'
    ).scalar() or 0
    
    # Échéances en retard
    overdue_schedules = ScheduleService.get_overdue_schedules()
    overdue_count = len(overdue_schedules)
    overdue_amount = sum(float(s.remaining_amount) for s in overdue_schedules)
    
    # Échéances à venir (7 jours)
    upcoming_schedules = ScheduleService.get_upcoming_schedules(7)
    upcoming_count = len(upcoming_schedules)
    upcoming_amount = sum(float(s.remaining_amount) for s in upcoming_schedules)
    
    # Activités récentes
    recent_loans = Loan.query.order_by(Loan.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    stats = {
        'total_clients': total_clients,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'total_loan_amount': float(total_loan_amount),
        'total_paid_amount': float(total_paid_amount),
        'outstanding_balance': outstanding_balance,
        'new_clients_this_month': new_clients_this_month,
        'new_loans_this_month': new_loans_this_month,
        'payments_this_month': float(payments_this_month),
        'overdue_count': overdue_count,
        'overdue_amount': overdue_amount,
        'upcoming_count': upcoming_count,
        'upcoming_amount': upcoming_amount,
        'repayment_rate': (float(total_paid_amount) / float(total_loan_amount) * 100) if total_loan_amount > 0 else 0
    }
    
    return render_template('dashboard/index.html', 
                         stats=stats,
                         recent_loans=recent_loans,
                         recent_payments=recent_payments,
                         overdue_schedules=overdue_schedules[:5],
                         upcoming_schedules=upcoming_schedules[:5],
                         title='Tableau de bord')

@bp.route('/charts')
@login_required
def charts():
    """Données pour les graphiques du dashboard"""
    # Prêts par mois (6 derniers mois)
    loans_by_month = []
    for i in range(6):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = Loan.query.filter(
            Loan.created_at >= month_start,
            Loan.created_at <= month_end
        ).count()
        
        loans_by_month.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    # Paiements par mois (6 derniers mois)
    payments_by_month = []
    for i in range(6):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        amount = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_start,
            Payment.payment_date <= month_end,
            Payment.status == 'paid'
        ).scalar() or 0
        
        payments_by_month.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(amount)
        })
    
    # Répartition des prêts par statut
    loan_status_stats = db.session.query(
        Loan.status, db.func.count(Loan.id)
    ).group_by(Loan.status).all()
    
    status_data = {status: count for status, count in loan_status_stats}
    
    return jsonify({
        'loans_by_month': list(reversed(loans_by_month)),
        'payments_by_month': list(reversed(payments_by_month)),
        'loan_status': {
            'labels': list(status_data.keys()),
            'data': list(status_data.values())
        }
    })
