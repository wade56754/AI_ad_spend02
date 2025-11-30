---
name: ai-ad-api-automation-test
version: "1.0"
status: ready_for_production
layer: skill
owner: wade
last_reviewed: 2025-12-01
baseline:
  - MASTER.md v3.5
  - SoT Freeze v2.6
  - Dev-Guides Freeze vFinal
  - Architecture Freeze v1.0
  - Infrastructure Freeze v1.0
  - Agent Freeze v1.0
  - AUTOMATION_TEST_SPEC_v1.4.md
---

<skill>
<name>ai-ad-api-automation-test</name>
<version>v1.0</version>
<domain>AI_AD_SYSTEM / API Automation Testing</domain>
<profile>API-Test-Orchestrator / Newman-Integration / pytest-Generation</profile>

<!-- ======================================================
     0. Core Mission
====================================================== -->
<mission>
  API 自动化测试编排与执行 Skill，负责：
  - 生成符合 AUTOMATION_TEST_SPEC_v1.4 规范的 pytest 测试代码
  - 支持 Newman/Postman Collection 集成（契约测试扩展）
  - 执行 L2 API 层测试并生成报告
  - 确保测试用例与 SoT 文档对齐

  参考来源：
  - https://github.com/jfrelis/sanbercode-api-automation-boilerplate
  - Newman + Postman Collection 模式
  - 项目内 AUTOMATION_TEST_SPEC_v1.4.md 规范
</mission>


<!-- ======================================================
     1. Upstream Dependencies
====================================================== -->
<dependencies>
  <sot_documents>
    | Priority | Document | Version | Purpose |
    |----------|----------|---------|---------|
    | P0 | STATE_MACHINE.md | v2.6 | State enums, transitions, terminal states |
    | P0 | DATA_SCHEMA.md | v5.2 | Data structures, field constraints |
    | P1 | API_SOT.md | v9.0 | API endpoints, request/response contracts |
    | P1 | ERROR_CODES_SOT.md | v2.1 | Error code definitions |
    | P1 | LEDGER_SOT.md | v1.1 | Ledger entry types, balance rules |
    | P2 | DAILY_REPORT_SOT.md | v1.0 | Daily report 8-state machine |
    | P2 | BUSINESS_RULES.md | v3.1 | Business constraints |
    | P3 | AUTH_SPEC.md | v2.0 | Role permission matrix |
  </sot_documents>

  <external_references>
    | Reference | URL | Purpose |
    |-----------|-----|---------|
    | sanbercode-api-automation-boilerplate | https://github.com/jfrelis/sanbercode-api-automation-boilerplate | Newman/Postman patterns |
    | Newman | https://www.npmjs.com/package/newman | Postman CLI runner |
    | newman-reporter-htmlextra | https://www.npmjs.com/package/newman-reporter-htmlextra | HTML report generation |
  </external_references>
</dependencies>


<!-- ======================================================
     2. Input Contract
====================================================== -->
<input_contract>
  Minimum Input:
  {
    mode: "GENERATE" | "RUN" | "NEWMAN" | "REPORT"
  }

  Optional Input:
  - target_module: string (e.g., "daily_report", "topup_request", "ledger")
  - test_level: "L0" | "L1" | "L2" | "L3" (default: "L2")
  - collection_path: string (Postman collection JSON path, for NEWMAN mode)
  - environment_path: string (Postman environment JSON path)
  - output_format: "cli" | "html" | "json" (for reports)

  Mode Behaviors:

  - GENERATE
    - Generate pytest test code for specified module
    - Output follows AUTOMATION_TEST_SPEC_v1.4 structure
    - Include SoT references in docstrings
    - Use common/ utilities (factories, asserts)

  - RUN
    - Execute pytest tests for specified level/module
    - Generate coverage report
    - Output test results summary

  - NEWMAN
    - Execute Newman runner with Postman collection
    - Support environment variables
    - Generate HTML report via newman-reporter-htmlextra

  - REPORT
    - Generate comprehensive test report
    - Include coverage metrics
    - SoT alignment verification

  Missing mode -> Output <halt>Missing: mode</halt> and stop.
</input_contract>


<!-- ======================================================
     3. Project Scope & Constraints
====================================================== -->
<project_scope>
  Target Directories:
  - Test code: backend/tests/
  - Test config: backend/tests/pytest.ini
  - Test fixtures: backend/tests/conftest.py
  - Common utilities: backend/tests/common/
  - Newman scripts: scripts/newman/ (optional)
  - Postman collections: collections/ (optional)

  Test Levels (from AUTOMATION_TEST_SPEC_v1.4):
  - L0 Unit: backend/tests/unit/ (@pytest.mark.unit)
  - L1 Integration: backend/tests/integration/ (@pytest.mark.integration)
  - L2 API: backend/tests/api/ (@pytest.mark.api)
  - L3 E2E: backend/tests/e2e/ (@pytest.mark.e2e)

  Safety Constraints:
  - MUST NOT modify production database
  - MUST use test database for all operations
  - MUST NOT commit secrets or credentials
  - MUST follow SoT referee chain for business rules
</project_scope>


<!-- ======================================================
     4. Workflow Overview
====================================================== -->
<workflow_overview>
  [Phase 1: Test Generation]
    GENERATE mode
      -> Read target module source code
      -> Query relevant SoT documents
      -> Generate test classes following naming conventions
      -> Output pytest test file

  [Phase 2: Test Execution]
    RUN mode
      -> Execute pytest with specified markers
      -> Collect coverage data
      -> Output results summary

  [Phase 3: Newman Integration (Optional)]
    NEWMAN mode
      -> Load Postman collection
      -> Apply environment variables
      -> Execute via Newman CLI
      -> Generate HTML report

  [Phase 4: Reporting]
    REPORT mode
      -> Aggregate test results
      -> Generate coverage report
      -> Verify SoT alignment
</workflow_overview>


<!-- ======================================================
     5. GENERATE Phase
====================================================== -->
<phase id="GENERATE">
  <description>
    Generate pytest test code following AUTOMATION_TEST_SPEC_v1.4 standards.
  </description>

  <prerequisites>
    - Target module exists in backend/
    - Relevant SoT documents identified
    - common/ utilities available
  </prerequisites>

  <naming_conventions>
    File naming: test_<module>.py or test_<module>_flow.py
    Class naming: Test<Module> or Test<Module>Flow
    Function naming: test_<condition>__<expected_result>

    Examples:
    - test_create_user__success
    - test_invalid_email__raises_validation_error
    - test_submit_raw__status_becomes_trend_pending
    - test_media_buyer_approve__returns_403
    - test_negative_amount__returns_BIZ_100
  </naming_conventions>

  <test_class_structure>
    Required test classes for L2 API tests:

    1. Test<Module>HappyPath
       - Complete successful flow from start to terminal state
       - Reference: STATE_MACHINE.md transitions

    2. Test<Module>Permissions
       - Permission boundary tests for each role
       - Reference: AUTH_SPEC.md permission matrix

    3. Test<Module>StateMachineViolations
       - Illegal state transition tests
       - Reference: STATE_MACHINE.md whitelist

    4. Test<Module>ErrorCodes
       - Error code validation tests
       - Reference: ERROR_CODES_SOT.md definitions
  </test_class_structure>

  <docstring_template>
    ```python
    """
    <Brief description>

    SoT References:
    - docs/2.sot/STATE_MACHINE.md v2.6 Section X.X (specific rule)
    - docs/2.sot/ERROR_CODES_SOT.md v2.1 (error code prefix)
    - docs/2.sot/API_SOT.md v9.0 (API endpoint)
    """
    ```
  </docstring_template>

  <output_template>
    ```python
    # backend/tests/api/test_<module>_flow.py
    """
    <Module> API Flow Tests

    SoT References:
    - docs/2.sot/STATE_MACHINE.md v2.6 Section X (state machine)
    - docs/2.sot/ERROR_CODES_SOT.md v2.1 (error codes)
    - docs/2.sot/API_SOT.md v9.0 (API contracts)
    - docs/2.sot/AUTH_SPEC.md v2.0 (permissions)
    """

    import pytest
    from decimal import Decimal
    from datetime import date

    from backend.tests.common.factories import create_user, create_<entity>
    from backend.tests.common.state_asserts import (
        assert_status_transition,
        assert_valid_transition,
        assert_terminal_state
    )
    from backend.tests.common.error_helpers import (
        assert_error_response,
        assert_success_response
    )
    from backend.tests.api.conftest import auth_header


    @pytest.mark.api
    class Test<Module>HappyPath:
        """
        Happy Path: Complete successful flow

        SoT Reference: STATE_MACHINE.md v2.6 Section X.X
        """

        def test_full_flow__start_to_terminal(self, client, db_session, *_tokens):
            """Complete happy path test"""
            # Arrange
            # Act
            # Assert
            pass


    @pytest.mark.api
    class Test<Module>Permissions:
        """
        Permission boundary tests

        SoT Reference: AUTH_SPEC.md v2.0 Section 3
        """

        def test_unauthorized_role__returns_403(self, client, db_session, token):
            """Role X cannot perform action Y"""
            pass


    @pytest.mark.api
    class Test<Module>StateMachineViolations:
        """
        Illegal state transition tests

        SoT Reference: STATE_MACHINE.md v2.6 Section X.X (whitelist)
        """

        def test_illegal_transition__returns_STATE_001(self, client, db_session):
            """<from_state> cannot directly transition to <to_state>"""
            pass


    @pytest.mark.api
    class Test<Module>ErrorCodes:
        """
        Error code validation tests

        SoT Reference: ERROR_CODES_SOT.md v2.1
        """

        def test_invalid_input__returns_VALIDATION_001(self, client):
            """Missing required field"""
            pass
    ```
  </output_template>
</phase>


<!-- ======================================================
     6. RUN Phase
====================================================== -->
<phase id="RUN">
  <description>
    Execute pytest tests with specified markers and generate reports.
  </description>

  <commands>
    | Scenario | Command | Description |
    |----------|---------|-------------|
    | All tests | pytest backend/tests | Full test suite |
    | Unit only | pytest -m unit | L0 tests |
    | Integration | pytest -m integration | L1 tests |
    | API only | pytest -m api | L2 tests |
    | E2E only | pytest -m e2e | L3 tests |
    | Quick CI | pytest -m "not e2e" | Exclude E2E |
    | Coverage | pytest --cov=backend --cov-report=html | With coverage |
    | Specific file | pytest backend/tests/api/test_X.py | Single file |
  </commands>

  <coverage_thresholds>
    | Level | Target | Description |
    |-------|--------|-------------|
    | L0 Unit | 80% | Core business logic |
    | L1 Integration | 70% | State machine flows |
    | L2 API | 60% | Core API endpoints |
    | Overall | 70% | CI blocking threshold |
  </coverage_thresholds>

  <output_format>
    ```markdown
    ## Test Execution Report

    **Timestamp**: YYYY-MM-DD HH:MM:SS
    **Mode**: RUN
    **Target**: <module or level>

    ### Results Summary
    | Metric | Value |
    |--------|-------|
    | Total Tests | N |
    | Passed | X |
    | Failed | Y |
    | Skipped | Z |
    | Coverage | XX% |

    ### Failed Tests
    - test_module.py::TestClass::test_function
      - Error: <error message>
      - Location: <file>:<line>

    ### Coverage by Module
    | Module | Coverage |
    |--------|----------|
    | backend/services/ | XX% |
    | backend/api/ | XX% |

    ### SoT Alignment Check
    - [x] STATE_MACHINE.md transitions covered
    - [x] ERROR_CODES_SOT.md codes validated
    - [ ] Missing: <specific coverage gaps>
    ```
  </output_format>
</phase>


<!-- ======================================================
     7. NEWMAN Phase (Contract Testing Extension)
====================================================== -->
<phase id="NEWMAN">
  <description>
    Execute Postman collections via Newman CLI for contract testing.
    Reference: sanbercode-api-automation-boilerplate patterns.
  </description>

  <prerequisites>
    - Node.js installed
    - Newman package: npm install -g newman
    - HTML reporter: npm install -g newman-reporter-htmlextra
    - Postman collection exported as JSON
    - Environment file (optional)
  </prerequisites>

  <directory_structure>
    ```
    project_root/
    ├── collections/                    # Postman collections
    │   ├── daily_report_api.json
    │   ├── topup_api.json
    │   └── ledger_api.json
    ├── environments/                   # Environment configs
    │   ├── local.json
    │   ├── staging.json
    │   └── production.json
    └── scripts/
        └── newman/
            ├── run_api_tests.js        # Newman runner script
            └── package.json            # Dependencies
    ```
  </directory_structure>

  <newman_runner_template>
    ```javascript
    // scripts/newman/run_api_tests.js
    /**
     * Newman API Test Runner
     *
     * Reference: sanbercode-api-automation-boilerplate
     * SoT: API_SOT.md v9.0
     */

    const newman = require("newman");
    const path = require("path");

    // Configuration
    const config = {
      collection: path.join(__dirname, "../../collections/api_collection.json"),
      environment: path.join(__dirname, "../../environments/local.json"),
      reporters: ["cli", "htmlextra"],
      reporter: {
        htmlextra: {
          export: path.join(__dirname, "../../reports/api_test_report.html"),
          title: "AI Ad Spend API Test Report",
          browserTitle: "API Tests",
          showOnlyFails: false,
          noSyntaxHighlighting: false,
          testPaging: true,
          logs: true,
          omitRequestBodies: false,
          omitResponseBodies: false,
        },
      },
      // Environment variables override
      envVar: [
        { key: "BASE_URL", value: process.env.API_BASE_URL || "http://localhost:8000" },
        { key: "API_VERSION", value: "v1" },
      ],
      // Timeout settings
      timeout: {
        request: 30000,
        script: 30000,
      },
    };

    // Run Newman
    newman.run(config, function (err, summary) {
      if (err) {
        console.error("Newman run failed:", err);
        process.exit(1);
      }

      // Output summary
      console.log("\n=== Test Summary ===");
      console.log(`Total: ${summary.run.stats.tests.total}`);
      console.log(`Passed: ${summary.run.stats.tests.total - summary.run.stats.tests.failed}`);
      console.log(`Failed: ${summary.run.stats.tests.failed}`);

      // Exit with error code if any tests failed
      if (summary.run.stats.tests.failed > 0) {
        process.exit(1);
      }
    });
    ```
  </newman_runner_template>

  <package_json_template>
    ```json
    {
      "name": "ai-ad-spend-api-tests",
      "version": "1.0.0",
      "description": "API automation tests for AI Ad Spend system",
      "scripts": {
        "test:api": "node run_api_tests.js",
        "test:api:local": "API_BASE_URL=http://localhost:8000 npm run test:api",
        "test:api:staging": "API_BASE_URL=https://staging.example.com npm run test:api"
      },
      "devDependencies": {
        "newman": "^6.0.0",
        "newman-reporter-htmlextra": "^1.22.11"
      }
    }
    ```
  </package_json_template>

  <postman_collection_template>
    ```json
    {
      "info": {
        "name": "AI Ad Spend API Tests",
        "description": "API contract tests - SoT: API_SOT.md v9.0",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
      },
      "variable": [
        {
          "key": "base_url",
          "value": "{{BASE_URL}}/api/{{API_VERSION}}"
        }
      ],
      "item": [
        {
          "name": "Daily Reports",
          "description": "Daily Report API tests - STATE_MACHINE.md v2.6 Section 8",
          "item": [
            {
              "name": "Create Daily Report",
              "request": {
                "method": "POST",
                "header": [
                  {
                    "key": "Authorization",
                    "value": "Bearer {{access_token}}"
                  },
                  {
                    "key": "Content-Type",
                    "value": "application/json"
                  }
                ],
                "url": {
                  "raw": "{{base_url}}/daily-reports/",
                  "host": ["{{base_url}}"],
                  "path": ["daily-reports", ""]
                },
                "body": {
                  "mode": "raw",
                  "raw": "{\n  \"ad_account_id\": \"test-account-001\",\n  \"report_date\": \"{{$isoTimestamp}}\",\n  \"conversions_raw\": 100,\n  \"raw_spend\": \"1000.00\"\n}"
                }
              },
              "event": [
                {
                  "listen": "test",
                  "script": {
                    "exec": [
                      "// Contract test: API_SOT.md v9.0",
                      "pm.test('Status code is 201', function() {",
                      "    pm.response.to.have.status(201);",
                      "});",
                      "",
                      "pm.test('Response has success=true', function() {",
                      "    const json = pm.response.json();",
                      "    pm.expect(json.success).to.be.true;",
                      "});",
                      "",
                      "pm.test('Status is raw_submitted (STATE_MACHINE.md)', function() {",
                      "    const json = pm.response.json();",
                      "    pm.expect(json.data.status).to.equal('raw_submitted');",
                      "});",
                      "",
                      "// Store report_id for subsequent tests",
                      "const json = pm.response.json();",
                      "pm.environment.set('report_id', json.data.id);"
                    ]
                  }
                }
              ]
            }
          ]
        }
      ]
    }
    ```
  </postman_collection_template>

  <execution_commands>
    | Command | Description |
    |---------|-------------|
    | npm run test:api | Run API tests with default config |
    | npm run test:api:local | Run against local server |
    | npm run test:api:staging | Run against staging |
    | newman run collection.json -e env.json | Direct Newman command |
    | newman run collection.json -r htmlextra | With HTML report |
  </execution_commands>
</phase>


<!-- ======================================================
     8. REPORT Phase
====================================================== -->
<phase id="REPORT">
  <description>
    Generate comprehensive test report with coverage and SoT alignment.
  </description>

  <report_structure>
    ```markdown
    # API Automation Test Report

    **Generated**: YYYY-MM-DD HH:MM:SS
    **Project**: AI Ad Spend System
    **Baseline**: AUTOMATION_TEST_SPEC_v1.4

    ## Executive Summary

    | Metric | Value | Status |
    |--------|-------|--------|
    | Total Tests | N | - |
    | Pass Rate | XX% | OK/WARN/FAIL |
    | Coverage | XX% | OK/WARN/FAIL |
    | SoT Alignment | XX% | OK/WARN/FAIL |

    ## Test Results by Level

    ### L0 Unit Tests
    - Total: N
    - Passed: X
    - Failed: Y
    - Coverage: XX%

    ### L1 Integration Tests
    - Total: N
    - Passed: X
    - Failed: Y
    - Coverage: XX%

    ### L2 API Tests
    - Total: N
    - Passed: X
    - Failed: Y
    - Coverage: XX%

    ## SoT Alignment Matrix

    | SoT Document | Coverage | Missing |
    |--------------|----------|---------|
    | STATE_MACHINE.md | XX/YY transitions | [list] |
    | ERROR_CODES_SOT.md | XX/YY codes | [list] |
    | API_SOT.md | XX/YY endpoints | [list] |
    | AUTH_SPEC.md | XX/YY permissions | [list] |

    ## Failed Test Details

    ### test_module::test_function
    - **Status**: FAILED
    - **Error**: <error message>
    - **Location**: <file>:<line>
    - **SoT Reference**: <relevant SoT>
    - **Suggested Fix**: <recommendation>

    ## Coverage Gaps

    1. **Missing Happy Path**: <module> lacks complete flow test
    2. **Missing Permission Test**: <role> + <action> combination
    3. **Missing Error Code**: <code> not validated

    ## Recommendations

    1. [ ] Add test for <specific scenario>
    2. [ ] Increase coverage for <module>
    3. [ ] Update test to align with SoT v<new_version>
    ```
  </report_structure>
</phase>


<!-- ======================================================
     9. Common Utilities Integration
====================================================== -->
<common_utilities>
  <factories>
    Location: backend/tests/common/factories.py

    Available factories:
    - create_user(db_session, role="media_buyer", **kwargs)
    - create_daily_report(db_session, user, status="raw_submitted", **kwargs)
    - create_topup_request(db_session, user, status="draft", amount=Decimal("1000.00"), **kwargs)

    MUST use factories instead of ad-hoc data creation.
  </factories>

  <state_asserts>
    Location: backend/tests/common/state_asserts.py

    Available assertions:
    - assert_status_transition(entity, expected_status, sot_ref=None)
    - assert_valid_transition(entity_type, from_status, to_status)
    - assert_terminal_state(entity, entity_type)

    State whitelist constants:
    - DAILY_REPORT_TRANSITIONS
    - TOPUP_REQUEST_TRANSITIONS
  </state_asserts>

  <error_helpers>
    Location: backend/tests/common/error_helpers.py

    Available helpers:
    - assert_error_response(response, expected_code, expected_http_status, message_contains=None)
    - assert_success_response(response, expected_http_status=200)

    Common error codes:
    - STATE_001: Invalid state transition
    - STATE_100: Terminal state protection
    - AUTH_501: Permission denied
    - BIZ_100: Invalid amount
    - VALIDATION_001: Missing required field
  </error_helpers>
</common_utilities>


<!-- ======================================================
     10. Usage Examples
====================================================== -->
<usage>
  Example 1: Generate L2 API tests for Daily Report module
  ```
  Use ai-ad-api-automation-test,
  mode = GENERATE,
  target_module = "daily_report",
  test_level = "L2".

  Generate complete test file following AUTOMATION_TEST_SPEC_v1.4.
  ```

  Example 2: Run all L2 API tests
  ```
  Use ai-ad-api-automation-test,
  mode = RUN,
  test_level = "L2",
  output_format = "cli".

  Execute pytest -m api and report results.
  ```

  Example 3: Execute Newman with Postman collection
  ```
  Use ai-ad-api-automation-test,
  mode = NEWMAN,
  collection_path = "collections/daily_report_api.json",
  environment_path = "environments/local.json",
  output_format = "html".

  Run Newman and generate HTML report.
  ```

  Example 4: Generate comprehensive test report
  ```
  Use ai-ad-api-automation-test,
  mode = REPORT,
  output_format = "html".

  Generate full report with coverage and SoT alignment.
  ```
</usage>


<!-- ======================================================
     11. Error Handling
====================================================== -->
<error_handling>
  Scenario 1: Target module not found
  - Report: "Error: Module '<name>' not found in backend/"
  - Suggest: List available modules

  Scenario 2: SoT document not found
  - Report: "Warning: SoT document '<path>' not found"
  - Fallback: Continue with available SoT references

  Scenario 3: Test execution fails
  - Report: Detailed error with stack trace
  - Include: Failed assertion details
  - Suggest: Potential fixes based on error type

  Scenario 4: Newman collection invalid
  - Report: "Error: Invalid Postman collection format"
  - Suggest: Validate JSON structure

  Scenario 5: Coverage below threshold
  - Report: "Warning: Coverage XX% below threshold YY%"
  - List: Uncovered modules/functions
</error_handling>


<!-- ======================================================
     12. Version Notes
====================================================== -->
<VERSION_NOTES>

  ### v1.0 (2025-12-01)

  **Initial Release**
  - Created skill based on sanbercode-api-automation-boilerplate patterns
  - Integrated with AUTOMATION_TEST_SPEC_v1.4.md standards
  - Support for 4 modes: GENERATE, RUN, NEWMAN, REPORT
  - pytest test generation with SoT alignment
  - Newman/Postman collection integration for contract testing
  - HTML report generation via newman-reporter-htmlextra
  - Common utilities integration (factories, state_asserts, error_helpers)

  **Reference Projects**
  - https://github.com/jfrelis/sanbercode-api-automation-boilerplate
  - Newman v6.0.0+
  - newman-reporter-htmlextra v1.22.11+

  **Alignment**
  - MASTER.md v3.5
  - SoT Freeze v2.6
  - AUTOMATION_TEST_SPEC_v1.4.md

</VERSION_NOTES>

</skill>
