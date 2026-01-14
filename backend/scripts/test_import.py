"""测试导入脚本"""
import sys
import os

# 输出到文件
output_file = os.path.join(os.path.dirname(__file__), "test_output.txt")
f = open(output_file, "w", encoding="utf-8")


def log(msg):
    f.write(msg + "\n")
    f.flush()


log("Starting test...")

# 添加项目根目录到 Python 路径 (backend 的父目录)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)
log(f"Project root: {project_root}")
log(f"Backend dir: {backend_dir}")

try:
    log("Testing backend.core.config...")
    from backend.core.config import get_settings

    log("✓ backend.core.config imported")
except Exception as e:
    log(f"✗ backend.core.config failed: {e}")

try:
    log("Testing backend.models.core.project...")
    from backend.models.core.project import Project

    log("✓ backend.models.core.project imported")
except Exception as e:
    log(f"✗ backend.models.core.project failed: {e}")

try:
    log("Testing backend.models.ledger...")
    from backend.models.ledger import LedgerTransaction

    log("✓ backend.models.ledger imported")
except Exception as e:
    log(f"✗ backend.models.ledger failed: {e}")

try:
    log("Getting settings...")
    settings = get_settings()
    log(f"✓ DB URL: {settings.database_url[:60]}...")
except Exception as e:
    log(f"✗ Settings failed: {e}")

try:
    log("Testing DB connection...")
    from sqlalchemy import create_engine, text

    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT count(*) FROM projects"))
        count = result.scalar()
        log(f"✓ Projects count: {count}")
except Exception as e:
    log(f"✗ DB connection failed: {e}")

try:
    log("Testing CSV file...")
    csv_path = r"d:\Backup\Downloads\收支表 - 明细表 (1).csv"
    if os.path.exists(csv_path):
        log(f"✓ CSV exists: {csv_path}")
    else:
        log(f"✗ CSV not found: {csv_path}")
except Exception as e:
    log(f"✗ CSV check failed: {e}")

log("Done!")
f.close()
