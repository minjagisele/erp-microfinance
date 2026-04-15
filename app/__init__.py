from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config.config import config

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name):
    """Factory pattern pour créer l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions avec l'application
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configuration du gestionnaire de login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Enregistrement des blueprints
    from app.routes import auth, clients, loans, payments, dashboard, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(clients.bp, url_prefix='/clients')
    app.register_blueprint(loans.bp, url_prefix='/loans')
    app.register_blueprint(payments.bp, url_prefix='/payments')
    app.register_blueprint(dashboard.bp, url_prefix='/dashboard')
    app.register_blueprint(api.bp, url_prefix='/api')
    
    return app
