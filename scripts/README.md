# 文档验证脚本

> **版本**: v1.0
> **更新日期**: 2025-11-16
> **用途**: 自动化验证文档规则一致性

---

## 📋 脚本说明

### validate-docs.py (推荐)
**Python版本** - 完整的文档规则验证工具

**检查项**:
1. ✅ Next.js版本统一性（应为16.0.2）
2. ✅ 错误码命名规范（SYS_*/BIZ_*/SEC_*前缀）
3. ✅ AppShell废弃检查（应迁移到AppLayout）
4. ✅ API响应timestamp格式（ISO 8601含毫秒）
5. ✅ 文档链接有效性（断链检测）

**使用方法**:
```bash
# 安装Python 3.7+后直接运行
python scripts/validate-docs.py

# 或使其可执行
chmod +x scripts/validate-docs.py
./scripts/validate-docs.py
```

**输出示例**:
```
ℹ️  开始文档规则一致性验证...

ℹ️  检查1: Next.js版本统一性...
✅ Next.js版本检查通过

ℹ️  检查2: 错误码命名规范...
✅ 错误码规范检查通过

...

============================================================
✅ 所有检查通过！文档规则一致性验证成功 🎉
```

---

### validate-docs.sh
**Bash版本** - 快速验证核心规则

**检查项**:
1. ✅ Next.js版本统一性
2. ✅ 错误码命名规范
3. ✅ AppShell废弃检查
4. ✅ TODO标记检测

**使用方法**:
```bash
# Git Bash / Linux / macOS
chmod +x scripts/validate-docs.sh
./scripts/validate-docs.sh

# Windows Git Bash
bash scripts/validate-docs.sh
```

---

## 🚀 CI/CD集成

### GitHub Actions示例
```yaml
name: 文档验证

on: [push, pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: 验证文档规则
        run: python scripts/validate-docs.py
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "运行文档验证..."
python scripts/validate-docs.py
if [ $? -ne 0 ]; then
    echo "文档验证失败，请修复后再提交"
    exit 1
fi
```

---

## 🔧 开发建议

### 提交前检查
```bash
# 1. 运行文档验证
python scripts/validate-docs.py

# 2. 前端类型检查
cd frontend && pnpm type-check

# 3. 后端测试
cd backend && pytest
```

### 文档修改后
```bash
# 修改文档后立即验证
python scripts/validate-docs.py

# 只检查特定规则（手动grep）
grep -rn "Next.js" docs/ --include="*.md"
```

---

## 📊 验证规则详解

### 1. Next.js版本统一性
**规则**: 所有文档中的Next.js版本必须为 `16.0.2`

**错误示例**:
```markdown
❌ Next.js 14.x
❌ Next.js 15.0.0
```

**正确示例**:
```markdown
✅ Next.js 16.0.2
```

---

### 2. 错误码命名规范
**规则**: 所有错误码必须使用 `SYS_*`、`BIZ_*`、`SEC_*` 前缀或 `SUCCESS`

**错误示例**:
```json
❌ "code": "VALIDATION_ERROR"
❌ "code": "NOT_FOUND"
```

**正确示例**:
```json
✅ "code": "BIZ_VALIDATION_ERROR"
✅ "code": "BIZ_NOT_FOUND"
✅ "code": "SEC_AUTHORIZATION_DENIED"
```

**参考**: [ERROR_CODES.md](../docs/ERROR_CODES.md)

---

### 3. AppShell废弃检查
**规则**: 不应在文档中推荐使用已废弃的 `AppShell` 组件

**错误示例**:
```tsx
❌ import AppShell from '@/components/layout/AppShell'
❌ <AppShell>...</AppShell>
```

**正确示例**:
```tsx
✅ import AppLayout from '@/components/layout/AppLayout'
✅ <AppLayout>...</AppLayout>
```

**例外**: 迁移指南和废弃说明可以提及AppShell

**参考**: [COMPONENT_MIGRATION.md](../docs/COMPONENT_MIGRATION.md)

---

### 4. API响应时间戳格式
**规则**: timestamp字段必须使用ISO 8601格式，包含毫秒

**错误示例**:
```json
❌ "timestamp": "2025-11-16T10:30:00Z"
```

**正确示例**:
```json
✅ "timestamp": "2025-11-16T10:30:00.000Z"
```

**参考**: [API_RULEBOOK.md](../docs/API_RULEBOOK.md)

---

### 5. 文档链接有效性
**规则**: 文档中的相对链接必须指向存在的文件

**错误示例**:
```markdown
❌ [开发指南](./DELETED_FILE.md)
```

**正确示例**:
```markdown
✅ [开发指南](./FRONTEND_GUIDE.md)
```

---

## 🛠️ 故障排除

### Python脚本无法运行
```bash
# 检查Python版本
python --version  # 需要3.7+

# Windows用户可能需要
python3 scripts/validate-docs.py
```

### Bash脚本权限问题
```bash
# Linux/macOS
chmod +x scripts/validate-docs.sh

# Windows
# 使用 Git Bash 或 WSL
bash scripts/validate-docs.sh
```

### 验证失败如何修复？
1. 查看脚本输出的具体文件和行号
2. 参考上述规则详解修复问题
3. 重新运行验证直到通过

---

## 📞 相关资源

- [API开发总规则](../docs/API_RULEBOOK.md)
- [错误码字典](../docs/ERROR_CODES.md)
- [组件迁移指南](../docs/COMPONENT_MIGRATION.md)
- [前端开发规则](../docs/rule/FRONTEND_DEVELOPMENT_RULES.md)

---

**维护者**: 项目架构团队
**最后更新**: 2025-11-16
