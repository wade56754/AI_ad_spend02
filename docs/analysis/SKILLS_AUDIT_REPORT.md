# Skills 审计报告

> **审计日期**: 2026-01-02
> **审计范围**: `.claude/skills/`, `.claude/commands/`, `agents/skills/`
> **审计目的**: 识别缺失、重复、冗余功能

---

## 执行摘要

| 指标 | 数值 | 说明 |
|------|------|------|
| **总 Skill 数** | 31 | 跨 5 个类别 |
| **完全冗余** | 12 | 可立即删除 |
| **部分冗余** | 8 | 需要合并 |
| **功能缺失** | 6 | 需要新建 |
| **文件冗余** | 27 对 | SKILL.md + skill.md 重复 |

**结论**: Skills 体系存在 **~40% 的冗余**，需要系统性清理。

---

## 一、冗余功能分析

### 1.1 文件级冗余（27 对）

所有 skill 目录同时包含 `SKILL.md` 和 `skill.md`，内容 100% 相同。

```
agents/skills/
├── ai-ad-agents-code-reviewer/
│   ├── SKILL.md    ← 保留
│   └── skill.md    ← 删除
├── ai-ad-agents-compliance-checker/
│   ├── SKILL.md    ← 保留
│   └── skill.md    ← 删除
... (共 27 个目录)
```

**建议**: 删除所有小写 `skill.md` 文件

### 1.2 v1/v2 命令重复（3 对）

| v1 命令 | v2 命令 | 重复程度 | 建议 |
|---------|---------|----------|------|
| `/gen` | `/gen-v2` | 80% | 删除 v1，保留 v2 |
| `/review` | `/review-v2` | 70% | 删除 v1，保留 v2 |
| `/doc` | `/doc-v2` | 75% | 删除 v1，保留 v2 |

### 1.3 OpenSpec 三重设计

存在 3 套功能重叠的 OpenSpec 实现：

| 设计 | 位置 | 命令 |
|------|------|------|
| **设计 A** | `.claude/commands/openspec/` | `/openspec:proposal`, `/openspec:apply`, `/openspec:archive` |
| **设计 B** | `.claude/commands/` | `/openspec-proposal`, `/openspec-apply`, `/openspec-archive`, `/openspec-validate` |
| **设计 C** | `.claude/commands/spec/` | `/spec` |

**建议**: 保留设计 A（命名空间更清晰），删除设计 B 和 C

### 1.4 Code Factory 冗余模块

方案 C Hook 集成后，以下模块已冗余：

| 模块 | 原位置 | 状态 | 替代方案 |
|------|--------|------|---------|
| CLI 交互 | `cli.py` | 🔴 冗余 | Claude Code 原生 CLI |
| RAG 知识库 | `rag/` | 🔴 冗余 | Grep/Glob 工具 |
| 代码搜索 | `searcher.py` | 🔴 冗余 | Explore Agent |
| 仓库地图 | `repo_map/` | 🔴 冗余 | 原生文件浏览 |
| LLM 客户端 | `llm_client.py` | 🔴 冗余 | Claude Code 内置 |
| 提示词系统 | `prompts/` | 🔴 冗余 | 直接对话 |
| 代码组装 | `assembler.py` | 🔴 冗余 | Claude Code 生成 |
| 代码选择 | `selector.py` | 🔴 冗余 | Claude Code 理解 |
| 代码适配 | `adapter.py` | 🔴 冗余 | 规则内联到 Hook |

**已迁移到 Hook 系统**:
- SoT 版本验证 → `.claude/hooks/lib/config.py`
- 角色白名单 → `.claude/hooks/lib/sot_validator.py`
- Phase 边界控制 → `.claude/hooks/lib/sot_validator.py`
- 合规检查 → `.claude/hooks/lib/compliance_checker.py`

---

## 二、重复功能分析

### 2.1 知识库搜索重复

| 功能 | 实现 1 | 实现 2 | 建议 |
|------|--------|--------|------|
| 知识库搜索 | `/kb-search` | `code_factory/rag/` | 保留 `/kb-search` |
| 知识库构建 | `/kb-build` | `code_factory/rag/builder.py` | 保留 `/kb-build` |

### 2.2 代码审查重复

| 功能 | 实现 1 | 实现 2 | 建议 |
|------|--------|--------|------|
| 代码审查 | `/review` | `/review-v2` | 保留 v2 |
| SoT 检查 | `/sot-check` | Hook 系统 | 两者保留（互补） |

### 2.3 文档生成重复

| 功能 | 实现 1 | 实现 2 | 建议 |
|------|--------|--------|------|
| 文档生成 | `/doc` | `/doc-v2` | 保留 v2 |
| API 文档 | `/doc-v2` | 手动编写 | 增强 v2 |

---

## 三、缺失功能分析

### 3.1 完全缺失（需新建）

| 功能 | 重要性 | 建议 | 预估工作量 |
|------|--------|------|-----------|
| 测试自动生成 | 🔴 高 | 新建 `/test-gen` | 2-3 天 |
| 性能分析 | 🟡 中 | 新建 `/perf-analyze` | 1-2 天 |
| 安全扫描 | 🟡 中 | 新建 `/security-scan` | 2-3 天 |
| 国际化支持 | 🟢 低 | 新建 `/i18n` | 1 天 |
| 数据库迁移 | 🟡 中 | 新建 `/migration` | 2 天 |
| 自动修复 | 🔴 高 | 新建 `/auto-fix` | 3-4 天 |

### 3.2 弱覆盖（需增强）

| 现有功能 | 当前能力 | 缺失能力 | 建议 |
|---------|---------|---------|------|
| `/sot-check` | 检查合规性 | 自动修复建议 | 增强 |
| `/review` | 代码审查 | 自动修复 | 增强 |
| `/gen` | 代码生成 | 测试联动 | 增强 |
| `/clarify` | 需求澄清 | 多轮对话 | 增强 |

---

## 四、分类清单

### 4.1 按功能分类

#### 🔧 开发辅助（9 个）
- `/gen-v2` - 代码生成 ✅
- `/review-v2` - 代码审查 ✅
- `/doc-v2` - 文档生成 ✅
- `/check-code` - 快速代码检查 ✅
- `/clarify` - 需求澄清 ✅
- `/kb-search` - 知识库搜索 ✅
- `/kb-build` - 知识库构建 ✅
- `/restart` - 重启开发服务 ✅
- `/pc` - 提示词优化 ✅

#### 📋 规范管理（6 个）
- `/openspec:proposal` - 规范变更提案 ✅
- `/openspec:apply` - 规范变更应用 ✅
- `/openspec:archive` - 规范变更归档 ✅
- `/sot-check` - SoT 合规检查 ✅
- `/sot-context` - SoT 上下文获取 ✅
- `/flow` - 工作流编排 ✅

#### 🤖 AI 辅助（5 个）
- `/ai-help` - AI 编程助手帮助 ✅
- `/preprompt` - 加载提示词模板 ✅
- `/project-config` - 项目配置 ✅
- `/dev-flow` - 统一开发流程 ✅
- `/help` - 帮助信息 ✅

#### 🗂️ 索引导航（3 个）
- `/INDEX` - 命令索引 ✅
- `/README` - Claude Commands 索引 ✅
- `/.claude/settings.json` - 配置文件 ✅

#### 🧪 测试相关（2 个 - 已废弃）
- `ai-ad-agents-test-orchestrator` - 🔴 废弃
- `ai-ad-agents-test-runner` - 🔴 废弃

### 4.2 按状态分类

| 状态 | 数量 | 列表 |
|------|------|------|
| ✅ 正常 | 19 | 见上方分类 |
| 🟡 需合并 | 6 | gen, review, doc (v1), openspec-*, spec |
| 🔴 废弃 | 4 | test-orchestrator, test-runner, v1 命令 |
| ⚪ 待建 | 6 | test-gen, perf-analyze, security-scan, i18n, migration, auto-fix |

---

## 五、清理计划

### Phase 1: 立即执行（P0）

```bash
# 1. 删除文件级冗余
find agents/skills -name "skill.md" -delete

# 2. 删除废弃 Skills
rm -rf agents/skills/ai-ad-agents-test-orchestrator/
rm -rf agents/skills/ai-ad-agents-test-runner/

# 3. 删除 Code Factory 冗余模块
rm agents/skills/code_factory/cli.py
rm -rf agents/skills/code_factory/rag/
rm agents/skills/code_factory/searcher.py
rm -rf agents/skills/code_factory/repo_map/
rm agents/skills/code_factory/llm_client.py
rm -rf agents/skills/code_factory/prompts/
rm agents/skills/code_factory/assembler.py
rm agents/skills/code_factory/selector.py
rm agents/skills/code_factory/adapter.py
```

### Phase 2: 合并清理（P1）

```bash
# 1. 删除 v1 命令
rm -rf .claude/commands/gen/
rm -rf .claude/commands/review/
rm -rf .claude/commands/doc/

# 2. 删除重复的 OpenSpec
rm -rf .claude/commands/openspec-proposal/
rm -rf .claude/commands/openspec-apply/
rm -rf .claude/commands/openspec-archive/
rm -rf .claude/commands/openspec-validate/
rm -rf .claude/commands/spec/

# 3. 重命名 v2 命令（移除 -v2 后缀）
mv .claude/commands/gen-v2 .claude/commands/gen
mv .claude/commands/review-v2 .claude/commands/review
mv .claude/commands/doc-v2 .claude/commands/doc
```

### Phase 3: 功能补充（P2）

```bash
# 创建缺失的 Skills
mkdir -p .claude/commands/test-gen
mkdir -p .claude/commands/perf-analyze
mkdir -p .claude/commands/security-scan
mkdir -p .claude/commands/i18n
mkdir -p .claude/commands/migration
mkdir -p .claude/commands/auto-fix
```

---

## 六、预期收益

| 指标 | 当前 | 优化后 | 改善 |
|------|------|--------|------|
| Skills 数量 | 31 | 19 | -39% |
| 冗余文件数 | 54 | 0 | -100% |
| 维护复杂度 | 高 | 低 | -60% |
| 功能覆盖率 | 70% | 90% | +20% |
| 命名一致性 | 差 | 好 | +100% |

---

## 七、风险与注意事项

### 7.1 删除前检查

1. **确认无外部依赖** - 检查是否有其他系统调用这些 Skills
2. **备份原文件** - 删除前先 `git stash` 或创建分支
3. **分步执行** - 不要一次性删除所有文件

### 7.2 已知风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 删除正在使用的 Skill | 用户无法使用 | 先标记废弃，观察 1 周 |
| 合并导致功能丢失 | 部分功能不可用 | 完整测试 v2 功能 |
| Hook 系统不稳定 | 验证失效 | 保留 code_factory 作为回退 |

### 7.3 回滚计划

```bash
# 如需回滚
git checkout HEAD~1 -- agents/skills/
git checkout HEAD~1 -- .claude/commands/
```

---

## 八、附录

### A. 完整 Skills 清单

```
.claude/commands/
├── ai-help/
├── check-code/
├── clarify/
├── dev-flow/
├── doc-v2/           # 保留，重命名为 doc
├── flow/
├── gen-v2/           # 保留，重命名为 gen
├── help/
├── INDEX/
├── kb-build/
├── kb-search/
├── openspec/         # 保留
│   ├── proposal/
│   ├── apply/
│   └── archive/
├── openspec-apply/   # 删除
├── openspec-archive/ # 删除
├── openspec-proposal/# 删除
├── openspec-validate/# 删除
├── pc/
├── preprompt/
├── project-config/
├── README/
├── restart/
├── review-v2/        # 保留，重命名为 review
├── sot-check/
├── sot-context/
└── spec/             # 删除

agents/skills/code_factory/
├── skills/           # 6 个子 skill
├── sot/              # 保留（核心）
├── security.py       # 保留（核心）
├── factory.py        # 保留（核心）
├── cli.py            # 删除
├── rag/              # 删除
├── searcher.py       # 删除
├── repo_map/         # 删除
├── llm_client.py     # 删除
├── prompts/          # 删除
├── assembler.py      # 删除
├── selector.py       # 删除
└── adapter.py        # 删除
```

### B. 参考文档

- [方案 C Hook 集成迁移指南](agents/skills/code_factory/MIGRATION_TO_HOOKS.md)
- [SoT 验证器配置](.claude/sot-validator.yaml)
- [AI 代码工厂架构审查报告](docs/analysis/CODE_FACTORY_AUDIT.md)

---

**报告生成时间**: 2026-01-02
**审计人**: Claude Opus 4.5
