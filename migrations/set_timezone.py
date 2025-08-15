"""
Migration script to set database timezone to IST
Run this script to ensure all timestamps are stored in Indian Standard Time
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SQLALCHEMY_DATABASE_URL

def set_database_timezone():
    """
    Set the database timezone to IST (Asia/Kolkata)
    """
    try:
        # Create engine
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        with engine.connect() as connection:
            # Set timezone to IST
            connection.execute(text("SET timezone = 'Asia/Kolkata';"))
            connection.commit()
            
            # Verify the timezone setting
            result = connection.execute(text("SHOW timezone;"))
            current_timezone = result.fetchone()[0]
            
            print(f"✅ Database timezone set to: {current_timezone}")
            
            # Test current timestamp
            result = connection.execute(text("SELECT NOW();"))
            current_time = result.fetchone()[0]
            print(f"✅ Current database time: {current_time}")
            
    except Exception as e:
        print(f"❌ Error setting timezone: {e}")
        return False
    
    return True

def update_existing_timestamps():
    """
    Update existing timestamp columns to use IST timezone
    Note: This is a destructive operation and should be used carefully
    """
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        with engine.connect() as connection:
            # Update event_registrations table
            connection.execute(text("""
                UPDATE event_registrations 
                SET created_at = created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
                WHERE created_at IS NOT NULL;
            """))
            
            # Update user_registrations table
            connection.execute(text("""
                UPDATE user_registrations 
                SET created_at = created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata',
                    updated_at = updated_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
                WHERE created_at IS NOT NULL;
            """))
            
            # Update transactions table
            connection.execute(text("""
                UPDATE transactions 
                SET created_at = created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'
                WHERE created_at IS NOT NULL;
            """))
            
            connection.commit()
            print("✅ Existing timestamps updated to IST")
            
    except Exception as e:
        print(f"❌ Error updating timestamps: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🕐 Setting database timezone to IST...")
    
    if set_database_timezone():
        print("\n🔄 Updating existing timestamps to IST...")
        update_existing_timestamps()
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
