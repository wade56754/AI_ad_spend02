# /auto-fix - 自动修复

> **版本**: v1.0
> **优先级**: 高
> **依赖**: Hook 系统, SoT 验证器

---

## 用途

自动检测并修复代码中的常见问题，包括 SoT 合规性、代码风格、废弃 API 等。

---

## 使用方式

```bash
/auto-fix <file>              # 自动修复指定文件
/auto-fix <dir>               # 自动修复目录下所有文件
/auto-fix <file> --dry-run    # 仅预览，不实际修改
/auto-fix <file> --sot        # 仅修复 SoT 相关问题
/auto-fix <file> --style      # 仅修复代码风格问题
/auto-fix --staged            # 修复 git 暂存区的文件
```

---

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `<file>` | 目标文件路径 | `backend/services/*.py` |
| `<dir>` | 目标目录 | `backend/services/` |
| `--dry-run` | 仅预览修复 | |
| `--sot` | 仅 SoT 问题 | |
| `--style` | 仅代码风格 | |
| `--staged` | 仅暂存文件 | |
| `--interactive` | 交互式确认 | |

---

## 自动修复类别

### 1. SoT 合规性修复

| 问题 | 自动修复 |
|------|---------|
| 废弃角色 `supervisor` | → `project_owner` |
| 废弃角色 `media_buyer` | → `pitcher` |
| 废弃角色 `data_operator` | → 删除 |
| Phase 2 状态在 Phase 1 | → 警告标注 |
| 直接余额修改 | → 使用 ledger API |

### 2. 代码风格修复

| 问题 | 自动修复 |
|------|---------|
| 直接 `fetch()` 调用 | → `apiGet()`/`apiPost()` |
| 手写 `<table>` | → `<DataTable>` |
| 缺少 `'use client'` | → 添加指令 |
| 未使用的 import | → 删除 |

### 3. 类型安全修复

| 问题 | 自动修复 |
|------|---------|
| `any` 类型 | → 推断具体类型 |
| 可选链缺失 | → 添加 `?.` |
| 空值检查缺失 | → 添加 `?? default` |

---

## 示例

### 修复单个文件

```bash
/auto-fix backend/routers/daily_reports.py
```

输出:
```
🔍 扫描文件: backend/routers/daily_reports.py

发现 3 个问题:
  🔴 [L45] 废弃角色 'supervisor' → 'project_owner'
  🟡 [L78] 直接 fetch 调用 → apiGet
  🟡 [L92] 缺少错误处理

🔧 自动修复:
  ✅ [L45] 角色已替换
  ✅ [L78] API 调用已替换
  ⚠️ [L92] 需要手动处理

修复完成: 2/3 (1 需手动)
```

### 预览修复

```bash
/auto-fix backend/services/ --dry-run
```

输出:
```
🔍 扫描目录: backend/services/ (12 文件)

将要修复:
  daily_report_service.py: 2 处
  topup_service.py: 1 处
  ledger_service.py: 0 处
  ...

总计: 8 处修复 (--dry-run 模式，未实际修改)
```

---

## 修复规则

### 角色替换规则

```python
ROLE_MAPPING = {
    "supervisor": "project_owner",
    "media_buyer": "pitcher",
    "data_operator": None,  # 删除
}
```

### API 替换规则

```typescript
// 前端
fetch('/api/...') → apiGet('/api/v1/...')
axios.get(...) → apiGet(...)

// 后端
直接 SQL → ORM 查询
硬编码状态 → 枚举常量
```

---

## 集成 Hook 系统

自动修复使用 `.claude/hooks/lib/` 中的验证器:

```python
from .claude.hooks.lib.sot_validator import SoTValidator
from .claude.hooks.lib.compliance_checker import ComplianceChecker

validator = SoTValidator()
issues = validator.validate(content, filepath)

for issue in issues:
    if issue.auto_fixable:
        content = apply_fix(content, issue)
```

---

## 输出

1. 修复后的文件
2. 修复报告 (JSON/Markdown)
3. 需手动处理的问题清单
