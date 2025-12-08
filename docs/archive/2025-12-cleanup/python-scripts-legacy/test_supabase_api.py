#!/usr/bin/env python
"""Test Supabase API connection."""
import urllib.request
import urllib.error
import json
import ssl

SUPABASE_URL = "https://jzmcoivxhiyidizncyaq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6bWNvaXZ4aGl5aWRpem5jeWFxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzMTc4MTEsImV4cCI6MjA3Nzg5MzgxMX0.PIr4EdBjfyCgRa48IxK6yLS0yIER-_3qvd-Mv-4I7rw"

output = []

# Create SSL context that doesn't verify
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    # Test REST API health
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
    )

    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        status = resp.status
        data = resp.read().decode()
        output.append(f"REST API Status: {status}")
        output.append(f"Response: {data[:200]}...")
        output.append("SUCCESS: Supabase API is accessible!")

except urllib.error.HTTPError as e:
    output.append(f"HTTP Error: {e.code} - {e.reason}")
    output.append(f"Response: {e.read().decode()[:200]}")
except urllib.error.URLError as e:
    output.append(f"URL Error: {e.reason}")
except Exception as e:
    output.append(f"Error: {type(e).__name__}: {e}")

# Write result
result = "\n".join(output)
print(result)

from pathlib import Path
out_file = Path(__file__).parent / "tmp" / "api_test_result.txt"
out_file.parent.mkdir(exist_ok=True)
out_file.write_text(result, encoding="utf-8")
