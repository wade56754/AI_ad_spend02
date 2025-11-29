"""
Ad Spend Router - Placeholder

This module has been cleared for rewrite.
The previous implementation used fields that didn't exist in the model.

TODO: Rebuild ad_spend endpoints based on new SoT (DATA_SCHEMA.md v5.2)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/adspend", tags=["ad_spend"])

# TODO: Rebuild ad_spend endpoints based on new SoT
# Endpoints to implement:
# - GET /reports - List ad spend reports
# - GET /reports/{id} - Get single report
# - POST /report - Create report
# - etc.
