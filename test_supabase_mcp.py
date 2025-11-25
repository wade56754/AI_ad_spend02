"""Test Supabase API connection"""
import requests

token = 'sbp_e64f59f761e35d6f89b8df7fd8c1a80a1c70a13a'
project_ref = 'jzmcoivxhiyidizncyq'

print("=" * 50)
print("Supabase API Connection Test")
print("=" * 50)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test 1: List projects
print("\n[Test 1] List Projects...")
try:
    resp = requests.get('https://api.supabase.com/v1/projects', headers=headers, timeout=10)
    print(f"  Status: HTTP {resp.status_code}")
    if resp.status_code == 200:
        projects = resp.json()
        print(f"  Result: Found {len(projects)} project(s)")
        for p in projects:
            print(f"    - {p.get('name', 'unknown')} (ref: {p.get('id', '')})")
    else:
        print(f"  Error: {resp.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")

# Test 2: Get specific project
print(f"\n[Test 2] Get Project '{project_ref}'...")
try:
    resp2 = requests.get(f'https://api.supabase.com/v1/projects/{project_ref}', headers=headers, timeout=10)
    print(f"  Status: HTTP {resp2.status_code}")
    if resp2.status_code == 200:
        proj = resp2.json()
        print(f"  Name: {proj.get('name')}")
        print(f"  Region: {proj.get('region')}")
        print(f"  Status: {proj.get('status')}")
        print(f"  DB Host: {proj.get('database', {}).get('host', 'N/A')}")
    else:
        print(f"  Error: {resp2.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")

print("\n" + "=" * 50)
print("Test Complete")
print("=" * 50)
