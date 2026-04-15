from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple
from app import db
from app.models.loan import Loan, LoanType, RepaymentFrequency
from app.models.schedule import PaymentSchedule
from .schedule_service import ScheduleService

class LoanService:
    """Service pour la gestion des prêts et calculs associés"""
    
    @staticmethod
    def calculate_loan_schedule(loan: Loan) -> List[Dict]:
        """
        Calculer l'échéancier de remboursement pour un prêt
        
        Args:
            loan: Objet prêt avec les paramètres
            
        Returns:
            Liste des échéances avec détails
        """
        if not loan.amount or not loan.interest_rate or not loan.duration_months:
            raise ValueError("Paramètres de prêt incomplets")
        
        # Calcul du montant total dû (capital + intérêts)
        principal = float(loan.amount)
        annual_rate = float(loan.interest_rate)
        months = loan.duration_months
        
        # Intérêt simple sur toute la durée
        total_interest = principal * (annual_rate / 100) * (months / 12)
        total_amount = principal + total_interest
        
        # Déterminer le nombre d'échéances selon la fréquence
        if loan.repayment_frequency == RepaymentFrequency.DAILY:
            installments = months * 30
        elif loan.repayment_frequency == RepaymentFrequency.WEEKLY:
            installments = months * 4
        else:  # MONTHLY
            installments = months
        
        # Calcul du montant par échéance
        installment_amount = total_amount / installments
        
        # Génération des échéances
        schedules = []
        current_date = loan.first_payment_date or date.today()
        
        for i in range(1, installments + 1):
            # Calcul de la date d'échéance
            if loan.repayment_frequency == RepaymentFrequency.DAILY:
                due_date = current_date + timedelta(days=i-1)
            elif loan.repayment_frequency == RepaymentFrequency.WEEKLY:
                due_date = current_date + timedelta(weeks=i-1)
            else:  # MONTHLY
                due_date = current_date + timedelta(days=30*(i-1))
            
            # Répartition principal/intérêt (amortissement simple)
            principal_part = principal / installments
            interest_part = total_interest / installments
            
            # Solde restant après cette échéance
            balance_after = total_amount - (installment_amount * i)
            
            schedule = {
                'installment_number': i,
                'due_date': due_date,
                'principal_amount': round(principal_part, 2),
                'interest_amount': round(interest_part, 2),
                'total_amount': round(installment_amount, 2),
                'balance_after': round(max(0, balance_after), 2)
            }
            schedules.append(schedule)
        
        return schedules
    
    @staticmethod
    def create_loan_schedule(loan: Loan) -> bool:
        """
        Créer les échéances en base de données pour un prêt
        
        Args:
            loan: Objet prêt approuvé
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Supprimer les anciennes échéances si existantes
            PaymentSchedule.query.filter_by(loan_id=loan.id).delete()
            
            # Calculer les nouvelles échéances
            schedules_data = LoanService.calculate_loan_schedule(loan)
            
            # Créer les enregistrements
            for schedule_data in schedules_data:
                schedule = PaymentSchedule(
                    loan_id=loan.id,
                    installment_number=schedule_data['installment_number'],
                    due_date=schedule_data['due_date'],
                    principal_amount=schedule_data['principal_amount'],
                    interest_amount=schedule_data['interest_amount'],
                    total_amount=schedule_data['total_amount'],
                    balance_after=schedule_data['balance_after']
                )
                db.session.add(schedule)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la création de l'échéancier: {e}")
            return False
    
    @staticmethod
    def approve_loan(loan_id: int, approved_by: int) -> Tuple[bool, str]:
        """
        Approuver un prêt et générer l'échéancier
        
        Args:
            loan_id: ID du prêt
            approved_by: ID de l'utilisateur qui approuve
            
        Returns:
            (succès, message)
        """
        try:
            loan = Loan.query.get(loan_id)
            if not loan:
                return False, "Prêt non trouvé"
            
            if loan.status != 'pending':
                return False, "Le prêt n'est pas en attente"
            
            # Mise à jour du statut
            loan.status = 'approved'
            loan.approved_by = approved_by
            loan.approved_at = datetime.utcnow()
            
            # Définir les dates si non définies
            if not loan.disbursement_date:
                loan.disbursement_date = date.today()
            
            if not loan.first_payment_date:
                # Premier paiement 7 jours après déboursement
                loan.first_payment_date = loan.disbursement_date + timedelta(days=7)
            
            # Calculer la date d'échéance finale
            schedules = LoanService.calculate_loan_schedule(loan)
            if schedules:
                loan.maturity_date = schedules[-1]['due_date']
            
            # Créer l'échéancier
            if LoanService.create_loan_schedule(loan):
                db.session.commit()
                return True, "Prêt approuvé avec succès"
            else:
                return False, "Erreur lors de la création de l'échéancier"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur: {str(e)}"
    
    @staticmethod
    def get_loan_summary(loan_id: int) -> Dict:
        """
        Obtenir un résumé complet d'un prêt
        
        Args:
            loan_id: ID du prêt
            
        Returns:
            Dictionnaire avec les informations du prêt
        """
        loan = Loan.query.get(loan_id)
        if not loan:
            return {}
        
        # Statistiques des paiements
        total_paid = sum(p.amount for p in loan.payments if p.status == 'paid')
        pending_schedules = loan.schedules.filter_by(status='pending').count()
        overdue_schedules = loan.schedules.filter_by(status='overdue').count()
        
        return {
            'loan': loan,
            'total_paid': float(total_paid),
            'outstanding_balance': loan.outstanding_balance,
            'next_payment': loan.schedules.filter_by(status='pending').first(),
            'pending_count': pending_schedules,
            'overdue_count': overdue_schedules,
            'is_overdue': loan.is_overdue,
            'overdue_days': loan.overdue_days
        }
