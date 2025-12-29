# Detection Patterns Reference

## Dead Code Patterns

### Unused Imports (High Confidence)

| Pattern | Example | Safe to Remove |
|---------|---------|----------------|
| Standard library unused | `import os` (never used) | ✅ Yes |
| Third-party unused | `import pandas as pd` | ✅ Yes |
| Partial import unused | `from typing import Dict` | ✅ Yes |

**False Positive Cases:**
- Re-exports in `__init__.py`
- Type hints in `if TYPE_CHECKING:` blocks
- Dynamic imports via `importlib`
- Plugins loaded by name

### Unused Functions (Medium Confidence)

| Pattern | Confidence | Notes |
|---------|------------|-------|
| Private function `_helper()` | Skip | Conventionally internal |
| Public function `process()` | Medium | Check for dynamic calls |
| Decorated `@app.route` | Skip | Framework magic |
| Class method | Lower | May be called via `self` |

**False Positive Cases:**
- Callback functions passed by reference
- Event handlers
- Test fixtures
- API endpoints

### Unused Classes (Medium Confidence)

| Pattern | Confidence | Notes |
|---------|------------|-------|
| No instantiation | Medium | May use factory pattern |
| Abstract base class | Lower | Inherited elsewhere |
| Exception class | Lower | Raised by name string |

## Stale Code Patterns

### Commented Code (Medium Confidence)

Detected when comment contains code-like patterns:

```python
# Flagged (looks like code):
# def old_function():
# return x + y
# import deprecated_module

# Not flagged (regular comments):
# This function handles user input
# TODO: refactor later
# See docs for details
```

### Debug Statements (High Confidence)

| Pattern | Language | Confidence |
|---------|----------|------------|
| `print(...)` | Python | High (in non-script) |
| `console.log(...)` | JS/TS | High |
| `debugger` | JS/TS | High |
| `pdb.set_trace()` | Python | High |
| `breakpoint()` | Python | High |

**False Positive Cases:**
- CLI tools that intentionally print
- Logging statements (use `logging` instead)
- Test output

### Stale TODOs (Based on Date)

```python
# Flagged (> 90 days old):
# TODO 2024-01-15: Fix this edge case

# Not flagged (recent):
# TODO 2025-12-01: Implement feature

# Low confidence (no date):
# TODO: Refactor this function
```

## Unused Dependencies

### Python (Low Confidence)

| Package | Import Name | Notes |
|---------|-------------|-------|
| pillow | PIL | Name mismatch |
| python-dotenv | dotenv | Name mismatch |
| pyyaml | yaml | Name mismatch |
| scikit-learn | sklearn | Name mismatch |

**False Positive Cases:**
- Build tools (setuptools, wheel)
- CLI tools (black, pytest)
- Plugins loaded by name
- Optional dependencies

### Node.js (Low Confidence)

**Always Skip:**
- `@types/*` - TypeScript types
- `eslint*`, `prettier` - Linting
- `webpack`, `vite`, `next` - Build tools
- `jest`, `vitest` - Testing
- `tailwindcss`, `postcss` - CSS processing

## Confidence Level Guidelines

| Level | Meaning | Recommended Action |
|-------|---------|-------------------|
| High | 95%+ certain unused | Safe to remove |
| Medium | 70-95% certain | Review before removing |
| Low | <70% certain | Manual verification needed |
