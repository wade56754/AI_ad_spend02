# Backend Test Environment Setup Guide

> **Version**: 1.0
> **Aligned Documents**: LEDGER_SOT.md v1.1, STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Option 1: Windows batch file (recommended)
run_ledger_tests.bat

# Option 2: Python script
python tests/ledger/run_ledger_tests.py -v

# Option 3: Direct pytest
python -m pytest tests/ledger -v --tb=short --no-cov
```

## Prerequisites

### 1. Python Environment

- **Python**: 3.9+
- **Package Manager**: pip or conda

```bash
# Check Python version
python --version
```

### 2. Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# Or install test dependencies only
pip install pytest pytest-asyncio pytest-cov pytest-mock sqlalchemy>=2.0.0
```

### 3. Environment Configuration

The test environment uses `.env.test` configuration file. Key settings:

```env
# .env.test (already exists)
ENVIRONMENT=test
DATABASE_URL=sqlite:///./ai_ad_spend_unit.db
TESTING=true
```

## Test Architecture

### Directory Structure

```
backend/tests/
├── conftest.py              # Shared fixtures and SQLite compatibility
├── ledger/
│   ├── test_ledger_service.py      # LedgerEntry CRUD and Service tests
│   ├── test_ledger_invariants.py   # LEDGER_SOT invariant validation
│   └── run_ledger_tests.py         # Module-specific test runner
├── daily_reports/
├── topups/
├── reconciliation/
└── README.md                # This file
```

### SQLite Compatibility

The test environment uses SQLite in-memory database for speed and isolation. Key compatibility features in `conftest.py`:

1. **BigInteger → INTEGER Compilation**:
   ```python
   @compiles(BigInteger, 'sqlite')
   def compile_biginteger_sqlite(element, compiler, **kw):
       return "INTEGER"  # SQLite only supports INTEGER for autoincrement
   ```

2. **UUID → CHAR(36) Mapping**:
   ```python
   class GUID(TypeDecorator):
       # Maps PostgreSQL UUID to SQLite CHAR(36)
   ```

3. **JSONB → JSON Mapping**:
   ```python
   class JSONBCompat(TypeDecorator):
       # Maps PostgreSQL JSONB to SQLite JSON
   ```

## Running Tests

### All Ledger Tests

```bash
# Verbose output
python -m pytest tests/ledger -v --tb=short --no-cov

# Quick run (minimal output)
python -m pytest tests/ledger -q --no-cov

# Stop on first failure
python -m pytest tests/ledger -x --tb=short --no-cov
```

### Specific Test Classes

```bash
# Run only CRUD tests
python -m pytest tests/ledger/test_ledger_service.py::TestLedgerEntryModelCRUD -v --no-cov

# Run only invariant tests
python -m pytest tests/ledger/test_ledger_invariants.py::TestAmountDirectionInvariant -v --no-cov

# Run tests matching pattern
python -m pytest tests/ledger -k "balance" -v --no-cov
```

### With Coverage Report

```bash
python -m pytest tests/ledger -v --cov=backend/models/finance --cov-report=term-missing
```

## Test Categories

### 1. Model-Level Tests (`test_ledger_service.py`)

| Test Class | Description | SoT Reference |
|------------|-------------|---------------|
| `TestLedgerEntryModelCRUD` | Basic CRUD operations | DATA_SCHEMA.md v5.2 |
| `TestLedgerEntryQueryMethods` | Query methods validation | LEDGER_SOT.md v1.1 §2.4 |
| `TestBalanceCalculation` | Balance sequence consistency | LEDGER_SOT.md v1.1 §2.4 |
| `TestLedgerEntryProperties` | Entry type properties | LEDGER_SOT.md v1.1 §2.2 |

### 2. Invariant Tests (`test_ledger_invariants.py`)

| Test Class | Description | SoT Reference |
|------------|-------------|---------------|
| `TestAmountDirectionInvariant` | Amount sign validation | LEDGER_SOT.md v1.1 §4.1 |
| `TestLedgerInvariantHelper` | Helper class validation | LEDGER_SOT.md v1.1 §4 |
| `TestBalanceConsistencyInvariant` | Balance sequence check | LEDGER_SOT.md v1.1 §2.4 |
| `TestEntryTypeConstraints` | Entry type whitelist | LEDGER_SOT.md v1.1 §4.2 |
| `TestDualLedgerIsolationInvariant` | Dual ledger isolation | LEDGER_SOT.md v1.1 §2.3 |
| `TestBoundaryConditions` | Edge cases | DATA_SCHEMA.md v5.2 |

## Troubleshooting

### Common Errors

#### 1. `NOT NULL constraint failed: ledger_entries.id`

**Cause**: SQLite requires `INTEGER PRIMARY KEY` for autoincrement, not `BIGINT`.

**Fix**: Ensure `conftest.py` has the BigInteger compiler:
```python
from sqlalchemy.ext.compiler import compiles
from sqlalchemy import BigInteger

@compiles(BigInteger, 'sqlite')
def compile_biginteger_sqlite(element, compiler, **kw):
    return "INTEGER"
```

#### 2. `AttributeError: type object 'SQLiteDialect_pysqlite' has no attribute 'type_compiler'`

**Cause**: Old monkey-patching techniques incompatible with SQLAlchemy 2.x.

**Fix**: Use `@compiles` decorator instead of direct dialect modification.

#### 3. `ModuleNotFoundError: No module named 'backend'`

**Cause**: PYTHONPATH not set correctly.

**Fix**:
```bash
cd backend
set PYTHONPATH=%CD%  # Windows
export PYTHONPATH=$PWD  # Linux/Mac
```

#### 4. Fixture `db_session` not found

**Cause**: conftest.py not loaded properly.

**Fix**: Run pytest from `backend/` directory:
```bash
cd backend
python -m pytest tests/ledger -v
```

### Debug Mode

```bash
# Run with verbose debugging
python -m pytest tests/ledger -v --tb=long -s

# Run specific test with print output
python -m pytest tests/ledger/test_ledger_service.py::TestLedgerEntryModelCRUD::test_create_revenue_entry -v -s
```

## CI/CD Integration

For GitHub Actions or other CI systems:

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run ledger tests
        run: |
          cd backend
          python -m pytest tests/ledger -v --tb=short --no-cov
        env:
          TESTING: 'true'
          DATABASE_URL: 'sqlite:///:memory:'
```

## References

- [LEDGER_SOT.md v1.1](../../docs/sot/LEDGER_SOT.md) - Ledger system specification
- [STATE_MACHINE.md v2.6](../../docs/sot/STATE_MACHINE.md) - State machine definitions
- [DATA_SCHEMA.md v5.2](../../docs/sot/DATA_SCHEMA.md) - Database schema specification
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
