#!/usr/bin/env python3
"""
Test script to verify admin user exists and password hash is correct.
"""
import psycopg2
import bcrypt

# Neon database URL
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_OHiFUPo9X0le@ep-cool-resonance-acsa3yku.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def test_admin_user():
    """Test admin user in Neon database."""
    conn = None
    cursor = None
    try:
        # Connect to Neon database
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cursor = conn.cursor()
        
        # Get admin user
        cursor.execute("SELECT id, nome, email, senha_hash, ativo FROM silver.usuarios WHERE email = %s", 
                      ("kauan.massuia@sou.inteli.edu.br",))
        user = cursor.fetchone()
        
        if not user:
            print("❌ Admin user not found in database")
            return False
            
        user_id, nome, email, senha_hash, ativo = user
        print(f"✅ Admin user found:")
        print(f"   ID: {user_id}")
        print(f"   Name: {nome}")
        print(f"   Email: {email}")
        print(f"   Active: {ativo}")
        print(f"   Password hash: {senha_hash[:50]}...")
        
        # Test password verification
        test_password = "123456"
        try:
            is_valid = bcrypt.checkpw(test_password.encode("utf-8"), senha_hash.encode("utf-8"))
            print(f"   Password '{test_password}' valid: {is_valid}")
            
            if not is_valid:
                print("❌ Password verification failed!")
                # Try to generate a new hash for comparison
                new_hash = bcrypt.hashpw(test_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                print(f"   New hash for '{test_password}': {new_hash}")
                return False
            else:
                print("✅ Password verification successful!")
                return True
        except Exception as e:
            print(f"❌ Error verifying password: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Testing admin user in Neon database...")
    success = test_admin_user()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")