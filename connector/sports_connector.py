from models.crude_operations_model import CrudeOperationsModel
from models.sports_model import SportsModel
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class SportsConnector(CrudeOperationsModel[SportsModel, None, None]):
    def __init__(self):
        super().__init__(SportsModel)

    def get_by_sport_key(self, db: Session, sport_key: str) -> Optional[SportsModel]:
        """Get sport by sport_key"""
        return db.query(SportsModel).filter_by(sport_key=sport_key).first()

    def get_available_sports(self, db: Session) -> List[SportsModel]:
        """Get all available sports"""
        return db.query(SportsModel).filter_by(is_active=True, is_sold_out=False).all()

    def get_sold_out_sports(self, db: Session) -> List[SportsModel]:
        """Get all sold out sports"""
        return db.query(SportsModel).filter_by(is_sold_out=True).all()

    def purchase_tickets(self, db: Session, sport_key: str, quantity: int = 1) -> tuple[bool, str, Optional[SportsModel]]:
        """
        Purchase tickets for a sport
        Returns: (success, message, sport_object)
        """
        sport = self.get_by_sport_key(db, sport_key)
        
        if not sport:
            return False, f"Sport '{sport_key}' not found", None
        
        if not sport.is_active:
            return False, f"{sport.sport_name} is currently inactive", sport
        
        if sport.is_sold_out:
            return False, f"{sport.sport_name} is sold out", sport
        
        if sport.current_count + quantity > sport.max_capacity:
            return False, f"Only {sport.remaining_tickets} tickets remaining for {sport.sport_name}", sport
        
        # Increment count
        if sport.increment_count(quantity):
            db.commit()
            logger.info(f"Purchased {quantity} tickets for {sport.sport_name}. New count: {sport.current_count}")
            return True, f"Successfully purchased {quantity} ticket(s) for {sport.sport_name}", sport
        else:
            return False, f"Failed to purchase tickets for {sport.sport_name}", sport

    def refund_tickets(self, db: Session, sport_key: str, quantity: int = 1) -> tuple[bool, str, Optional[SportsModel]]:
        """
        Refund tickets for a sport
        Returns: (success, message, sport_object)
        """
        sport = self.get_by_sport_key(db, sport_key)
        
        if not sport:
            return False, f"Sport '{sport_key}' not found", None
        
        if sport.current_count - quantity < 0:
            return False, f"Cannot refund {quantity} tickets. Only {sport.current_count} tickets sold", sport
        
        # Decrement count
        if sport.decrement_count(quantity):
            db.commit()
            logger.info(f"Refunded {quantity} tickets for {sport.sport_name}. New count: {sport.current_count}")
            return True, f"Successfully refunded {quantity} ticket(s) for {sport.sport_name}", sport
        else:
            return False, f"Failed to refund tickets for {sport.sport_name}", sport

    def reset_sport_count(self, db: Session, sport_key: str) -> tuple[bool, str, Optional[SportsModel]]:
        """
        Reset ticket count for a sport (admin function)
        Returns: (success, message, sport_object)
        """
        sport = self.get_by_sport_key(db, sport_key)
        
        if not sport:
            return False, f"Sport '{sport_key}' not found", None
        
        sport.reset_count()
        db.commit()
        logger.info(f"Reset ticket count for {sport.sport_name}")
        return True, f"Successfully reset ticket count for {sport.sport_name}", sport

    def update_capacity(self, db: Session, sport_key: str, new_capacity: int) -> tuple[bool, str, Optional[SportsModel]]:
        """
        Update capacity for a sport (admin function)
        Returns: (success, message, sport_object)
        """
        sport = self.get_by_sport_key(db, sport_key)
        
        if not sport:
            return False, f"Sport '{sport_key}' not found", None
        
        if new_capacity <= 0:
            return False, "Capacity must be greater than 0", sport
        
        sport.set_capacity(new_capacity)
        db.commit()
        logger.info(f"Updated capacity for {sport.sport_name} to {new_capacity}")
        return True, f"Successfully updated capacity for {sport.sport_name} to {new_capacity}", sport

    def get_sports_summary(self, db: Session) -> dict:
        """Get summary of all sports"""
        all_sports = db.query(SportsModel).all()
        available_sports = [s for s in all_sports if s.is_available]
        sold_out_sports = [s for s in all_sports if s.is_sold_out]
        
        return {
            "total_sports": len(all_sports),
            "available_sports": len(available_sports),
            "sold_out_sports": len(sold_out_sports),
            "total_tickets_sold": sum(s.current_count for s in all_sports),
            "total_capacity": sum(s.max_capacity for s in all_sports)
        }

sports_connector = SportsConnector()
