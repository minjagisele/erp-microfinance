from datetime import datetime, date
from decimal import Decimal
from typing import Tuple, List, Dict
from app import db
from app.models.payment import Payment
from app.models.loan import Loan
from app.models.schedule import PaymentSchedule

class PaymentService:
    """Service pour la gestion des paiements et remboursements"""
    
    @staticmethod
    def process_payment(loan_id: int, amount: float, payment_method: str = 'cash', 
                       notes: str = None, created_by: int = None) -> Tuple[bool, str, Payment]:
        """
        Traiter un paiement pour un prêt
        
        Args:
            loan_id: ID du prêt
            amount: Montant du paiement
            payment_method: Méthode de paiement
            notes: Notes sur le paiement
            created_by: ID de l'utilisateur qui enregistre
            
        Returns:
            (succès, message, paiement)
        """
        try:
            loan = Loan.query.get(loan_id)
            if not loan:
                return False, "Prêt non trouvé", None
            
            if loan.status != 'approved':
                return False, "Le prêt n'est pas approuvé", None
            
            if amount <= 0:
                return False, "Le montant doit être positif", None
            
            # Générer un code de paiement
            payment_code = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Créer le paiement
            payment = Payment(
                code=payment_code,
                loan_id=loan_id,
                amount=amount,
                payment_method=payment_method,
                notes=notes,
                created_by=created_by or 1
            )
            
            # Appliquer le paiement aux échéances
            remaining_amount = amount
            pending_schedules = PaymentSchedule.query.filter_by(
                loan_id=loan_id, 
                status='pending'
            ).order_by(PaymentSchedule.due_date).all()
            
            if not pending_schedules:
                return False, "Aucune échéance en attente", None
            
            for schedule in pending_schedules:
                if remaining_amount <= 0:
                    break
                
                if schedule.remaining_amount <= remaining_amount:
                    # Payer complètement cette échéance
                    schedule.mark_as_paid(schedule.remaining_amount, date.today())
                    payment.schedule_id = schedule.id
                    remaining_amount -= float(schedule.remaining_amount)
                else:
                    # Paiement partiel de cette échéance
                    schedule.paid_amount += remaining_amount
                    schedule.status = 'partial'
                    payment.schedule_id = schedule.id
                    remaining_amount = 0
            
            # Sauvegarder
            db.session.add(payment)
            db.session.commit()
            
            # Vérifier si le prêt est complètement remboursé
            PaymentService._check_loan_completion(loan)
            
            return True, "Paiement enregistré avec succès", payment
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors du paiement: {str(e)}", None
    
    @staticmethod
    def _check_loan_completion(loan: Loan):
        """Vérifier si un prêt est complètement remboursé"""
        all_schedules = PaymentSchedule.query.filter_by(loan_id=loan.id).all()
        
        if all(schedule.status in ['paid', 'partial'] for schedule in all_schedules):
            loan.status = 'completed'
            db.session.commit()
    
    @staticmethod
    def get_payment_history(loan_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """
        Obtenir l'historique des paiements pour un prêt
        
        Args:
            loan_id: ID du prêt
            page: Page pour la pagination
            per_page: Nombre par page
            
        Returns:
            Dictionnaire avec les paiements et pagination
        """
        payments = Payment.query.filter_by(loan_id=loan_id)\
                               .order_by(Payment.payment_date.desc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'payments': payments.items,
            'total': payments.total,
            'pages': payments.pages,
            'current_page': payments.page,
            'has_next': payments.has_next,
            'has_prev': payments.has_prev
        }
    
    @staticmethod
    def get_overdue_payments() -> List[Dict]:
        """
        Obtenir la liste des paiements en retard
        
        Returns:
            Liste des prêts avec échéances en retard
        """
        overdue_schedules = db.session.query(PaymentSchedule, Loan)\
            .join(Loan, PaymentSchedule.loan_id == Loan.id)\
            .filter(
                PaymentSchedule.status == 'pending',
                PaymentSchedule.due_date < date.today(),
                Loan.status == 'approved'
            )\
            .order_by(PaymentSchedule.due_date)\
            .all()
        
        result = []
        for schedule, loan in overdue_schedules:
            result.append({
                'schedule': schedule,
                'loan': loan,
                'client': loan.client,
                'overdue_days': schedule.overdue_days,
                'overdue_amount': float(schedule.remaining_amount)
            })
        
        return result
    
    @staticmethod
    def generate_payment_reminders(days_before: int = 3) -> List[Dict]:
        """
        Générer la liste des rappels de paiement
        
        Args:
            days_before: Jours avant échéance pour le rappel
            
        Returns:
            Liste des échéances à venir
        """
        reminder_date = date.today() + timedelta(days=days_before)
        
        upcoming_schedules = db.session.query(PaymentSchedule, Loan)\
            .join(Loan, PaymentSchedule.loan_id == Loan.id)\
            .filter(
                PaymentSchedule.status == 'pending',
                PaymentSchedule.due_date <= reminder_date,
                PaymentSchedule.due_date >= date.today(),
                Loan.status == 'approved'
            )\
            .order_by(PaymentSchedule.due_date)\
            .all()
        
        result = []
        for schedule, loan in upcoming_schedules:
            result.append({
                'schedule': schedule,
                'loan': loan,
                'client': loan.client,
                'days_until_due': (schedule.due_date - date.today()).days,
                'amount_due': float(schedule.remaining_amount)
            })
        
        return result
    
    @staticmethod
    def cancel_payment(payment_id: int, reason: str = None) -> Tuple[bool, str]:
        """
        Annuler un paiement
        
        Args:
            payment_id: ID du paiement
            reason: Raison de l'annulation
            
        Returns:
            (succès, message)
        """
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                return False, "Paiement non trouvé"
            
            if payment.status != 'paid':
                return False, "Le paiement n'est pas en statut payé"
            
            # Remettre à jour les échéances associées
            if payment.schedule:
                schedule = payment.schedule
                schedule.paid_amount -= payment.amount
                if schedule.paid_amount <= 0:
                    schedule.status = 'pending'
                    schedule.paid_amount = 0
                    schedule.paid_date = None
                else:
                    schedule.status = 'partial'
            
            # Mettre à jour le statut du prêt si nécessaire
            loan = payment.loan
            if loan.status == 'completed':
                loan.status = 'approved'
            
            # Annuler le paiement
            payment.status = 'cancelled'
            payment.notes = f"ANNULÉ: {reason or 'Aucune raison spécifiée'}"
            
            db.session.commit()
            return True, "Paiement annulé avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'annulation: {str(e)}"
