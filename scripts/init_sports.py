"""
Initialize sports table with default sports
Run this script to set up the initial sports data
"""

import os
import sys
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from models.sports_model import SportsModel

def init_sports():
    """
    Initialize the sports table with default sports
    """
    db = SessionLocal()
    
    try:
        # Check if sports already exist
        existing_sports = db.query(SportsModel).count()
        if existing_sports > 0:
            print(f"✅ Sports table already has {existing_sports} sports. Skipping initialization.")
            return
        
        # Default sports data
        default_sports = [
            {
                "sport_name": "Padel",
                "sport_key": "padel",
                "description": "Fun padel games for all skill levels.",
                "price": 200,
                "max_capacity": 500,  # Available for booking
                "timing": None,  # No timing display
                "is_active": True,
                "is_sold_out": False
            }
        ]
        
        # Create sports
        for sport_data in default_sports:
            sport = SportsModel(**sport_data)
            db.add(sport)
            print(f"➕ Adding sport: {sport_data['sport_name']} (₹{sport_data['price']}) - Capacity: {sport_data['max_capacity']}")
        
        db.commit()
        print(f"✅ Successfully initialized {len(default_sports)} sports!")
        
        # Display summary
        print("\n📊 Sports Summary:")
        sports = db.query(SportsModel).all()
        for sport in sports:
            status = "🟢 Available" if sport.is_available else "🔴 Sold Out" if sport.is_sold_out else "⚫ Inactive"
            print(f"  • {sport.sport_name}: ₹{sport.price} - {sport.current_count}/{sport.max_capacity} - {status}")
        
    except Exception as e:
        print(f"❌ Error initializing sports: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def update_sport_capacity(sport_key: str, new_capacity: int):
    """
    Update capacity for a specific sport
    """
    db = SessionLocal()
    
    try:
        sport = db.query(SportsModel).filter_by(sport_key=sport_key).first()
        if not sport:
            print(f"❌ Sport '{sport_key}' not found")
            return
        
        old_capacity = sport.max_capacity
        sport.set_capacity(new_capacity)
        db.commit()
        
        print(f"✅ Updated {sport.sport_name} capacity: {old_capacity} → {new_capacity}")
        
    except Exception as e:
        print(f"❌ Error updating capacity: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🏃‍♂️ Initializing sports table...")
    init_sports()
    
    # Example: Update padel capacity if needed
    # update_sport_capacity("padel", 30)
    
    print("\n🎉 Sports initialization completed!")
