"""
Initialize database tables on Neon PostgreSQL.
Run this before starting the backend.
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.models import Base
from core.config import get_settings

settings = get_settings()

print("=" * 60)
print("🚀 Carthage Alpha - Database Initialization")
print("=" * 60)
print(f"\n📡 Connecting to Neon PostgreSQL...")
print(f"Host: ep-shy-breeze-ag2f4327-pooler.c-2.eu-central-1.aws.neon.tech")
print(f"Database: neondb\n")

try:
    # Create engine (psycopg3)
    db_url = settings.database_url.replace('postgresql://', 'postgresql+psycopg://')
    engine = create_engine(db_url, pool_pre_ping=True, echo=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"PostgreSQL: {version.split(',')[0]}\n")
    
    # Create all tables
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!\n")
    
    # List created tables
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = result.fetchall()
        
        print(f"📊 Database tables ({len(tables)}):")
        for table in tables:
            # Get row count
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]};"))
            count = count_result.fetchone()[0]
            print(f"  ✓ {table[0]:<25} ({count} rows)")
    
    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Load historical data: python scripts/load_data.py")
    print("2. Start backend: uvicorn main:app --reload")
    print("3. Access API docs: http://localhost:8000/docs\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("- Database credentials in .env file")
    print("- Network connection to Neon")
    print("- SSL requirements (sslmode=require)")
    sys.exit(1)
