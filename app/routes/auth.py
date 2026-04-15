from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    """Charger l'utilisateur pour Flask-Login"""
    return User.query.get(int(user_id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            user.last_login = db.session.execute(
                db.select(db.func.current_timestamp())
            ).scalar()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            
            flash(f'Bienvenue {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription (uniquement pour les admins)"""
    if current_user.is_authenticated and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role='agent'  # Par défaut, les nouveaux utilisateurs sont des agents
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Utilisateur {user.username} créé avec succès', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/profile')
@login_required
def profile():
    """Profil utilisateur"""
    return render_template('auth/profile.html', user=current_user)
