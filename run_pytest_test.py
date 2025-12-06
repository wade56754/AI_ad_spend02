"""
Phase 2c 验证脚本: RUN-PYTEST / RUN-SUITE 模式验证
临时文件，执行后可删除
"""
import subprocess
import sys
import os
import json
import time

os.chdir(r'D:\git\1108\AI_ad_spend02')
os.environ['PYTHONPATH'] = r'D:\git\1108\AI_ad_spend02'

results = []

# Test 1: RUN-PYTEST mode - single test
print("=" * 60)
print("TEST 1: RUN-PYTEST mode (test_factory.py)")
print("=" * 60)

start = time.time()
result = subprocess.run(
    [r'.venv\Scripts\python.exe', '-m', 'pytest',
     'agents/tests/test_factory.py::TestCreateAgent::test_create_fe_agent',
     '-v', '--tb=short', '-p', 'no:postgresql'],
    capture_output=True,
    text=True,
    timeout=60
)
duration = int((time.time() - start) * 1000)

print(f"Command: pytest agents/tests/test_factory.py::TestCreateAgent::test_create_fe_agent -v --tb=short")
print(f"Return code: {result.returncode}")
print(f"Duration: {duration}ms")
print("STDOUT:", result.stdout[:2000] if result.stdout else "(empty)")
print("STDERR:", result.stderr[:500] if result.stderr else "(empty)")

results.append({
    "mode": "RUN-PYTEST",
    "test_id": "agents/tests/test_factory.py::TestCreateAgent::test_create_fe_agent",
    "returncode": result.returncode,
    "duration_ms": duration,
    "passed": result.returncode == 0
})

# Test 2: RUN-PYTEST mode - test_types.py
print("\n" + "=" * 60)
print("TEST 2: RUN-PYTEST mode (test_types.py)")
print("=" * 60)

start = time.time()
result = subprocess.run(
    [r'.venv\Scripts\python.exe', '-m', 'pytest',
     'agents/tests/test_types.py',
     '-v', '--tb=short', '-p', 'no:postgresql'],
    capture_output=True,
    text=True,
    timeout=60
)
duration = int((time.time() - start) * 1000)

print(f"Command: pytest agents/tests/test_types.py -v --tb=short")
print(f"Return code: {result.returncode}")
print(f"Duration: {duration}ms")
print("STDOUT:", result.stdout[:2000] if result.stdout else "(empty)")
print("STDERR:", result.stderr[:500] if result.stderr else "(empty)")

results.append({
    "mode": "RUN-PYTEST",
    "test_id": "agents/tests/test_types.py",
    "returncode": result.returncode,
    "duration_ms": duration,
    "passed": result.returncode == 0
})

# Test 3: RUN-SUITE mode - smoke
print("\n" + "=" * 60)
print("TEST 3: RUN-SUITE mode (scope=smoke)")
print("=" * 60)

start = time.time()
result = subprocess.run(
    [r'.venv\Scripts\python.exe', '-m', 'pytest',
     'agents/tests/test_factory.py', 'agents/tests/test_types.py',
     '-v', '--tb=short', '-p', 'no:postgresql', '--maxfail=5'],
    capture_output=True,
    text=True,
    timeout=120
)
duration = int((time.time() - start) * 1000)

print(f"Command: pytest agents/tests/test_factory.py agents/tests/test_types.py -v --tb=short --maxfail=5")
print(f"Return code: {result.returncode}")
print(f"Duration: {duration}ms")
print("STDOUT:", result.stdout[:3000] if result.stdout else "(empty)")
print("STDERR:", result.stderr[:500] if result.stderr else "(empty)")

results.append({
    "mode": "RUN-SUITE",
    "scope": "smoke",
    "returncode": result.returncode,
    "duration_ms": duration,
    "passed": result.returncode == 0
})

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(json.dumps(results, indent=2))

# Write to file for verification
with open('pytest_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults written to pytest_results.json")
