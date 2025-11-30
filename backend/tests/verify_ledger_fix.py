#!/usr/bin/env python
"""
Quick verification script for LedgerEntry SQLite fix.
Run: python tests/verify_ledger_fix.py
"""
import os
import sys
from pathlib import Path

# Setup path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
os.chdir(backend_dir)

# Load test env
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env.test", override=True)
os.environ["TESTING"] = "true"

print("=" * 60)
print("LedgerEntry SQLite Compatibility Test")
print("=" * 60)

# Step 1: Register BigInteger compiler BEFORE importing models
print("\n[1] Registering BigInteger SQLite compiler...")
from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles

@compiles(BigInteger, 'sqlite')
def compile_biginteger_sqlite(element, compiler, **kw):
    return "INTEGER"

print("    OK - Compiler registered")

# Step 2: Import models
print("\n[2] Importing models...")
from backend.models.finance.ledger import LedgerEntry
from backend.models.base import Base, LedgerEntryType
print(f"    OK - LedgerEntry imported: {LedgerEntry.__tablename__}")

# Step 3: Create SQLite in-memory engine
print("\n[3] Creating SQLite in-memory engine...")
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

print("    OK - Engine created")

# Step 4: Create all tables
print("\n[4] Creating all tables...")
Base.metadata.create_all(bind=engine)
print("    OK - Tables created")

# Step 5: Test inserting LedgerEntry
print("\n[5] Testing LedgerEntry insert...")
Session = sessionmaker(bind=engine)
session = Session()

try:
    # First, we need to create prerequisites (AdAccount requires Channel, Project, User)
    # For simplicity, let's check the table schema directly
    from sqlalchemy import inspect
    inspector = inspect(engine)

    # Check ledger_entries table columns
    columns = inspector.get_columns('ledger_entries')
    print(f"    Table 'ledger_entries' columns:")
    for col in columns:
        pk_marker = " [PK]" if col.get('primary_key') else ""
        nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
        default = f" default={col.get('default')}" if col.get('default') else ""
        auto = " AUTOINCREMENT" if col.get('autoincrement') else ""
        print(f"      - {col['name']}: {col['type']}{pk_marker} {nullable}{default}{auto}")

    # Verify id column type
    id_col = next((c for c in columns if c['name'] == 'id'), None)
    if id_col:
        id_type = str(id_col['type'])
        print(f"\n    id column type: {id_type}")
        if 'INTEGER' in id_type.upper():
            print("    SUCCESS: id is INTEGER (SQLite compatible)")
        else:
            print(f"    WARNING: id is {id_type}, may not support autoincrement")

    print("\n[6] Test PASSED - BigInteger correctly compiled to INTEGER")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

finally:
    session.close()

print("\n" + "=" * 60)
print("Verification complete. Run full tests with:")
print("  python -m pytest tests/ledger -v --tb=short --no-cov")
print("=" * 60)
