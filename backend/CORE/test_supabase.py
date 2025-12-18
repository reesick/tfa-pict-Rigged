"""Test Supabase connection."""
import os

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv(override=True)  # Override any existing env vars

# Reset cached settings to pick up new env
from app.config import reset_settings, get_settings
reset_settings()

settings = get_settings()
print(f"Supabase configured: {settings.is_supabase_configured}")
print(f"Database URL: {settings.database_url[:60]}...")
print(f"Embedding dim: {settings.embedding_dimension}")

# Test PostgreSQL connection
from app.database import reset_engine, get_engine
reset_engine()  # Reset cached engine

engine = get_engine()
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT current_database(), version()"))
    row = result.fetchone()
    print(f"\n✅ Connected to: {row[0]}")
    print(f"PostgreSQL: {row[1][:60]}...")
    
    # Check tables
    result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
    tables = [r[0] for r in result.fetchall()]
    print(f"\nTables ({len(tables)}):")
    for t in tables:
        print(f"  ✓ {t}")
