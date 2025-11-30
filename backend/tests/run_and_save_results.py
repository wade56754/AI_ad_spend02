#!/usr/bin/env python
"""Run pytest and save results to file."""
import subprocess
import sys
import os
from pathlib import Path

# Change to backend directory
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

# Run pytest
result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/ledger', '-v', '--tb=short', '--no-cov'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=180
)

# Save results
output_file = backend_dir / 'tests' / 'pytest_results.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("PYTEST RESULTS\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"EXIT CODE: {result.returncode}\n\n")
    f.write("STDOUT:\n")
    f.write(result.stdout or "None")
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr or "None")

print(f"Results saved to: {output_file}")
print(f"Exit code: {result.returncode}")
