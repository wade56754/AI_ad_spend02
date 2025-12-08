#!/usr/bin/env python
"""Test Supabase database connection."""
from pathlib import Path

DATABASE_URL = "postgresql://postgres:BTsBIezNsDQF0UFp@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres"
SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / "tmp" / "db_test_result.txt"

output = []

try:
    from sqlalchemy import create_engine, text

    output.append("Connecting to Supabase PostgreSQL...")
    engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        output.append(f"SUCCESS: Connected to PostgreSQL")
        output.append(f"Version: {version[:60]}...")

        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]

        output.append(f"\nTables in public schema: {len(tables)}")
        for t in tables:
            output.append(f"  - {t}")

        if len(tables) == 0:
            output.append("\n(Database is empty - ready for schema creation)")

except Exception as e:
    output.append(f"ERROR: {type(e).__name__}: {e}")

# Ensure dir exists
OUTPUT_FILE.parent.mkdir(exist_ok=True)

# Write to file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(output))
    f.write(f"\n\nOutput written to: {OUTPUT_FILE}")

print("\n".join(output))
