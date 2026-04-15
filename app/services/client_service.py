from datetime import datetime
from typing import List, Dict, Tuple
from app import db
from app.models.client import Client
from app.models.loan import Loan

class ClientService:
    """Service pour la gestion des clients"""
    
    @staticmethod
    def create_client(client_data: Dict, created_by: int) -> Tuple[bool, str, Client]:
        """
        Créer un nouveau client
        
        Args:
            client_data: Données du client
            created_by: ID de l'utilisateur qui crée
            
        Returns:
            (succès, message, client)
        """
        try:
            # Vérifier si le téléphone existe déjà
            if Client.query.filter_by(phone=client_data['phone']).first():
                return False, "Ce numéro de téléphone existe déjà", None
            
            # Générer un code client unique
            client_code = ClientService._generate_client_code()
            
            client = Client(
                code=client_code,
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                phone=client_data['phone'],
                email=client_data.get('email'),
                address=client_data.get('address'),
                activity=client_data['activity'],
                id_card_number=client_data.get('id_card_number'),
                id_card_type=client_data.get('id_card_type'),
                birth_date=client_data.get('birth_date'),
                gender=client_data.get('gender'),
                marital_status=client_data.get('marital_status'),
                number_of_children=client_data.get('number_of_children', 0),
                monthly_income=client_data.get('monthly_income'),
                created_by=created_by
            )
            
            db.session.add(client)
            db.session.commit()
            
            return True, "Client créé avec succès", client
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la création: {str(e)}", None
    
    @staticmethod
    def update_client(client_id: int, client_data: Dict) -> Tuple[bool, str]:
        """
        Mettre à jour les informations d'un client
        
        Args:
            client_id: ID du client
            client_data: Nouvelles données
            
        Returns:
            (succès, message)
        """
        try:
            client = Client.query.get(client_id)
            if not client:
                return False, "Client non trouvé"
            
            # Vérifier si le téléphone est déjà utilisé par un autre client
            if 'phone' in client_data:
                existing = Client.query.filter(
                    Client.phone == client_data['phone'],
                    Client.id != client_id
                ).first()
                if existing:
                    return False, "Ce numéro de téléphone est déjà utilisé"
            
            # Mettre à jour les champs
            for field, value in client_data.items():
                if hasattr(client, field) and field not in ['id', 'code', 'created_at', 'created_by']:
                    setattr(client, field, value)
            
            client.updated_at = datetime.utcnow()
            db.session.commit()
            
            return True, "Client mis à jour avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la mise à jour: {str(e)}"
    
    @staticmethod
    def _generate_client_code() -> str:
        """Générer un code client unique"""
        prefix = "CLI"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}{timestamp}"
    
    @staticmethod
    def get_client_by_code(client_code: str) -> Client:
        """
        Obtenir un client par son code
        
        Args:
            client_code: Code du client
            
        Returns:
            Objet client ou None
        """
        return Client.query.filter_by(code=client_code).first()
    
    @staticmethod
    def search_clients(query: str, page: int = 1, per_page: int = 20) -> Dict:
        """
        Rechercher des clients
        
        Args:
            query: Terme de recherche
            page: Page pour la pagination
            per_page: Nombre par page
            
        Returns:
            Dictionnaire avec les résultats et pagination
        """
        search = f"%{query}%"
        
        clients = Client.query.filter(
            db.or_(
                Client.code.ilike(search),
                Client.first_name.ilike(search),
                Client.last_name.ilike(search),
                Client.phone.ilike(search),
                Client.activity.ilike(search)
            )
        ).filter_by(is_active=True)\
         .order_by(Client.created_at.desc())\
         .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'clients': clients.items,
            'total': clients.total,
            'pages': clients.pages,
            'current_page': clients.page,
            'has_next': clients.has_next,
            'has_prev': clients.has_prev
        }
    
    @staticmethod
    def get_client_summary(client_id: int) -> Dict:
        """
        Obtenir un résumé complet d'un client
        
        Args:
            client_id: ID du client
            
        Returns:
            Dictionnaire avec les informations du client
        """
        client = Client.query.get(client_id)
        if not client:
            return {}
        
        # Statistiques des prêts
        total_loans = client.loans.count()
        active_loans = client.active_loans
        completed_loans = client.loans.filter_by(status='completed').count()
        defaulted_loans = client.loans.filter_by(status='defaulted').count()
        
        # Montants
        total_borrowed = client.total_loan_amount
        total_repaid = client.total_paid_amount
        outstanding_balance = client.outstanding_balance
        
        # Prêts en retard
        overdue_loans = [loan for loan in active_loans if loan.is_overdue]
        
        return {
            'client': client,
            'total_loans': total_loans,
            'active_loans': len(active_loans),
            'completed_loans': completed_loans,
            'defaulted_loans': defaulted_loans,
            'overdue_loans': len(overdue_loans),
            'total_borrowed': total_borrowed,
            'total_repaid': total_repaid,
            'outstanding_balance': outstanding_balance,
            'repayment_rate': (total_repaid / total_borrowed * 100) if total_borrowed > 0 else 0,
            'recent_loans': client.loans.order_by(Loan.created_at.desc()).limit(5).all()
        }
    
    @staticmethod
    def deactivate_client(client_id: int) -> Tuple[bool, str]:
        """
        Désactiver un client (suppression logique)
        
        Args:
            client_id: ID du client
            
        Returns:
            (succès, message)
        """
        try:
            client = Client.query.get(client_id)
            if not client:
                return False, "Client non trouvé"
            
            # Vérifier s'il y a des prêts actifs
            if client.active_loans:
                return False, "Impossible de désactiver un client avec des prêts actifs"
            
            client.is_active = False
            client.updated_at = datetime.utcnow()
            db.session.commit()
            
            return True, "Client désactivé avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la désactivation: {str(e)}"
    
    @staticmethod
    def get_clients_with_overdue_loans() -> List[Client]:
        """
        Obtenir la liste des clients avec des prêts en retard
        
        Returns:
            Liste des clients avec prêts en retard
        """
        from app.models.schedule import PaymentSchedule
        
        # Requête pour trouver les clients avec des échéances en retard
        clients_with_overdue = db.session.query(Client).join(
            Loan, Client.id == Loan.client_id
        ).join(
            PaymentSchedule, Loan.id == PaymentSchedule.loan_id
        ).filter(
            Loan.status == 'approved',
            PaymentSchedule.status == 'pending',
            PaymentSchedule.due_date < datetime.now().date()
        ).distinct().all()
        
        return clients_with_overdue
    
    @staticmethod
    def get_client_statistics() -> Dict:
        """
        Obtenir les statistiques globales des clients
        
        Returns:
            Dictionnaire avec les statistiques
        """
        total_clients = Client.query.filter_by(is_active=True).count()
        new_clients_this_month = Client.query.filter(
            Client.is_active == True,
            db.extract('month', Client.created_at) == datetime.now().month,
            db.extract('year', Client.created_at) == datetime.now().year
        ).count()
        
        clients_with_loans = db.session.query(Client.id).join(
            Loan, Client.id == Loan.client_id
        ).filter(
            Loan.status == 'approved'
        ).distinct().count()
        
        return {
            'total_clients': total_clients,
            'new_clients_this_month': new_clients_this_month,
            'clients_with_loans': clients_with_loans,
            'clients_without_loans': total_clients - clients_with_loans
        }
