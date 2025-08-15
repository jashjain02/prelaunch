"""
Migration script to create Jindal registrations table
Run this script to create the jindal_registrations table
"""

import os
import sys
from sqlalchemy import text

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import engine

def create_jindal_table():
    """
    Create the jindal_registrations table
    """
    try:
        with engine.connect() as connection:
            # Create jindal_registrations table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS jindal_registrations (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL UNIQUE,
                phone VARCHAR(15) NOT NULL,
                jgu_student_id VARCHAR(50) NOT NULL UNIQUE,
                city VARCHAR(100) NOT NULL,
                state VARCHAR(100) NOT NULL,
                selected_sports TEXT,
                pickle_level VARCHAR(50),
                total_amount INTEGER NOT NULL DEFAULT 0,
                payment_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                payment_proof VARCHAR(500),
                agreed_to_terms BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            connection.execute(text(create_table_sql))
            connection.commit()
            
            print("✅ Successfully created jindal_registrations table!")
            
            # Create indexes for better performance
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_jindal_email ON jindal_registrations(email);",
                "CREATE INDEX IF NOT EXISTS idx_jindal_jgu_id ON jindal_registrations(jgu_student_id);",
                "CREATE INDEX IF NOT EXISTS idx_jindal_payment_status ON jindal_registrations(payment_status);",
                "CREATE INDEX IF NOT EXISTS idx_jindal_created_at ON jindal_registrations(created_at);"
            ]
            
            for index_sql in indexes_sql:
                connection.execute(text(index_sql))
            
            connection.commit()
            print("✅ Successfully created indexes for jindal_registrations table!")
            
    except Exception as e:
        print(f"❌ Error creating jindal_registrations table: {e}")
        raise

def drop_jindal_table():
    """
    Drop the jindal_registrations table (use with caution!)
    """
    try:
        with engine.connect() as connection:
            drop_table_sql = "DROP TABLE IF EXISTS jindal_registrations CASCADE;"
            connection.execute(text(drop_table_sql))
            connection.commit()
            print("✅ Successfully dropped jindal_registrations table!")
            
    except Exception as e:
        print(f"❌ Error dropping jindal_registrations table: {e}")
        raise

if __name__ == "__main__":
    print("🏗️ Creating Jindal registrations table...")
    create_jindal_table()
    print("\n🎉 Jindal registrations table migration completed!")
    
    # Uncomment the line below if you need to drop the table
    # drop_jindal_table()
