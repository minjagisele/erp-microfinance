from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.loan import Loan, LoanType, RepaymentFrequency
from app.models.client import Client
from app.services.loan_service import LoanService
from app.forms.loan import LoanForm, LoanApprovalForm

bp = Blueprint('loans', __name__)

@bp.route('/')
@login_required
def index():
    """Liste des prêts"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Loan.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    loans = query.order_by(Loan.created_at.desc())\
                 .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('loans/index.html', 
                         loans=loans, 
                         status_filter=status_filter,
                         title='Liste des prêts')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Création d'un nouveau prêt"""
    form = LoanForm()
    
    # Remplir la liste des clients
    clients = Client.query.filter_by(is_active=True).all()
    form.client_id.choices = [(c.id, f'{c.code} - {c.full_name}') for c in clients]
    
    if form.validate_on_submit():
        # Générer un code de prêt unique
        loan_code = f"LOAN{db.session.execute(db.select(db.func.current_timestamp())).scalar().strftime('%Y%m%d%H%M%S')}"
        
        loan = Loan(
            code=loan_code,
            client_id=form.client_id.data,
            amount=form.amount.data,
            interest_rate=form.interest_rate.data,
            duration_months=form.duration_months.data,
            loan_type=LoanType(form.loan_type.data),
            repayment_frequency=RepaymentFrequency(form.repayment_frequency.data),
            input_value=form.input_value.data,
            purpose=form.purpose.data,
            first_payment_date=form.first_payment_date.data,
            created_by=current_user.id
        )
        
        db.session.add(loan)
        db.session.commit()
        
        flash(f'Prêt {loan.code} créé avec succès', 'success')
        return redirect(url_for('loans.view', id=loan.id))
    
    return render_template('loans/create.html', form=form, title='Nouveau prêt')

@bp.route('/<int:id>')
@login_required
def view(id):
    """Détails d'un prêt"""
    loan = Loan.query.get_or_404(id)
    summary = LoanService.get_loan_summary(id)
    
    return render_template('loans/view.html', 
                         loan=loan, 
                         summary=summary,
                         title=f'Prêt - {loan.code}')

@bp.route('/<int:id>/approve', methods=['GET', 'POST'])
@login_required
def approve(id):
    """Approbation d'un prêt"""
    loan = Loan.query.get_or_404(id)
    
    if loan.status != 'pending':
        flash('Ce prêt ne peut plus être approuvé', 'warning')
        return redirect(url_for('loans.view', id=id))
    
    form = LoanApprovalForm()
    
    if form.validate_on_submit():
        if form.approved.data == 'approved':
            success, message = LoanService.approve_loan(id, current_user.id)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
        else:
            loan.status = 'rejected'
            loan.approved_by = current_user.id
            loan.approved_at = db.session.execute(db.select(db.func.current_timestamp())).scalar()
            db.session.commit()
            flash('Prêt rejeté', 'info')
        
        return redirect(url_for('loans.view', id=id))
    
    return render_template('loans/approve.html', 
                         form=form, 
                         loan=loan,
                         title=f'Approbation - {loan.code}')

@bp.route('/<int:id>/schedule')
@login_required
def schedule(id):
    """Échéancier d'un prêt"""
    loan = Loan.query.get_or_404(id)
    schedules = LoanService.calculate_loan_schedule(loan)
    
    return render_template('loans/schedule.html', 
                         loan=loan, 
                         schedules=schedules,
                         title=f'Échéancier - {loan.code}')

@bp.route('/<int:id>/regenerate', methods=['POST'])
@login_required
def regenerate_schedule(id):
    """Régénérer l'échéancier d'un prêt"""
    success, message = LoanService.regenerate_schedule(id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('loans.schedule', id=id))

@bp.route('/api/client-loans/<int:client_id>')
@login_required
def api_client_loans(client_id):
    """API pour obtenir les prêts d'un client"""
    loans = Loan.query.filter_by(client_id=client_id)\
                      .order_by(Loan.created_at.desc())\
                      .limit(10).all()
    
    results = []
    for loan in loans:
        results.append({
            'id': loan.id,
            'code': loan.code,
            'amount': float(loan.amount),
            'status': loan.status,
            'created_at': loan.created_at.strftime('%d/%m/%Y'),
            'outstanding_balance': loan.outstanding_balance
        })
    
    return jsonify(results)
