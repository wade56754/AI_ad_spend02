# 质量门禁规范

> 所有门禁必须产出可验证的证据，不接受口头确认。

---

## 1. PR门禁（CI自动执行）

### 1.1 单元测试
```bash
# 命令
pytest -q --cov=backend --cov-report=xml

# 通过条件
- 全部测试通过（exit code = 0）
- 变更文件覆盖率 >= 70%
- 总覆盖率不低于上次（ratchet机制）

# 证据产物
- reports/coverage.xml
- reports/pytest-report.html
```

### 1.2 代码检查
```bash
# 命令
ruff check . && ruff format --check .
mypy backend/ --strict

# 通过条件
- 无错误（exit code = 0）
- 无新增 type: ignore

# 证据产物
- CI日志
```

### 1.3 迁移可回滚
```bash
# 检查命令
python scripts/check_migration.py

# 通过条件
- 每个migration文件必须有对应的downgrade
- 或在 migrations/EXEMPTIONS.md 中说明豁免原因并经过review

# 证据产物
- scripts/check_migration.py 输出
- 豁免需要PR中有明确的reviewer approval
```

### 1.4 CHANGELOG更新
```bash
# 检查命令
python scripts/check_changelog.py

# 通过条件
- docs/sot/CHANGELOG.md 有新增条目
- 条目包含PR编号和版本号
- 格式符合 Keep a Changelog 规范

# 证据产物
- git diff docs/sot/CHANGELOG.md
```

---

## 2. 上线门禁（人工+自动混合）

### 2.1 验收测试
```bash
# 命令
pytest tests/acceptance/ -v --html=reports/acceptance.html
# 或 API契约测试
schemathesis run openapi.json --base-url=http://staging

# 通过条件
- 全部验收用例通过
- 覆盖 MASTER.md Part C 的18项验收清单

# 证据产物
- reports/acceptance.html
- 截图/录屏（UI相关）
```

### 2.2 老板确认
```markdown
# 证据形式（三选一）
1. docs/releases/YYYY-MM-DD-vX.X.X.md 中有老板签字章节
2. GitHub Release PR 有 ceo-approved label
3. 飞书/钉钉审批单截图存入 docs/releases/approvals/

# 禁止
- 口头确认
- 微信消息（除非截图归档）
```

### 2.3 回滚点确认
```bash
# 上线前必须执行
git tag pre-release-$(date +%Y%m%d)
alembic stamp head  # 记录当前数据库版本

# 证据产物
- Git tag
- 数据库版本快照
```

---

## 3. 门禁检查清单（CI/CD使用）

```yaml
# .github/workflows/ci.yml 中的jobs
pr_gates:
  - test: pytest -q --cov
  - lint: ruff check . && ruff format --check .
  - types: mypy backend/ --strict
  - migration: python scripts/check_migration.py
  - changelog: python scripts/check_changelog.py

release_gates:
  - acceptance: pytest tests/acceptance/
  - contract: schemathesis run openapi.json
  - approval: check-label ceo-approved
  - tag: git tag pre-release-*
```

---

## 4. 豁免流程

如果某条门禁无法满足，必须：

1. 在PR描述中说明原因
2. 在 `docs/exemptions/YYYY-MM-DD-{issue}.md` 中记录
3. 获得Tech Lead + 老板双重approval
4. 设定修复deadline

**格式**：
```markdown
# 豁免申请：[简述]

- **日期**: 2025-12-27
- **申请人**: @xxx
- **影响门禁**: 迁移可回滚
- **原因**: 该迁移涉及数据重构，无法自动回滚
- **替代方案**: 手工回滚脚本 scripts/rollback_xxx.sql
- **修复计划**: 下版本补充自动化回滚
- **审批**: 
  - [ ] Tech Lead @yyy
  - [ ] CEO @zzz
```
