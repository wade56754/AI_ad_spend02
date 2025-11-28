"""
Tests for SoT 守门员 Skill (sot_guard_skill.py)

Tests cover:
- State machine compliance checking
- Ledger compliance checking
- Error code compliance checking
- Data schema compliance checking
- Dynamic SoT parsing (P2 enhancement)
"""

import pytest
from agents.skills.sot_guard_skill import (
    validate_against_sot,
    guard_check,
    check_state_machine_compliance,
    check_ledger_compliance,
    check_error_code_compliance,
    check_data_schema_compliance,
    SotViolation,
    SotGuardResult,
    get_daily_report_states,
    get_project_states,
    get_error_code_prefixes,
    DEFAULT_DAILY_REPORT_STATES,
    DEFAULT_ERROR_CODE_PREFIXES,
)


class TestStateMachineCompliance:
    """Tests for state machine compliance checking."""

    def test_valid_daily_report_status(self):
        """Valid daily report status should not trigger violations."""
        code = '''
        report.status = "raw_submitted"
        report.status = "trend_pending"
        report.status = "final_locked"
        '''
        violations = check_state_machine_compliance(code, "test.py")
        # Valid states should not generate P0 violations
        p0_violations = [v for v in violations if v.severity == "P0"]
        assert len(p0_violations) == 0

    def test_invalid_daily_report_status_detected(self):
        """Invalid daily report status should trigger P0 violation."""
        code = '''
        report.status = "invalid_status"
        daily_report.status = "unknown_state"
        '''
        violations = check_state_machine_compliance(code, "test.py")
        # Should detect invalid states
        assert len(violations) >= 1
        assert all(v.severity == "P0" for v in violations)
        assert all(v.rule == "SM-DR-001" for v in violations)

    def test_project_status_validation(self):
        """Project status should be validated against SoT."""
        # Valid
        valid_code = 'project.status = "active"'
        violations = check_state_machine_compliance(valid_code, "test.py")
        p0 = [v for v in violations if v.severity == "P0" and "SM-PROJ" in v.rule]
        assert len(p0) == 0

    def test_comments_are_skipped(self):
        """Comments should be skipped in compliance checking."""
        code = '''
        # status = "invalid_status"
        // status = "another_invalid"
        '''
        violations = check_state_machine_compliance(code, "test.py")
        assert len(violations) == 0


class TestLedgerCompliance:
    """Tests for ledger system compliance checking."""

    def test_direct_balance_modification_detected(self):
        """Direct balance modification should trigger P0 violation."""
        code = '''
        project.balance = 1000
        account.balance += 500
        balance = balance + 100
        '''
        violations = check_ledger_compliance(code, "test.py")
        assert len(violations) >= 1
        assert any(v.rule == "LED-001" for v in violations)
        assert all(v.severity == "P0" for v in violations)

    def test_sql_balance_update_detected(self):
        """SQL UPDATE on balance should trigger P0 violation."""
        code = '''
        UPDATE projects SET balance = 1000 WHERE id = 1
        '''
        violations = check_ledger_compliance(code, "test.py")
        assert len(violations) >= 1
        assert any(v.rule == "LED-001" for v in violations)

    def test_ledger_entries_update_detected(self):
        """UPDATE/DELETE on ledger_entries should trigger P0 violation."""
        code = '''
        UPDATE ledger_entries SET amount = 100
        DELETE FROM ledger_entries WHERE id = 1
        '''
        violations = check_ledger_compliance(code, "test.py")
        assert len(violations) >= 2
        assert all(v.rule == "LED-002" for v in violations)

    def test_ledger_insert_allowed(self):
        """INSERT into ledger_entries should be allowed."""
        code = '''
        INSERT INTO ledger_entries (amount, type) VALUES (100, 'RECHARGE')
        '''
        violations = check_ledger_compliance(code, "test.py")
        assert len(violations) == 0

    def test_comments_are_skipped_in_ledger(self):
        """SQL comments should be skipped."""
        code = '''
        -- UPDATE ledger_entries SET amount = 100
        # project.balance = 1000
        '''
        violations = check_ledger_compliance(code, "test.py")
        assert len(violations) == 0


class TestErrorCodeCompliance:
    """Tests for error code compliance checking."""

    def test_valid_error_code_prefixes(self):
        """Known error code prefixes should not trigger warnings."""
        code = '''
        raise APIError("VAL-001", "Validation error")
        return error_response("AUTH-002", "Unauthorized")
        '''
        warnings = check_error_code_compliance(code, "test.py")
        assert len(warnings) == 0

    def test_unknown_error_code_prefix_detected(self):
        """Unknown error code prefix should trigger P1 warning."""
        code = '''
        raise APIError("XYZ-001", "Unknown error")
        '''
        warnings = check_error_code_compliance(code, "test.py")
        assert len(warnings) >= 1
        assert warnings[0].rule == "ERR-001"
        assert warnings[0].severity == "P1"
        assert "XYZ" in warnings[0].detail


class TestDataSchemaCompliance:
    """Tests for data schema compliance checking."""

    def test_known_table_allowed(self):
        """Known tables should not trigger warnings."""
        code = '''
        class DailyReports(Base):
            __tablename__ = "daily_reports"
        '''
        warnings = check_data_schema_compliance(code, "test.py")
        assert len(warnings) == 0

    def test_unknown_table_detected(self):
        """Unknown table definitions should trigger P1 warning."""
        code = '''
        class UnknownTable(Base):
            __tablename__ = "unknown_table"
        '''
        warnings = check_data_schema_compliance(code, "test.py")
        assert len(warnings) >= 1
        assert warnings[0].rule == "SCHEMA-001"
        assert warnings[0].severity == "P1"


class TestValidateAgainstSot:
    """Integration tests for validate_against_sot function."""

    def test_empty_changes_pass(self):
        """Empty changes should pass validation."""
        result = validate_against_sot({})
        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_clean_code_passes(self):
        """Clean code following SoT should pass."""
        changes = {
            "test.py": '''
            report.status = "raw_submitted"
            ledger_entry = LedgerEntry(amount=100, type="RECHARGE")
            db.add(ledger_entry)
            '''
        }
        result = validate_against_sot(changes)
        # Should pass (no P0 violations)
        assert result["passed"] is True

    def test_p0_violations_fail_validation(self):
        """P0 violations should fail validation."""
        changes = {
            "bad_code.py": '''
            project.balance = 1000  # LED-001: Direct balance modification
            '''
        }
        result = validate_against_sot(changes)
        assert result["passed"] is False
        assert len(result["violations"]) >= 1

    def test_guard_check_alias(self):
        """guard_check should be alias for validate_against_sot."""
        changes = {"test.py": "valid = True"}
        result1 = validate_against_sot(changes)
        result2 = guard_check(changes)
        assert result1 == result2


class TestSotGuardResult:
    """Tests for SotGuardResult dataclass."""

    def test_to_dict(self):
        """to_dict should return proper dictionary format."""
        violation = SotViolation(
            file="test.py",
            rule="LED-001",
            severity="P0",
            detail="Direct balance modification",
            line=10,
        )
        result = SotGuardResult(
            passed=False,
            violations=[violation],
            warnings=[],
        )
        d = result.to_dict()
        assert d["passed"] is False
        assert len(d["violations"]) == 1
        assert d["violations"][0]["file"] == "test.py"
        assert d["violations"][0]["rule"] == "LED-001"
        assert d["violations"][0]["line"] == 10


class TestDynamicSotParsing:
    """Tests for P2 dynamic SoT parsing enhancement."""

    def test_get_daily_report_states_returns_set(self):
        """get_daily_report_states should return a non-empty set."""
        states = get_daily_report_states()
        assert isinstance(states, set)
        assert len(states) > 0
        # Should include default states as minimum
        assert "raw_submitted" in states
        assert "final_locked" in states

    def test_get_project_states_returns_set(self):
        """get_project_states should return a non-empty set."""
        states = get_project_states()
        assert isinstance(states, set)
        assert len(states) > 0
        assert "active" in states or "draft" in states

    def test_get_error_code_prefixes_returns_set(self):
        """get_error_code_prefixes should return known prefixes."""
        prefixes = get_error_code_prefixes()
        assert isinstance(prefixes, set)
        assert len(prefixes) > 0
        # Should include default prefixes as minimum
        assert "VAL" in prefixes or len(prefixes) > 5

    def test_default_states_available(self):
        """Default state constants should be available for fallback."""
        assert len(DEFAULT_DAILY_REPORT_STATES) == 8
        assert "raw_submitted" in DEFAULT_DAILY_REPORT_STATES
        assert "final_locked" in DEFAULT_DAILY_REPORT_STATES

    def test_default_error_prefixes_available(self):
        """Default error code prefixes should be available."""
        assert len(DEFAULT_ERROR_CODE_PREFIXES) >= 10
        assert "VAL" in DEFAULT_ERROR_CODE_PREFIXES
        assert "AUTH" in DEFAULT_ERROR_CODE_PREFIXES
