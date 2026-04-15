from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.loan import Loan, LoanType, RepaymentFrequency
from app.models.payment import Payment
from app.services.client_service import ClientService
from app.services.loan_service import LoanService
from app.services.payment_service import PaymentService

bp = Blueprint('api', __name__)

# API Clients
@bp.route('/clients', methods=['GET'])
@login_required
def get_clients():
    """API pour obtenir la liste des clients"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    if search:
        clients_data = ClientService.search_clients(search, page)
    else:
        clients = Client.query.filter_by(is_active=True)\
                           .order_by(Client.created_at.desc())\
                           .paginate(page=page, per_page=20, error_out=False)
        
        clients_data = {
            'clients': clients.items,
            'total': clients.total,
            'pages': clients.pages,
            'current_page': clients.page
        }
    
    result = {
        'clients': [
            {
                'id': c.id,
                'code': c.code,
                'full_name': c.full_name,
                'phone': c.phone,
                'activity': c.activity,
                'created_at': c.created_at.strftime('%Y-%m-%d'),
                'total_loans': c.loans.count(),
                'outstanding_balance': c.outstanding_balance
            }
            for c in clients_data['clients']
        ],
        'pagination': {
            'total': clients_data.get('total', 0),
            'pages': clients_data.get('pages', 0),
            'current_page': clients_data.get('current_page', 1)
        }
    }
    
    return jsonify(result)

@bp.route('/clients/<int:client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    """API pour obtenir les détails d'un client"""
    client = Client.query.get_or_404(client_id)
    summary = ClientService.get_client_summary(client_id)
    
    result = {
        'id': client.id,
        'code': client.code,
        'full_name': client.full_name,
        'phone': client.phone,
        'email': client.email,
        'address': client.address,
        'activity': client.activity,
        'is_active': client.is_active,
        'created_at': client.created_at.strftime('%Y-%m-%d'),
        'summary': {
            'total_loans': summary.get('total_loans', 0),
            'active_loans': summary.get('active_loans', 0),
            'completed_loans': summary.get('completed_loans', 0),
            'total_borrowed': summary.get('total_borrowed', 0),
            'total_repaid': summary.get('total_repaid', 0),
            'outstanding_balance': summary.get('outstanding_balance', 0),
            'repayment_rate': summary.get('repayment_rate', 0)
        }
    }
    
    return jsonify(result)

# API Prêts
@bp.route('/loans', methods=['GET'])
@login_required
def get_loans():
    """API pour obtenir la liste des prêts"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    client_id = request.args.get('client_id', type=int)
    
    query = Loan.query
    
    if status:
        query = query.filter_by(status=status)
    
    if client_id:
        query = query.filter_by(client_id=client_id)
    
    loans = query.order_by(Loan.created_at.desc())\
                .paginate(page=page, per_page=20, error_out=False)
    
    result = {
        'loans': [
            {
                'id': l.id,
                'code': l.code,
                'client': {
                    'id': l.client.id,
                    'name': l.client.full_name,
                    'code': l.client.code
                },
                'amount': float(l.amount),
                'interest_rate': float(l.interest_rate),
                'duration_months': l.duration_months,
                'loan_type': l.loan_type.value,
                'repayment_frequency': l.repayment_frequency.value,
                'status': l.status,
                'created_at': l.created_at.strftime('%Y-%m-%d'),
                'outstanding_balance': l.outstanding_balance,
                'is_overdue': l.is_overdue,
                'overdue_days': l.overdue_days
            }
            for l in loans.items
        ],
        'pagination': {
            'total': loans.total,
            'pages': loans.pages,
            'current_page': loans.page
        }
    }
    
    return jsonify(result)

@bp.route('/loans/<int:loan_id>', methods=['GET'])
@login_required
def get_loan(loan_id):
    """API pour obtenir les détails d'un prêt"""
    loan = Loan.query.get_or_404(loan_id)
    summary = LoanService.get_loan_summary(loan_id)
    
    result = {
        'id': loan.id,
        'code': loan.code,
        'client': {
            'id': loan.client.id,
            'name': loan.client.full_name,
            'code': loan.client.code,
            'phone': loan.client.phone
        },
        'amount': float(loan.amount),
        'interest_rate': float(loan.interest_rate),
        'duration_months': loan.duration_months,
        'loan_type': loan.loan_type.value,
        'repayment_frequency': loan.repayment_frequency.value,
        'purpose': loan.purpose,
        'status': loan.status,
        'disbursement_date': loan.disbursement_date.strftime('%Y-%m-%d') if loan.disbursement_date else None,
        'first_payment_date': loan.first_payment_date.strftime('%Y-%m-%d') if loan.first_payment_date else None,
        'maturity_date': loan.maturity_date.strftime('%Y-%m-%d') if loan.maturity_date else None,
        'created_at': loan.created_at.strftime('%Y-%m-%d'),
        'total_amount_due': loan.total_amount_due,
        'total_paid': loan.total_paid,
        'outstanding_balance': loan.outstanding_balance,
        'next_payment_amount': loan.next_payment_amount,
        'is_overdue': loan.is_overdue,
        'overdue_days': loan.overdue_days,
        'summary': {
            'total_paid': summary.get('total_paid', 0),
            'outstanding_balance': summary.get('outstanding_balance', 0),
            'pending_count': summary.get('pending_count', 0),
            'overdue_count': summary.get('overdue_count', 0)
        }
    }
    
    return jsonify(result)

@bp.route('/loans/<int:loan_id>/schedule', methods=['GET'])
@login_required
def get_loan_schedule(loan_id):
    """API pour obtenir l'échéancier d'un prêt"""
    loan = Loan.query.get_or_404(loan_id)
    schedules = LoanService.calculate_loan_schedule(loan)
    
    result = {
        'loan_id': loan.id,
        'loan_code': loan.code,
        'schedules': [
            {
                'installment_number': s['installment_number'],
                'due_date': s['due_date'].strftime('%Y-%m-%d'),
                'principal_amount': s['principal_amount'],
                'interest_amount': s['interest_amount'],
                'total_amount': s['total_amount'],
                'balance_after': s['balance_after']
            }
            for s in schedules
        ]
    }
    
    return jsonify(result)

# API Paiements
@bp.route('/payments', methods=['POST'])
@login_required
def create_payment():
    """API pour créer un paiement"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    try:
        success, message, payment = PaymentService.process_payment(
            loan_id=data['loan_id'],
            amount=float(data['amount']),
            payment_method=data.get('payment_method', 'cash'),
            notes=data.get('notes'),
            created_by=current_user.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'payment': {
                    'id': payment.id,
                    'code': payment.code,
                    'amount': float(payment.amount),
                    'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
                    'payment_method': payment.payment_method
                }
            }), 201
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/payments/overdue', methods=['GET'])
@login_required
def get_overdue_payments():
    """API pour obtenir les paiements en retard"""
    overdue_payments = PaymentService.get_overdue_payments()
    
    result = {
        'overdue_payments': [
            {
                'schedule_id': p['schedule'].id,
                'loan': {
                    'id': p['loan'].id,
                    'code': p['loan'].code,
                    'amount': float(p['loan'].amount)
                },
                'client': {
                    'id': p['client'].id,
                    'name': p['client'].full_name,
                    'phone': p['client'].phone
                },
                'overdue_days': p['overdue_days'],
                'overdue_amount': p['overdue_amount'],
                'due_date': p['schedule'].due_date.strftime('%Y-%m-%d')
            }
            for p in overdue_payments
        ]
    }
    
    return jsonify(result)

# API Statistiques
@bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """API pour obtenir les statistiques globales"""
    from datetime import datetime
    
    # Statistiques de base
    total_clients = Client.query.filter_by(is_active=True).count()
    total_loans = Loan.query.count()
    active_loans = Loan.query.filter_by(status='approved').count()
    
    # Statistiques financières
    total_loan_amount = db.session.query(db.func.sum(Loan.amount)).filter(Loan.status == 'approved').scalar() or 0
    total_paid_amount = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == 'paid').scalar() or 0
    
    # Statistiques du jour
    today = datetime.now().date()
    today_payments = db.session.query(db.func.sum(Payment.amount)).filter(
        Payment.payment_date == today,
        Payment.status == 'paid'
    ).scalar() or 0
    
    result = {
        'total_clients': total_clients,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'total_loan_amount': float(total_loan_amount),
        'total_paid_amount': float(total_paid_amount),
        'outstanding_balance': float(total_loan_amount) - float(total_paid_amount),
        'today_payments': float(today_payments),
        'repayment_rate': (float(total_paid_amount) / float(total_loan_amount) * 100) if total_loan_amount > 0 else 0
    }
    
    return jsonify(result)
