from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.loan import Loan
from app.services.client_service import ClientService
from app.forms.client import ClientForm, ClientSearchForm

bp = Blueprint('clients', __name__)

@bp.route('/')
@login_required
def index():
    """Liste des clients"""
    page = request.args.get('page', 1, type=int)
    form = ClientSearchForm()
    
    clients = Client.query.filter_by(is_active=True)\
                         .order_by(Client.created_at.desc())\
                         .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('clients/index.html', 
                         clients=clients, 
                         form=form,
                         title='Liste des clients')

@bp.route('/search')
@login_required
def search():
    """Recherche de clients"""
    form = ClientSearchForm()
    clients = None
    
    if form.validate_on_submit() or request.args.get('q'):
        query = request.args.get('q', form.query.data)
        clients = ClientService.search_clients(query)
    
    return render_template('clients/search.html', 
                         form=form, 
                         clients=clients,
                         title='Recherche de clients')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Création d'un nouveau client"""
    form = ClientForm()
    
    if form.validate_on_submit():
        client_data = {
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'address': form.address.data,
            'activity': form.activity.data,
            'id_card_number': form.id_card_number.data,
            'id_card_type': form.id_card_type.data,
            'birth_date': form.birth_date.data,
            'gender': form.gender.data,
            'marital_status': form.marital_status.data,
            'number_of_children': form.number_of_children.data,
            'monthly_income': form.monthly_income.data
        }
        
        success, message, client = ClientService.create_client(client_data, current_user.id)
        
        if success:
            flash(f'Client {client.code} créé avec succès', 'success')
            return redirect(url_for('clients.view', id=client.id))
        else:
            flash(message, 'danger')
    
    return render_template('clients/create.html', form=form, title='Nouveau client')

@bp.route('/<int:id>')
@login_required
def view(id):
    """Détails d'un client"""
    client = Client.query.get_or_404(id)
    summary = ClientService.get_client_summary(id)
    
    return render_template('clients/view.html', 
                         client=client, 
                         summary=summary,
                         title=f'Client - {client.full_name}')

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Modification d'un client"""
    client = Client.query.get_or_404(id)
    form = ClientForm(original_phone=client.phone, obj=client)
    
    if form.validate_on_submit():
        client_data = {
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'phone': form.phone.data,
            'email': form.email.data,
            'address': form.address.data,
            'activity': form.activity.data,
            'id_card_number': form.id_card_number.data,
            'id_card_type': form.id_card_type.data,
            'birth_date': form.birth_date.data,
            'gender': form.gender.data,
            'marital_status': form.marital_status.data,
            'number_of_children': form.number_of_children.data,
            'monthly_income': form.monthly_income.data
        }
        
        success, message = ClientService.update_client(id, client_data)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('clients.view', id=id))
        else:
            flash(message, 'danger')
    
    return render_template('clients/edit.html', form=form, client=client, title='Modifier client')

@bp.route('/<int:id>/deactivate', methods=['POST'])
@login_required
def deactivate(id):
    """Désactivation d'un client"""
    success, message = ClientService.deactivate_client(id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('clients.view', id=id))

@bp.route('/api/search')
@login_required
def api_search():
    """API pour la recherche de clients (autocomplete)"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    clients = Client.query.filter(
        db.or_(
            Client.first_name.ilike(f'%{query}%'),
            Client.last_name.ilike(f'%{query}%'),
            Client.phone.ilike(f'%{query}%'),
            Client.code.ilike(f'%{query}%')
        ),
        Client.is_active == True
    ).limit(10).all()
    
    results = []
    for client in clients:
        results.append({
            'id': client.id,
            'code': client.code,
            'name': client.full_name,
            'phone': client.phone,
            'activity': client.activity
        })
    
    return jsonify(results)
