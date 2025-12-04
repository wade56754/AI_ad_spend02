import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    import pytest
    print(f"pytest version: {pytest.__version__}")
    print(f"pytest location: {pytest.__file__}")
except ImportError as e:
    print(f"pytest not installed: {e}")
