#!/usr/bin/env python3
"""
Script to create admin user on Neon database.
"""
import psycopg2
from datetime import datetime

# Neon database URL from the summary
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_OHiFUPo9X0le@ep-cool-resonance-acsa3yku.sa-east-1.aws.neon.tech/neondb?sslmode=require"

# Admin user details
ADMIN_EMAIL = "kauan.massuia@sou.inteli.edu.br"
ADMIN_PASSWORD_HASH = "$2b$12$RFRtOizTJsfSeczrpvlKROLef5bSTfwWHee8Su9UxD4BQvnjh3EzK"
ADMIN_NAME = "Melhoramais"
ADMIN_FARM_ID = 1
ADMIN_ROLE = "admin"
ADMIN_ATIVO = True
CREATED_AT = datetime.now()

def create_admin_user():
    """Create admin user on Neon database if not exists."""
    conn = None
    cursor = None
    try:
        # Connect to Neon database
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id FROM silver.usuarios WHERE email = %s", (ADMIN_EMAIL,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"Admin user already exists with ID: {existing_user[0]}")
            return existing_user[0]
        else:
            print("Admin user does not exist, creating...")
        
        # Insert admin user
        insert_query = """
        INSERT INTO silver.usuarios (nome, email, senha_hash, id_farm, role, ativo, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        cursor.execute(insert_query, (
            ADMIN_NAME,
            ADMIN_EMAIL,
            ADMIN_PASSWORD_HASH,
            ADMIN_FARM_ID,
            ADMIN_ROLE,
            ADMIN_ATIVO,
            CREATED_AT
        ))
        
        new_user_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Admin user created successfully with ID: {new_user_id}")
        return new_user_id
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Creating admin user on Neon database...")
    user_id = create_admin_user()
    if user_id:
        print("✅ Admin user created/verified successfully")
    else:
        print("❌ Failed to create admin user")