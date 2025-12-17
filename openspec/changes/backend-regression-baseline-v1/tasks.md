# Tasks: Backend Regression Baseline v1.0

**Status**: IN PROGRESS
**Last Updated**: 2025-12-02

## 1. OpenSpec Scaffold ✅

- [x] 1.1 Create `openspec/changes/backend-regression-baseline-v1/` directory
- [x] 1.2 Create `proposal.md`
- [x] 1.3 Create `tasks.md`
- [ ] 1.4 Run `openspec validate backend-regression-baseline-v1 --strict` (final validation)

## 2. Update AUTOMATION_TEST_SPEC ✅

- [x] 2.1 Add Section 11.7 "回归基线管理" to `docs/testing/AUTOMATION_TEST_SPEC_v1.4.md`
  - [x] 2.1.1 Define regression baseline v1.0
  - [x] 2.1.2 Document baseline comparison method
  - [x] 2.1.3 Document baseline maintenance process
  - [x] 2.1.4 Reference `BACKEND_REGRESSION_FREEZE_REPORT_v1.0.md`

## 3. Update SKILL.md ✅

- [x] 3.1 Add regression baseline reference to `.claude/skills/ai-ad-api-automation-test/SKILL.md`
  - [x] 3.1.1 Add baseline report reference in dependencies section
  - [x] 3.1.2 Update regression test execution instructions
  - [x] 3.1.3 Add baseline comparison requirement

## 4. Update OpenSpec Conventions ✅

- [x] 4.1 Update `openspec/AGENTS.md` change workflow
  - [x] 4.1.1 Add mandatory regression test task requirement
  - [x] 4.1.2 Specify affected change scopes (API/state machine)
  - [x] 4.1.3 Add example tasks.md entry

## 5. Verification

- [ ] 5.1 Run regression tests to ensure still passing:
```bash
python run_tests.py --type regression
```
Expected: 198 passed, 0 failed

- [ ] 5.2 Verify all documentation updates are complete
- [ ] 5.3 Verify OpenSpec validate passes

## 6. OpenSpec Archive

- [ ] 6.1 Update proposal.md status to "READY FOR ARCHIVE"
- [ ] 6.2 Run `openspec validate backend-regression-baseline-v1 --strict`
- [ ] 6.3 Run `openspec archive backend-regression-baseline-v1 --yes`
- [ ] 6.4 Verify archive completed successfully

---

## Summary

| Category | Before | After |
|----------|--------|-------|
| Regression Baseline | Not formally registered | Registered as v1.0 |
| AUTOMATION_TEST_SPEC | Missing baseline section | Section 11.7 added |
| SKILL.md | No baseline reference | Baseline reference added |
| OpenSpec Conventions | No mandatory regression task | Mandatory task requirement added |
| Documentation | Baseline report exists but not referenced | Fully integrated into docs |

**Ready for Archive**: PENDING VALIDATION

## Mandatory Regression Test Task Template

For any change affecting API or state machine, add this to `tasks.md`:

```markdown
## N. Regression Test Verification

- [ ] N.1 Run regression test suite:
```bash
python run_tests.py --type regression
```
- [ ] N.2 Verify all tests pass (compare with baseline v1.0)
- [ ] N.3 Document any new failures or skipped tests
- [ ] N.4 If tests fail, fix code or update baseline (with approval)
```

**Affected Change Scopes** (MUST include regression test task):
- `backend/routers/*` - Any router changes
- `backend/services/*` - Any service changes  
- `docs/2.sot/*` - Any SoT document changes (API_SOT, STATE_MACHINE, etc.)
- `.claude/skills/ai-ad-api-automation-test/*` - Test automation skill changes

