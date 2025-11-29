# TODO: AdSpendDaily model will be redesigned and reimplemented based on DATA_SCHEMA.md
#
# This module has been cleared for rewrite.
# The previous implementation had field mismatches with SoT:
# - Used ad_account_code (String) instead of proper FK
# - Field names didn't align with API expectations
#
# Next steps:
# 1. Review DATA_SCHEMA.md v5.2 for correct table structure
# 2. Implement model aligned with SoT
# 3. Create proper relationships and indexes


class AdSpendDaily:
    """
    Placeholder class to prevent import errors.

    This will be replaced with a proper SQLAlchemy model
    aligned with DATA_SCHEMA.md v5.2.
    """
    __abstract__ = True  # Prevents SQLAlchemy from creating a table
    pass
