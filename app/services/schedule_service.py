from datetime import datetime, date, timedelta
from typing import List, Dict
from app import db
from app.models.schedule import PaymentSchedule
from app.models.loan import Loan

class ScheduleService:
    """Service pour la gestion des échéanciers de paiement"""
    
    @staticmethod
    def get_loan_schedule(loan_id: int) -> List[PaymentSchedule]:
        """
        Obtenir l'échéancier complet d'un prêt
        
        Args:
            loan_id: ID du prêt
            
        Returns:
            Liste des échéances
        """
        return PaymentSchedule.query.filter_by(loan_id=loan_id)\
                                  .order_by(PaymentSchedule.installment_number)\
                                  .all()
    
    @staticmethod
    def get_pending_schedules(loan_id: int) -> List[PaymentSchedule]:
        """
        Obtenir les échéances en attente pour un prêt
        
        Args:
            loan_id: ID du prêt
            
        Returns:
            Liste des échéances en attente
        """
        return PaymentSchedule.query.filter_by(loan_id=loan_id, status='pending')\
                                  .order_by(PaymentSchedule.due_date)\
                                  .all()
    
    @staticmethod
    def get_overdue_schedules(loan_id: int = None) -> List[PaymentSchedule]:
        """
        Obtenir les échéances en retard
        
        Args:
            loan_id: ID du prêt (optionnel)
            
        Returns:
            Liste des échéances en retard
        """
        query = PaymentSchedule.query.filter(
            PaymentSchedule.status == 'pending',
            PaymentSchedule.due_date < date.today()
        )
        
        if loan_id:
            query = query.filter_by(loan_id=loan_id)
        
        return query.order_by(PaymentSchedule.due_date).all()
    
    @staticmethod
    def get_upcoming_schedules(days_ahead: int = 7) -> List[PaymentSchedule]:
        """
        Obtenir les échéances à venir dans les prochains jours
        
        Args:
            days_ahead: Nombre de jours à venir
            
        Returns:
            Liste des échéances à venir
        """
        end_date = date.today() + timedelta(days=days_ahead)
        
        return PaymentSchedule.query.filter(
            PaymentSchedule.status == 'pending',
            PaymentSchedule.due_date >= date.today(),
            PaymentSchedule.due_date <= end_date
        ).order_by(PaymentSchedule.due_date).all()
    
    @staticmethod
    def update_schedule_status(schedule_id: int, status: str) -> bool:
        """
        Mettre à jour le statut d'une échéance
        
        Args:
            schedule_id: ID de l'échéance
            status: Nouveau statut
            
        Returns:
            True si succès, False sinon
        """
        try:
            schedule = PaymentSchedule.query.get(schedule_id)
            if not schedule:
                return False
            
            schedule.status = status
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False
    
    @staticmethod
    def bulk_update_overdue_status() -> int:
        """
        Mettre à jour en masse le statut des échéances en retard
        
        Returns:
            Nombre d'échéances mises à jour
        """
        try:
            overdue_count = PaymentSchedule.query.filter(
                PaymentSchedule.status == 'pending',
                PaymentSchedule.due_date < date.today()
            ).update({'status': 'overdue'})
            
            db.session.commit()
            return overdue_count
            
        except Exception:
            db.session.rollback()
            return 0
    
    @staticmethod
    def get_schedule_statistics(loan_id: int = None) -> Dict:
        """
        Obtenir les statistiques des échéances
        
        Args:
            loan_id: ID du prêt (optionnel)
            
        Returns:
            Dictionnaire avec les statistiques
        """
        query = PaymentSchedule.query
        
        if loan_id:
            query = query.filter_by(loan_id=loan_id)
        
        total = query.count()
        paid = query.filter_by(status='paid').count()
        pending = query.filter_by(status='pending').count()
        overdue = query.filter_by(status='overdue').count()
        partial = query.filter_by(status='partial').count()
        
        total_amount = sum(float(s.total_amount) for s in query.all())
        paid_amount = sum(float(s.paid_amount) for s in query.all())
        
        return {
            'total_schedules': total,
            'paid_count': paid,
            'pending_count': pending,
            'overdue_count': overdue,
            'partial_count': partial,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'remaining_amount': total_amount - paid_amount,
            'payment_rate': (paid / total * 100) if total > 0 else 0
        }
    
    @staticmethod
    def regenerate_schedule(loan_id: int) -> Tuple[bool, str]:
        """
        Régénérer l'échéancier d'un prêt
        
        Args:
            loan_id: ID du prêt
            
        Returns:
            (succès, message)
        """
        try:
            from .loan_service import LoanService
            
            loan = Loan.query.get(loan_id)
            if not loan:
                return False, "Prêt non trouvé"
            
            # Vérifier qu'il n'y a pas de paiements déjà effectués
            if loan.payments.filter_by(status='paid').count() > 0:
                return False, "Impossible de régénérer l'échéancier: des paiements existent déjà"
            
            # Supprimer l'ancien échéancier
            PaymentSchedule.query.filter_by(loan_id=loan_id).delete()
            
            # Recréer l'échéancier
            if LoanService.create_loan_schedule(loan):
                return True, "Échéancier régénéré avec succès"
            else:
                return False, "Erreur lors de la régénération"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur: {str(e)}"
