"""
PostgreSQL Connection Test Script
Run this script to verify your database connection is working properly.
"""

from config import Config
from sqlalchemy import create_engine, text
import sys

def test_connection():
    """Test the PostgreSQL connection"""
    
    print("=" * 70)
    print("🔍 TESTING POSTGRESQL CONNECTION")
    print("=" * 70)
    
    # Get connection string from config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    
    # Parse connection details (for display only)
    if 'postgresql' in db_uri:
        parts = db_uri.replace('postgresql://', '').split('@')
        if len(parts) == 2:
            credentials = parts[0]
            location = parts[1]
            username = credentials.split(':')[0]
            host_port_db = location.split('/')
            host_port = host_port_db[0]
            database = host_port_db[1] if len(host_port_db) > 1 else 'unknown'
            
            print(f"\n📌 Connection Details:")
            print(f"   Username: {username}")
            print(f"   Host:Port: {host_port}")
            print(f"   Database: {database}")
    else:
        print(f"\n⚠️  Not using PostgreSQL!")
        print(f"   Current URI: {db_uri}")
        return False
    
    print("\n🔌 Attempting connection...")
    
    try:
        # Create engine and test connection
        engine = create_engine(db_uri)
        
        # Test query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            
            print("\n✅ CONNECTION SUCCESSFUL!")
            print(f"\n📊 PostgreSQL Version:")
            print(f"   {version.split(',')[0]}")
            
            # Test if database has tables
            result = connection.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """))
            table_count = result.fetchone()[0]
            
            print(f"\n📋 Database Status:")
            print(f"   Tables found: {table_count}")
            
            if table_count == 0:
                print("\n⚠️  No tables found. Run migrations:")
                print("   1. python -m flask db init")
                print("   2. python -m flask db migrate -m 'Initial migration'")
                print("   3. python -m flask db upgrade")
            else:
                print("   ✓ Database is ready!")
            
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print("\n❌ CONNECTION FAILED!")
        print(f"\n🔴 Error Details:")
        print(f"   {type(e).__name__}: {e}")
        
        print("\n" + "=" * 70)
        print("💡 TROUBLESHOOTING CHECKLIST:")
        print("=" * 70)
        print("\n1️⃣  Is PostgreSQL running?")
        print("   → Check Windows Services for 'postgresql'")
        
        print("\n2️⃣  Is the password correct?")
        print("   → Update password in config.py")
        print("   → Test with: psql -U postgres")
        
        print("\n3️⃣  Does the database exist?")
        print("   → Check with: psql -U postgres -c \"\\l\"")
        print("   → Create with: psql -U postgres -c \"CREATE DATABASE student_insight_system;\"")
        
        print("\n4️⃣  Is PostgreSQL listening on port 5432?")
        print("   → Check with: netstat -an | findstr 5432")
        
        print("\n5️⃣  Firewall blocking connection?")
        print("   → Temporarily disable to test")
        
        print("\n" + "=" * 70)
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
