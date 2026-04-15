from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.payment import Payment
from app.models.loan import Loan
from app.services.payment_service import PaymentService

bp = Blueprint('payments', __name__)

@bp.route('/')
@login_required
def index():
    """Liste des paiements"""
    page = request.args.get('page', 1, type=int)
    loan_id = request.args.get('loan_id', type=int)
    
    if loan_id:
        payments_history = PaymentService.get_payment_history(loan_id, page)
        loan = Loan.query.get_or_404(loan_id)
        return render_template('payments/loan_history.html', 
                             payments_history=payments_history,
                             loan=loan,
                             title=f'Paiements - {loan.code}')
    
    payments = Payment.query.order_by(Payment.payment_date.desc())\
                          .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('payments/index.html', 
                         payments=payments, 
                         title='Liste des paiements')

@bp.route('/create/<int:loan_id>', methods=['GET', 'POST'])
@login_required
def create(loan_id):
    """Enregistrement d'un nouveau paiement"""
    loan = Loan.query.get_or_404(loan_id)
    
    if loan.status != 'approved':
        flash('Les paiements ne sont possibles que pour les prêts approuvés', 'warning')
        return redirect(url_for('loans.view', id=loan_id))
    
    from app.forms.payment import PaymentForm
    form = PaymentForm()
    
    if form.validate_on_submit():
        success, message, payment = PaymentService.process_payment(
            loan_id=loan_id,
            amount=float(form.amount.data),
            payment_method=form.payment_method.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('payments.view', id=payment.id))
        else:
            flash(message, 'danger')
    
    # Pr-remplir avec les informations du prêt
    return render_template('payments/create.html', 
                         form=form, 
                         loan=loan,
                         title=f'Nouveau paiement - {loan.code}')

@bp.route('/<int:id>')
@login_required
def view(id):
    """Détails d'un paiement"""
    payment = Payment.query.get_or_404(id)
    
    return render_template('payments/view.html', 
                         payment=payment,
                         title=f'Paiement - {payment.code}')

@bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    """Annulation d'un paiement"""
    reason = request.form.get('reason', '')
    success, message = PaymentService.cancel_payment(id, reason)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('payments.view', id=id))

@bp.route('/overdue')
@login_required
def overdue():
    """Liste des paiements en retard"""
    overdue_payments = PaymentService.get_overdue_payments()
    
    return render_template('payments/overdue.html', 
                         overdue_payments=overdue_payments,
                         title='Paiements en retard')

@bp.route('/reminders')
@login_required
def reminders():
    """Rappels de paiement à venir"""
    days_ahead = request.args.get('days', 7, type=int)
    reminders = PaymentService.generate_payment_reminders(days_ahead)
    
    return render_template('payments/reminders.html', 
                         reminders=reminders,
                         days_ahead=days_ahead,
                         title='Rappels de paiement')

@bp.route('/api/loan-balance/<int:loan_id>')
@login_required
def api_loan_balance(loan_id):
    """API pour obtenir le solde d'un prêt"""
    loan = Loan.query.get_or_404(loan_id)
    
    return jsonify({
        'total_amount_due': loan.total_amount_due,
        'total_paid': loan.total_paid,
        'outstanding_balance': loan.outstanding_balance,
        'next_payment_amount': loan.next_payment_amount
    })
