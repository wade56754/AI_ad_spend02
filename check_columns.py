"""Quick check for fulfillment columns in projects table"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text

# Get database URL from environment or use default
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:dI3YqJj1ZbC3IO4C@db.jzmcoivxhiyidizncyaq.supabase.co:5432/postgres",
)

engine = create_engine(database_url)
inspector = inspect(engine)

print("=== Projects Table Columns ===")
columns = inspector.get_columns("projects")
fulfillment_cols = [
    c for c in columns if "fulfillment" in c["name"] or c["name"] == "fulfilled_at"
]

if fulfillment_cols:
    print("\nFulfillment columns found:")
    for c in fulfillment_cols:
        print(
            f"  - {c['name']}: {c['type']} (nullable={c['nullable']}, default={c.get('default', 'None')})"
        )
else:
    print("\nNo fulfillment columns found!")
    print("\nAll columns:")
    for c in columns:
        print(f"  - {c['name']}")
