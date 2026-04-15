# ERP Microfinance

Un système de gestion de microfinance robuste développé avec Flask, conçu pour la gestion des prêts, des remboursements et du suivi des clients.

## Fonctionnalités

### Gestion des Clients
- CRUD complet des clients
- suivi des informations personnelles et professionnelles
- Historique des prêts par client
- Recherche avancée

### Gestion des Prêts
- Prêts en espèces et en intrants
- Calcul automatique des échéanciers
- Taux d'intérêt configurables
- Durées flexibles (1-60 mois)
- Fréquences de remboursement (journalier, hebdomadaire, mensuel)

### Suivi des Remboursements
- Enregistrement des paiements
- Gestion des paiements partiels
- Détection automatique des impayés
- Alertes visuelles pour les retards

### Tableau de Bord
- Statistiques en temps réel
- Graphiques d'évolution
- Alertes sur les échéances
- Rapports financiers

## Stack Technique

- **Backend**: Flask 2.3.3
- **Base de données**: PostgreSQL (avec support MySQL)
- **ORM**: SQLAlchemy
- **Formulaires**: WTForms
- **Authentification**: Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap 5)
- **Migration**: Flask-Migrate

## Installation

### Prérequis
- Python 3.8+
- PostgreSQL (ou MySQL)
- pip

### Étapes d'installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd erp-microfinance
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer la base de données**
```bash
# Créer la base de données PostgreSQL
createdb erp_microfinance_dev

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos informations de base de données
```

5. **Initialiser la base de données**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. **Créer un utilisateur administrateur**
```bash
python -c "
from app import create_app, db
from app.models.user import User
app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        phone='1234567890',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Administrateur créé avec succès')
"
```

7. **Lancer l'application**
```bash
python run.py
```

L'application sera accessible sur `http://localhost:5000`

## Configuration

### Variables d'environnement

Copiez `.env.example` vers `.env` et configurez les variables suivantes:

- `DATABASE_URL`: URL de connexion à la base de données
- `SECRET_KEY`: Clé secrète pour les sessions Flask
- `FLASK_ENV`: Environnement (development/production)

### Configuration de la base de données

#### PostgreSQL (recommandé)
```sql
CREATE DATABASE erp_microfinance_dev;
CREATE USER erp_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE erp_microfinance_dev TO erp_user;
```

#### MySQL
```sql
CREATE DATABASE erp_microfinance_dev;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON erp_microfinance_dev.* TO 'erp_user'@'localhost';
```

## Utilisation

### Connexion initiale

1. Accédez à `http://localhost:5000`
2. Connectez-vous avec:
   - Nom d'utilisateur: `admin`
   - Mot de passe: `admin123`

### Flux de travail typique

1. **Créer un client**: Allez dans Clients > Nouveau Client
2. **Créer un prêt**: Allez dans Prêts > Nouveau Prêt
3. **Approuver le prêt**: Dans la page du prêt, cliquez sur "Approuver"
4. **Enregistrer les paiements**: Allez dans Paiements > Enregistrer Paiement

## Architecture du Projet

```
/app
  /models          # Modèles SQLAlchemy
  /routes          # Routes Flask (Blueprints)
  /services        # Logique métier
  /forms           # Formulaires WTForms
  /templates       # Templates Jinja2
  /static
    /css          # Styles CSS
    /js           # JavaScript
    /img          # Images
/config            # Configuration
/migrations        # Migrations de base de données
/tests             # Tests unitaires
run.py             # Point d'entrée
requirements.txt   # Dépendances Python
```

## Développement

### Ajout de nouvelles fonctionnalités

1. **Modèles**: Ajoutez vos modèles dans `app/models/`
2. **Services**: Implémentez la logique métier dans `app/services/`
3. **Routes**: Créez de nouvelles routes dans `app/routes/`
4. **Templates**: Ajoutez les templates dans `app/templates/`

### Tests

```bash
# Lancer les tests
python -m pytest tests/

# Tests avec couverture
python -m pytest --cov=app tests/
```

### Migrations de base de données

```bash
# Créer une nouvelle migration
flask db migrate -m "Description de la modification"

# Appliquer les migrations
flask db upgrade

# Annuler la dernière migration
flask db downgrade
```

## Déploiement

### Production

1. **Configuration**
   - Changez `FLASK_ENV=production`
   - Utilisez une base de données PostgreSQL robuste
   - Configurez un `SECRET_KEY` sécurisé

2. **Serveur WSGI**
   - Utilisez Gunicorn ou uWSGI
   - Configurez Nginx comme reverse proxy

3. **Exemple avec Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## Support et Maintenance

### Sauvegarde

```bash
# Sauvegarde PostgreSQL
pg_dump erp_microfinance_prod > backup.sql

# Restauration
psql erp_microfinance_prod < backup.sql
```

### Monitoring

- Surveillez les logs de l'application
- Configurez des alertes pour les erreurs critiques
- Surveillez les performances de la base de données

## Contribuer

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Commitez vos changements
4. Pushez vers votre fork
5. Créez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Contact

Pour toute question ou support, veuillez contacter l'équipe de développement.

---

**Note**: Ce système est conçu pour être utilisé par des agents de terrain avec une interface simple et responsive, adaptée aux connexions internet faibles.
