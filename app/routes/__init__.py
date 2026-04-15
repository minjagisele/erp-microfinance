# Import des blueprints
from .auth import bp as auth_bp
from .clients import bp as clients_bp
from .loans import bp as loans_bp
from .payments import bp as payments_bp
from .dashboard import bp as dashboard_bp
from .api import bp as api_bp

__all__ = ['auth_bp', 'clients_bp', 'loans_bp', 'payments_bp', 'dashboard_bp', 'api_bp']
