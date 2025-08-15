from models.crude_operations_model import CrudeOperationsModel
from models.jindal_registration_model import JindalRegistrationModel
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)

class JindalRegistrationConnector(CrudeOperationsModel[JindalRegistrationModel, None, None]):
    def __init__(self):
        super().__init__(JindalRegistrationModel)

    def create_registration(self, db: Session, registration_data: dict) -> JindalRegistrationModel:
        """
        Create a new Jindal registration with proper data handling
        """
        # Convert selected_sports list to JSON string if provided
        if 'selected_sports' in registration_data and isinstance(registration_data['selected_sports'], list):
            registration_data['selected_sports'] = json.dumps(registration_data['selected_sports'])
        
        registration = JindalRegistrationModel(**registration_data)
        db.add(registration)
        db.commit()
        db.refresh(registration)
        
        logger.info(f"Created Jindal registration for {registration.first_name} {registration.last_name}")
        return registration

    def get_by_email(self, db: Session, email: str) -> Optional[JindalRegistrationModel]:
        """Get registration by email"""
        return db.query(JindalRegistrationModel).filter_by(email=email).first()

    def get_by_jgu_id(self, db: Session, jgu_student_id: str) -> Optional[JindalRegistrationModel]:
        """Get registration by JGU Student ID"""
        return db.query(JindalRegistrationModel).filter_by(jgu_student_id=jgu_student_id).first()

    def get_by_payment_status(self, db: Session, payment_status: str) -> List[JindalRegistrationModel]:
        """Get registrations by payment status"""
        return db.query(JindalRegistrationModel).filter_by(payment_status=payment_status).all()

    def update_payment_status(self, db: Session, registration_id: int, payment_status: str, payment_proof: str = None) -> Optional[JindalRegistrationModel]:
        """Update payment status and proof"""
        registration = db.query(JindalRegistrationModel).filter_by(id=registration_id).first()
        if registration:
            registration.payment_status = payment_status
            if payment_proof:
                registration.payment_proof = payment_proof
            db.commit()
            db.refresh(registration)
            logger.info(f"Updated payment status for registration {registration_id} to {payment_status}")
        return registration

    def get_registrations_summary(self, db: Session) -> dict:
        """Get summary of all registrations"""
        total_registrations = db.query(JindalRegistrationModel).count()
        pending_payments = db.query(JindalRegistrationModel).filter_by(payment_status="pending").count()
        completed_payments = db.query(JindalRegistrationModel).filter_by(payment_status="completed").count()
        failed_payments = db.query(JindalRegistrationModel).filter_by(payment_status="failed").count()
        
        # Calculate total revenue
        total_revenue = db.query(JindalRegistrationModel).filter_by(payment_status="completed").with_entities(
            db.func.sum(JindalRegistrationModel.total_amount)
        ).scalar() or 0
        
        return {
            "total_registrations": total_registrations,
            "pending_payments": pending_payments,
            "completed_payments": completed_payments,
            "failed_payments": failed_payments,
            "total_revenue": total_revenue
        }

    def get_registration_with_sports(self, db: Session, registration_id: int) -> Optional[dict]:
        """Get registration with parsed sports data"""
        registration = db.query(JindalRegistrationModel).filter_by(id=registration_id).first()
        if registration:
            registration_dict = {
                "id": registration.id,
                "first_name": registration.first_name,
                "last_name": registration.last_name,
                "email": registration.email,
                "phone": registration.phone,
                "jgu_student_id": registration.jgu_student_id,
                "city": registration.city,
                "state": registration.state,
                "selected_sports": json.loads(registration.selected_sports) if registration.selected_sports else [],
                "pickle_level": registration.pickle_level,
                "total_amount": registration.total_amount,
                "payment_status": registration.payment_status,
                "payment_proof": registration.payment_proof,
                "agreed_to_terms": registration.agreed_to_terms,
                "created_at": registration.created_at,
                "updated_at": registration.updated_at
            }
            return registration_dict
        return None

jindal_registration_connector = JindalRegistrationConnector()
