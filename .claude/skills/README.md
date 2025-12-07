# SuperClaude Skills 索引

> **版本**: v3.0 | **更新**: 2025-12-07

## 📚 Skills 总览

本目录包含所有 SuperClaude Skill 定义，按功能分类如下：

---

## 🔧 代码生成 Skills

### ai-ad-be-gen
- **路径**: `ai-ad-be-gen/SKILL.md`
- **版本**: v2.0
- **功能**: 后端代码生成（FastAPI + SQLAlchemy + Pydantic）
- **输出**: Schema、Service、Router 三层代码
- **SoT 依赖**: DATA_SCHEMA, STATE_MACHINE, API_SOT, BUSINESS_RULES, ERROR_CODES

**使用示例**:
```
使用 ai-ad-be-gen 实现充值审批 API，
目标文件: schemas/topup.py, services/topup_service.py, routers/topups.py
```

---

### ai-ad-fe-gen
- **路径**: `ai-ad-fe-gen/SKILL.md`
- **版本**: v2.0
- **功能**: 前端代码生成（Next.js + React + TypeScript）
- **输出**: PageShell、hooks、components、services、types
- **技术栈**: Next.js 14+, shadcn/ui, TanStack Query

**使用示例**:
```
使用 ai-ad-fe-gen 实现充值列表页面，模块: topups
```

---

### ai-ad-test-gen
- **路径**: `ai-ad-test-gen/SKILL.md`
- **版本**: v1.0
- **功能**: 测试代码生成
- **输出**: pytest 单元测试、vitest 前端测试

**使用示例**:
```
使用 ai-ad-test-gen 为 topup_service 生成单元测试
```

---

## 📝 文档处理 Skills

### ai-ad-doc-orchestrator
- **路径**: `ai-ad-doc-orchestrator/SKILL.md`
- **版本**: v5.3
- **功能**: 文档编排总控
- **工作流**: 大纲生成 → 审查 → 修订 → 冻结 → 正文生成 → 审查 → 冻结
- **子 Skills**: ai-project-doc-writer, ai-ad-doc-fixer, ai-master-architect

**使用示例**:
```
使用 ai-ad-doc-orchestrator 生成 PROJECT.md，outline_exists = false
```

---

### ai-ad-doc-architect
- **路径**: `ai-ad-doc-architect/SKILL.md`
- **版本**: v2.0
- **功能**: 文档架构设计与一致性审查

**使用示例**:
```
使用 ai-ad-doc-architect 审查 ARCHITECTURE.md 结构
```

---

### ai-ad-doc-fixer
- **路径**: `ai-ad-doc-fixer/skill.md`
- **版本**: v2.0
- **功能**: 文档审查与修复
- **模式**: DOC-ANALYZE（只审不改）、DOC-PATCH（修复）

**使用示例**:
```
使用 ai-ad-doc-fixer 模式 DOC-ANALYZE 审查 PROJECT.md
```

---

### ai-project-doc-writer
- **路径**: `ai-project-doc-writer/skill.md`
- **版本**: v2.0
- **功能**: 文档内容生成
- **模式**: OUTLINE（大纲）、DW-FILL（正文）

**使用示例**:
```
使用 ai-project-doc-writer 模式 OUTLINE 生成 DOMAIN.md 大纲
```

---

### ai-master-architect
- **路径**: `ai-master-architect/skill.md`
- **版本**: v1.0
- **功能**: 宪法级一致性校验（MASTER/SoT 对齐检查）

**使用示例**:
```
使用 ai-master-architect 校验 PROJECT.md 第3章与 MASTER.md 一致性
```

---

## 🛡️ 治理 Skills

### ai-ad-spec-governor
- **路径**: `ai-ad-spec-governor/SKILL.md`
- **版本**: v2.0
- **功能**: SoT 合规治理
- **检查项**: 状态枚举、错误码、字段类型、业务规则

**使用示例**:
```
使用 ai-ad-spec-governor 检查 backend/services/topup_service.py 的 SoT 合规性
```

---

### ai-doc-system-auditor
- **路径**: `ai-doc-system-auditor/SKILL.md`
- **版本**: v1.0
- **功能**: 文档系统审计

**使用示例**:
```
使用 ai-doc-system-auditor 审计整个文档体系
```

---

## 🧪 测试 Skills

### ai-ad-api-automation-test
- **路径**: `ai-ad-api-automation-test/SKILL.md`
- **版本**: v1.0
- **功能**: API 自动化测试设计与执行

**使用示例**:
```
使用 ai-ad-api-automation-test 设计 /api/v1/topups 的自动化测试
```

---

### ai-ad-agents-test-orchestrator
- **路径**: `ai-ad-agents-test-orchestrator/SKILL.md`
- **版本**: v1.0
- **功能**: 测试编排

---

### ai-ad-agents-test-runner
- **路径**: `ai-ad-agents-test-runner/SKILL.md`
- **版本**: v1.0
- **功能**: 测试执行

---

## 🔨 工具 Skills

### prompt-engineer-skill
- **路径**: `prompt-engineer-skill/SKILL.md`
- **版本**: v1.0
- **功能**: Prompt 工程辅助
- **参考文档**:
  - `references/xml-patterns.md`
  - `references/chain-patterns.md`
  - `references/role-patterns.md`

**使用示例**:
```
使用 prompt-engineer-skill 优化这个 Prompt 的结构
```

---

## 📊 Skill 调用链

```
                    ┌─────────────────────────────────┐
                    │   ai-ad-doc-orchestrator        │
                    │   (文档编排总控)                 │
                    └─────────────┬───────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ai-project-     │    │ ai-ad-doc-      │    │ ai-master-      │
│ doc-writer      │    │ fixer           │    │ architect       │
│ (内容生成)       │    │ (审查修复)       │    │ (宪法校验)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

```
┌─────────────────────────────────────────────────────────┐
│                  代码生成工作流                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  需求 ──▶ ai-ad-be-gen ──▶ ai-ad-test-gen              │
│              │                    │                     │
│              ▼                    ▼                     │
│         后端代码              单元测试                   │
│                                                         │
│  需求 ──▶ ai-ad-fe-gen ──▶ ai-ad-test-gen              │
│              │                    │                     │
│              ▼                    ▼                     │
│         前端代码              前端测试                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔗 相关文档

- **主入口**: [../README.md](../README.md)
- **使用指南**: [../SUPERCLAUDE_SETUP.md](../SUPERCLAUDE_SETUP.md)
- **项目规则**: [../PROJECT_RULES.md](../PROJECT_RULES.md)
- **优化报告**: [SKILL_OPTIMIZATION_REPORT_v1.0.md](SKILL_OPTIMIZATION_REPORT_v1.0.md)

---

## 📋 Skill 状态

| Skill | 版本 | 状态 | 最后更新 |
|-------|------|------|----------|
| ai-ad-be-gen | v2.0 | ✅ Production | 2025-12-06 |
| ai-ad-fe-gen | v2.0 | ✅ Production | 2025-12-06 |
| ai-ad-test-gen | v1.0 | ✅ Production | 2025-12-06 |
| ai-ad-doc-orchestrator | v5.3 | ✅ Production | 2025-11-28 |
| ai-ad-doc-architect | v2.0 | ✅ Production | 2025-11-27 |
| ai-ad-doc-fixer | v2.0 | ✅ Production | 2025-11-27 |
| ai-project-doc-writer | v2.0 | ✅ Production | 2025-11-27 |
| ai-master-architect | v1.0 | ✅ Production | 2025-11-27 |
| ai-ad-spec-governor | v2.0 | ✅ Production | 2025-11-27 |
| ai-doc-system-auditor | v1.0 | ✅ Production | 2025-11-27 |
| ai-ad-api-automation-test | v1.0 | ✅ Production | 2025-12-06 |
| prompt-engineer-skill | v1.0 | ✅ Production | 2025-11-25 |

---

**基准**: AI Code Factory v3.0
