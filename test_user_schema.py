"""Verify user schema team_id fields"""

from backend.schemas.user import UserResponse, UserListResponse
from uuid import uuid4
from datetime import datetime

# Check schema fields
print("=== UserResponse fields ===")
for name, field in UserResponse.model_fields.items():
    if "team" in name:
        print(f"{name}: {field.annotation}")

print()
print("=== UserListResponse fields ===")
for name, field in UserListResponse.model_fields.items():
    if "team" in name:
        print(f"{name}: {field.annotation}")

# Test serialization
sample = UserResponse(
    id=uuid4(),
    username="test_pitcher",
    email="test@example.com",
    full_name="测试投手",
    role="pitcher",
    department="深圳团队",
    team_id=uuid4(),
    team_name="深圳团队",
    is_active=True,
    created_at=datetime.now(),
    updated_at=None,
)

print()
print("=== Sample Response ===")
data = sample.model_dump()
print(f"team_id: {data['team_id']}")
print(f"team_name: {data['team_name']}")
print()
print("SUCCESS: team_id and team_name serialization works!")
