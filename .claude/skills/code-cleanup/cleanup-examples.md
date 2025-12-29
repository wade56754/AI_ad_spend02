# Cleanup Examples

## Example 1: Removing Unused Imports

### Before
```python
import os
import sys
import json
from typing import Dict, List, Optional
from datetime import datetime

def get_user(user_id: int) -> Optional[Dict]:
    """Fetch user by ID."""
    return {"id": user_id, "name": "Test"}
```

### After
```python
from typing import Dict, Optional

def get_user(user_id: int) -> Optional[Dict]:
    """Fetch user by ID."""
    return {"id": user_id, "name": "Test"}
```

**Removed:**
- `import os` - never used
- `import sys` - never used  
- `import json` - never used
- `List` - not used in type hints
- `datetime` - never used

---

## Example 2: Removing Debug Code

### Before
```typescript
async function fetchUsers() {
  console.log('Fetching users...');
  const response = await api.get('/users');
  console.log('Response:', response);
  debugger;
  return response.data;
}
```

### After
```typescript
async function fetchUsers() {
  const response = await api.get('/users');
  return response.data;
}
```

**Removed:**
- `console.log('Fetching users...')` - debug output
- `console.log('Response:', response)` - debug output
- `debugger` - breakpoint

---

## Example 3: Cleaning Stale Comments

### Before
```python
def calculate_total(items):
    # TODO 2023-06-15: optimize this loop
    # for item in items:
    #     total += item.price * item.quantity
    total = sum(item.price * item.quantity for item in items)
    return total
```

### After
```python
def calculate_total(items):
    total = sum(item.price * item.quantity for item in items)
    return total
```

**Removed:**
- Stale TODO (> 18 months old)
- Commented-out code block

---

## Example 4: Removing Unused Dependencies

### requirements.txt Before
```
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.0
requests==2.31.0    # Not used
pandas==2.0.0       # Not used
numpy==1.24.0       # Only used by pandas
```

### requirements.txt After
```
fastapi==0.100.0
uvicorn==0.23.0
pydantic==2.0.0
```

---

## Batch Cleanup Commands

### Remove All Unused Imports (Python)

```bash
# Using autoflake
pip install autoflake
autoflake --in-place --remove-all-unused-imports backend/**/*.py

# Using ruff
pip install ruff
ruff check --select F401 --fix backend/
```

### Remove All Debug Statements

```bash
# Find and review first
grep -rn "console.log\|debugger" src/

# Remove with sed (careful!)
find src -name "*.ts" -exec sed -i '/console.log/d' {} \;
```

### Remove Commented Code

```bash
# Python: Remove lines starting with #<code>
# (Manual review recommended - too risky for automation)
```

---

## Safety Checklist

Before bulk cleanup:

- [ ] Commit current state (backup)
- [ ] Run test suite (baseline)
- [ ] Review high-confidence issues first
- [ ] Apply changes incrementally
- [ ] Run tests after each batch
- [ ] Check for runtime errors

After cleanup:

- [ ] All tests pass
- [ ] Application starts correctly
- [ ] Key features work
- [ ] No import errors at runtime
