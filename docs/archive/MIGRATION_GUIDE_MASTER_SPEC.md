# Master Specification 迁移指南

> **文档版本**: v1.0
> **发布日期**: 2025-11-20
> **维护团队**: 系统架构团队
> **文档状态**: ✅ 迁移指南 (执行手册)

---

## 📋 迁移背景

### 变更说明

**已完成操作**:
- ✅ 已创建统一的核心开发手册: `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (v2.0)
- ✅ 合并了两份旧文档的全部有效内容:
  - `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` (v3.x, 395行)
  - `docs/core/MASTER_DESIGN_DOCUMENT.md` (v1.0, 2527行)
- ✅ 文档总计 2140 行,包含 6 章正文 + 5 个附录

**合并内容清单** (从旧文档吸收的 5 项):
1. 分页响应 meta 字段示例 (第 1 章 1.2.2 节)
2. 状态流转校验代码示例 (第 2 章 2.3.1 节)
3. 测试覆盖率目标表格 (第 6 章 6.4 节)
4. 历史方案归档说明 (附录 D)
5. 开发承诺与规范 (附录 E)

### 迁移目标

1. **统一真相源**: 确保团队所有成员(人类+AI)引用同一份主规范文档
2. **清理冗余**: 归档旧文档,避免版本混淆
3. **更新配置**: 修正所有项目配置文件中的文档路径引用
4. **平稳过渡**: 提供清晰的沟通计划和回退策略

---

## 1. 旧文档归档方案

### 1.1 归档目录结构

建议创建以下归档目录:

```
docs/
├── _archive/
│   └── 2025-11-20_master_spec_merge/
│       ├── AI_AD_SYSTEM_MAIN_DOCUMENT.md       (旧 v3.x)
│       ├── MASTER_DESIGN_DOCUMENT.md           (旧 v1.0)
│       ├── MERGE_ANALYSIS.md                   (diff 分析记录)
│       └── README.md                           (归档说明)
└── core/
    ├── AI_AD_SYSTEM_MASTER_SPEC.md            (✅ 新统一文档)
    ├── DATA_SCHEMA.md                          (保持不变)
    ├── STATE_MACHINE.md                        (保持不变)
    └── ...
```

### 1.2 执行步骤

#### Step 1.2.1: 创建归档目录

```bash
# 在项目根目录执行
mkdir -p docs/_archive/2025-11-20_master_spec_merge
```

#### Step 1.2.2: 移动旧文档到归档目录

```bash
# 移动旧文档
git mv docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md docs/_archive/2025-11-20_master_spec_merge/
git mv docs/core/MASTER_DESIGN_DOCUMENT.md docs/_archive/2025-11-20_master_spec_merge/
```

#### Step 1.2.3: 创建归档说明文件

在 `docs/_archive/2025-11-20_master_spec_merge/README.md` 中写入:

```markdown
# Master Specification 合并归档

## 归档日期
2025-11-20

## 归档原因
这两份文档已合并为统一的核心开发手册,位于:
- **新文档路径**: `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (v2.0)

## 归档文件说明

### AI_AD_SYSTEM_MAIN_DOCUMENT.md
- **原版本**: v3.x
- **最后更新**: 2025-11-17
- **行数**: 395 行
- **定位**: SoT-Implementation (实现规范)
- **合并到新文档的内容**:
  - Section 6.4: 分页响应示例
  - Section 4.2: 状态流转校验代码
  - Section 9: 测试覆盖率表格
  - Appendix A: 历史方案归档
  - 开发承诺章节

### MASTER_DESIGN_DOCUMENT.md
- **原版本**: v1.0
- **最后更新**: 2025-11-20
- **行数**: 2527 行
- **定位**: 核心开发手册 (完整 6 章结构)
- **作用**: 作为新文档的结构骨架

## 如何查阅历史版本

**Git 历史记录**:
```bash
# 查看旧文档最后一次修改
git log --follow docs/_archive/2025-11-20_master_spec_merge/AI_AD_SYSTEM_MAIN_DOCUMENT.md

# 查看完整变更历史
git log --all --full-history -- "**/AI_AD_SYSTEM_MAIN_DOCUMENT.md"
```

**迁移后引用规范**:
- ❌ 禁止: 在新代码/文档中引用归档文件路径
- ✅ 推荐: 所有引用指向 `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md`

## 团队通知

已通过以下渠道通知团队:
- [ ] 项目 Wiki 更新公告
- [ ] 团队例会说明
- [ ] Slack/钉钉频道通知
- [ ] PR 描述中说明变更

## 回退策略

如发现新文档存在重大遗漏或错误:
1. 从归档目录恢复旧文档
2. 执行回退命令:
   ```bash
   git mv docs/_archive/2025-11-20_master_spec_merge/AI_AD_SYSTEM_MAIN_DOCUMENT.md docs/core/
   git mv docs/_archive/2025-11-20_master_spec_merge/MASTER_DESIGN_DOCUMENT.md docs/core/
   ```
3. 提交 Issue 说明问题,重新评估合并方案

---

**维护团队**: 系统架构团队
**审核者**: [待填写]
```

### 1.3 为旧文档添加废弃声明

#### 方案 A: 在旧文档顶部添加警告标记 (推荐)

在归档前,先编辑旧文档添加废弃声明:

**`AI_AD_SYSTEM_MAIN_DOCUMENT.md` 顶部添加**:
```markdown
> ⚠️ **废弃声明 (DEPRECATED)**
> **废弃日期**: 2025-11-20
> **新文档路径**: [`docs/core/AI_AD_SYSTEM_MASTER_SPEC.md`](../core/AI_AD_SYSTEM_MASTER_SPEC.md) (v2.0)
> **原因**: 已与 MASTER_DESIGN_DOCUMENT.md 合并为统一主规范
> **本文档状态**: 仅供历史参考,禁止作为开发依据
> **如需查阅最新规范**: 请访问新文档
```

**`MASTER_DESIGN_DOCUMENT.md` 顶部添加**:
```markdown
> ⚠️ **废弃声明 (DEPRECATED)**
> **废弃日期**: 2025-11-20
> **新文档路径**: [`docs/core/AI_AD_SYSTEM_MASTER_SPEC.md`](../core/AI_AD_SYSTEM_MASTER_SPEC.md) (v2.0)
> **原因**: 已与 AI_AD_SYSTEM_MAIN_DOCUMENT.md 合并为统一主规范
> **本文档状态**: 仅供历史参考,禁止作为开发依据
> **如需查阅最新规范**: 请访问新文档
```

#### 方案 B: 完全删除旧文档 (激进方案)

如果团队确信新文档已完全覆盖所有内容,可直接删除:
```bash
git rm docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md
git rm docs/core/MASTER_DESIGN_DOCUMENT.md
```

**⚠️ 风险警告**: 此方案无法通过文件系统直接回退,仅可通过 Git 历史恢复。

---

## 2. 项目配置文件更新

### 2.1 需要更新的配置文件清单

| 文件路径 | 当前引用 | 需修改为 | 优先级 |
|---------|---------|---------|-------|
| `.project-rules.md` | 可能引用旧路径 | `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` | **P0** |
| `CLAUDE.md` | 可能引用旧路径 | `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` | **P0** |
| `.cursorrules` | 可能引用旧路径 | `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` | **P0** |
| `README.md` | 可能包含文档链接 | 更新文档索引链接 | P1 |
| `.github/PULL_REQUEST_TEMPLATE.md` | 可能引用开发规范 | 更新 Code Review 检查清单链接 | P1 |
| `docs/README.md` | 文档目录索引 | 更新主规范链接 | P1 |

### 2.2 具体修改方案

#### 2.2.1 `.project-rules.md` 更新

**查找替换操作**:
```bash
# 查找所有旧文档引用
grep -n "AI_AD_SYSTEM_MAIN_DOCUMENT\|MASTER_DESIGN_DOCUMENT" .project-rules.md

# 替换为新路径 (示例)
sed -i 's|docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md|docs/core/AI_AD_SYSTEM_MASTER_SPEC.md|g' .project-rules.md
sed -i 's|docs/core/MASTER_DESIGN_DOCUMENT.md|docs/core/AI_AD_SYSTEM_MASTER_SPEC.md|g' .project-rules.md
```

**推荐内容示例**:
```markdown
# 项目规则总纲

## 核心文档引用顺序

开发前必须阅读以下文档:

1. **核心开发手册** (最高优先级): [`docs/core/AI_AD_SYSTEM_MASTER_SPEC.md`](docs/core/AI_AD_SYSTEM_MASTER_SPEC.md) (v2.0)
2. **数据结构 SoT**: [`docs/core/DATA_SCHEMA.md`](docs/core/DATA_SCHEMA.md)
3. **状态机 SoT**: [`docs/core/STATE_MACHINE.md`](docs/core/STATE_MACHINE.md)
4. **错误码 SoT**: [`docs/ERROR_CODES.md`](docs/ERROR_CODES.md)
5. **API 开发流程**: [`docs/core/API_DEVELOPMENT_FLOW.md`](docs/core/API_DEVELOPMENT_FLOW.md)

## 冲突仲裁规则

当文档之间出现冲突时,按以下优先级仲裁:
- **最高权威**: `AI_AD_SYSTEM_MASTER_SPEC.md` (本手册)
- **数据结构**: `DATA_SCHEMA.md`
- **状态流转**: `STATE_MACHINE.md`
- **错误处理**: `ERROR_CODES.md`
```

#### 2.2.2 `CLAUDE.md` 更新

**当前可能的内容** (假设):
```markdown
# Claude AI 协作指南

## 必读文档

在生成任何代码前,必须加载:
- `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`  ← 旧路径
- `docs/core/DATA_SCHEMA.md`
```

**更新为**:
```markdown
# Claude AI 协作指南

## 必读文档

在生成任何代码前,必须按以下顺序加载:

1. **核心开发手册**: `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (v2.0) ← **新统一文档**
2. **数据结构 SoT**: `docs/core/DATA_SCHEMA.md`
3. **状态机 SoT**: `docs/core/STATE_MACHINE.md`
4. **错误码 SoT**: `docs/ERROR_CODES.md`
5. **对应模块文档**: `docs/modules/[具体模块]/`

## 关键约束提醒

- ❌ 禁止引用已归档的旧文档 (`docs/_archive/2025-11-20_master_spec_merge/`)
- ✅ 所有角色仅为 5 个合法值: `admin`, `finance`, `data_operator`, `account_manager`, `media_buyer`
- ✅ 字段/表引用必须与 `DATA_SCHEMA.md` 一致
- ✅ 状态流转必须符合 `STATE_MACHINE.md`
- ✅ 错误码必须来自 `ERROR_CODES.md`
```

#### 2.2.3 `.cursorrules` 更新

**查找替换操作**:
```bash
# 查找旧引用
grep -n "AI_AD_SYSTEM_MAIN_DOCUMENT\|MASTER_DESIGN_DOCUMENT" .cursorrules

# 替换为新路径
sed -i 's|AI_AD_SYSTEM_MAIN_DOCUMENT.md|AI_AD_SYSTEM_MASTER_SPEC.md|g' .cursorrules
sed -i 's|MASTER_DESIGN_DOCUMENT.md|AI_AD_SYSTEM_MASTER_SPEC.md|g' .cursorrules
```

**推荐规则示例**:
```yaml
# .cursorrules

rules:
  - name: "强制加载核心文档"
    trigger: "before_code_generation"
    action: "load_documents"
    files:
      - "docs/core/AI_AD_SYSTEM_MASTER_SPEC.md"  # ✅ 新统一文档
      - "docs/core/DATA_SCHEMA.md"
      - "docs/core/STATE_MACHINE.md"
      - "docs/ERROR_CODES.md"

  - name: "禁止引用归档文档"
    trigger: "path_reference"
    pattern: "docs/_archive/.*"
    action: "reject"
    message: "禁止引用归档文档,请使用 docs/core/AI_AD_SYSTEM_MASTER_SPEC.md"
```

#### 2.2.4 其他配置文件

**`README.md` 更新示例**:
```markdown
# AI 广告代投系统

## 📚 文档索引

- **核心开发手册**: [AI_AD_SYSTEM_MASTER_SPEC.md](docs/core/AI_AD_SYSTEM_MASTER_SPEC.md) (v2.0) ← **主规范**
- **数据结构规范**: [DATA_SCHEMA.md](docs/core/DATA_SCHEMA.md)
- **状态机规范**: [STATE_MACHINE.md](docs/core/STATE_MACHINE.md)
- **错误码规范**: [ERROR_CODES.md](docs/ERROR_CODES.md)
- **RLS 策略决策**: [RLS_STRATEGY_DECISION.md](docs/RLS_STRATEGY_DECISION.md)
```

**`.github/PULL_REQUEST_TEMPLATE.md` 更新示例**:
```markdown
## Code Review 检查清单

请在提交 PR 前自检以下项目 (详见 [核心开发手册 6.3 节](../docs/core/AI_AD_SYSTEM_MASTER_SPEC.md#63-code-review检查清单)):

**架构与设计**:
- [ ] 代码遵循 Router→Service→Model 三层架构
- [ ] 所有字段定义与 `DATA_SCHEMA.md` 一致
- [ ] 状态枚举引用 `STATE_MACHINE.md`
```

### 2.3 自动化检查脚本 (可选)

创建 `scripts/check_doc_references.sh` 用于 CI/CD 检查:

```bash
#!/bin/bash
# 检查是否存在对旧文档的引用

echo "🔍 检查旧文档引用..."

# 定义旧文档路径模式
OLD_PATTERNS=(
  "AI_AD_SYSTEM_MAIN_DOCUMENT.md"
  "MASTER_DESIGN_DOCUMENT.md"
  "docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT"
  "docs/core/MASTER_DESIGN_DOCUMENT"
)

# 排除归档目录和 Git 目录
EXCLUDE_DIRS="--exclude-dir=docs/_archive --exclude-dir=.git --exclude-dir=node_modules"

FOUND_ISSUES=0

for pattern in "${OLD_PATTERNS[@]}"; do
  echo "检查模式: $pattern"

  # 在关键配置文件中搜索
  RESULTS=$(grep -r $EXCLUDE_DIRS "$pattern" \
    .project-rules.md \
    CLAUDE.md \
    .cursorrules \
    README.md \
    .github/ \
    backend/ \
    frontend/ \
    2>/dev/null)

  if [ ! -z "$RESULTS" ]; then
    echo "❌ 发现旧文档引用:"
    echo "$RESULTS"
    FOUND_ISSUES=1
  fi
done

if [ $FOUND_ISSUES -eq 0 ]; then
  echo "✅ 未发现旧文档引用"
  exit 0
else
  echo ""
  echo "⚠️  请将以上引用更新为: docs/core/AI_AD_SYSTEM_MASTER_SPEC.md"
  exit 1
fi
```

**集成到 CI/CD** (`.github/workflows/pr-checks.yml`):
```yaml
name: PR Checks

on:
  pull_request:
    branches: [main, master]

jobs:
  check-doc-references:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check for deprecated document references
        run: |
          chmod +x scripts/check_doc_references.sh
          ./scripts/check_doc_references.sh
```

---

## 3. 代码库扫描与风险评估

### 3.1 扫描脚本

执行以下命令扫描代码中的文档路径硬编码:

```bash
# 扫描 Python 代码
grep -rn "AI_AD_SYSTEM_MAIN_DOCUMENT\|MASTER_DESIGN_DOCUMENT" backend/ --include="*.py"

# 扫描 TypeScript/JavaScript 代码
grep -rn "AI_AD_SYSTEM_MAIN_DOCUMENT\|MASTER_DESIGN_DOCUMENT" frontend/ --include="*.ts" --include="*.tsx" --include="*.js"

# 扫描 Markdown 文档
grep -rn "AI_AD_SYSTEM_MAIN_DOCUMENT\|MASTER_DESIGN_DOCUMENT" docs/ --include="*.md" --exclude-dir=_archive

# 扫描配置文件
grep -rn "AI_AD_SYSTEM_MAIN_DOCUMENT\|MASTER_DESIGN_DOCUMENT" . \
  --include=".project-rules.md" \
  --include="CLAUDE.md" \
  --include=".cursorrules" \
  --include="README.md"
```

### 3.2 风险矩阵

| 风险项 | 风险级别 | 影响范围 | 缓解措施 |
|-------|---------|---------|---------|
| **配置文件引用错误** | 🔴 高 | AI 工具可能加载旧文档 | 按 2.2 节逐一更新配置 |
| **开发者习惯性引用旧文档** | 🟡 中 | 新成员可能困惑 | 执行团队培训 + 发布公告 |
| **CI/CD 脚本引用旧路径** | 🟡 中 | 自动化流程失败 | 检查所有 `.github/workflows/*.yml` |
| **文档交叉引用断链** | 🟢 低 | 其他文档链接失效 | 执行全局链接检查 |
| **历史 PR/Issue 引用** | 🟢 低 | 无实际影响 | 无需处理,保留历史记录 |

### 3.3 兼容性检查清单

迁移执行前,请确认以下检查项:

**环境检查**:
- [ ] 本地 Git 仓库状态干净 (`git status` 无未提交变更)
- [ ] 已拉取最新 main/master 分支
- [ ] 所有团队成员已通知迁移计划

**功能检查**:
- [ ] 后端单元测试通过 (`pytest backend/tests/`)
- [ ] 前端类型检查通过 (`pnpm type-check`)
- [ ] 前端 Lint 检查通过 (`pnpm lint`)
- [ ] 本地开发服务器正常启动

**文档检查**:
- [ ] 新文档 `AI_AD_SYSTEM_MASTER_SPEC.md` 已完整生成 (2140 行)
- [ ] 新文档版本号为 v2.0
- [ ] 新文档包含完整 6 章 + 5 个附录
- [ ] 已验证 5 项合并内容存在于新文档中

---

## 4. 团队沟通计划

### 4.1 公告模板

#### 4.1.1 项目 Wiki 公告

**标题**: [重要] Master Specification 文档合并通知

**内容**:
```markdown
# 📢 核心开发手册迁移通知

## 变更生效日期
2025-11-20

## 变更内容

我们已完成核心开发手册的整合工作,将以下两份文档合并为统一规范:

- ❌ **已归档**: `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` (v3.x)
- ❌ **已归档**: `docs/core/MASTER_DESIGN_DOCUMENT.md` (v1.0)
- ✅ **新文档**: `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (v2.0)

## 为什么要合并?

1. **消除歧义**: 旧文档存在部分内容冲突,导致开发者和 AI 工具困惑
2. **提升效率**: 统一入口,减少查阅多份文档的时间成本
3. **完整覆盖**: 新文档包含旧文档所有有效内容 + 更清晰的结构

## 新文档亮点

- **6 章完整结构**: 系统架构、业务模型、数据库、安全、业务规则、开发工作流
- **5 个附录**: 变更历史、术语表、相关资源、历史方案归档、开发承诺
- **2140 行内容**: 覆盖所有技术栈、角色权限、状态机、API 设计等核心规范
- **AI 友好**: 提供完整的 AI 辅助开发 Prompt 模板和检查清单

## 你需要做什么?

### 对于开发者:
1. **立即操作**: 更新你的本地书签/收藏夹,指向新文档
2. **开发前检查**: 确保按新文档第 6.1 节的开发流程执行
3. **Code Review**: 使用新文档第 6.3 节的检查清单

### 对于 AI 工具用户 (Cursor/Claude):
1. **更新配置**: 检查 `.project-rules.md`, `CLAUDE.md`, `.cursorrules` 是否已更新
2. **加载文档**: 生成代码前务必加载新文档 + 相关 SoT 文档
3. **验证输出**: 确保生成的代码符合新文档规范

### 对于团队 Lead:
1. **培训计划**: 组织一次文档结构讲解会议 (可选)
2. **监督执行**: Code Review 时检查是否遵循新规范
3. **反馈收集**: 如发现新文档遗漏或错误,及时提出

## 旧文档去哪了?

旧文档已移至归档目录: `docs/_archive/2025-11-20_master_spec_merge/`

⚠️ **禁止引用归档文档作为开发依据**

## 常见问题

**Q: 我正在进行的 PR 需要修改吗?**
A: 如果你的 PR 中引用了旧文档路径,请更新为新路径。代码本身无需修改。

**Q: 新文档有什么实质性内容变化吗?**
A: 无实质性内容删减,仅结构优化和内容整合。所有旧文档的有效规范均已保留。

**Q: 如何快速了解新文档结构?**
A: 查看新文档的目录 (第 70-103 行) 和第 1 章"文档说明"即可。

**Q: 发现新文档有错误怎么办?**
A: 立即在 Slack #engineering 频道或 GitHub Issue 反馈,我们会优先处理。

## 联系方式

- **技术问题**: GitHub Issue 或 Slack #engineering
- **紧急问题**: 联系系统架构团队 @architecture-team
- **文档反馈**: 提交 PR 到 `docs/core/` 目录

---

**发布团队**: 系统架构团队
**发布日期**: 2025-11-20
```

#### 4.1.2 Slack/钉钉通知模板

```
📢 【重要通知】核心开发手册已更新

Hi @channel,

从今天起,我们的核心开发手册已合并为统一版本:

✅ 新文档: docs/core/AI_AD_SYSTEM_MASTER_SPEC.md (v2.0)
❌ 旧文档: AI_AD_SYSTEM_MAIN_DOCUMENT.md + MASTER_DESIGN_DOCUMENT.md (已归档)

📌 **你需要做的**:
• 开发前加载新文档 (AI 工具用户必须)
• 更新你的书签/笔记
• Code Review 使用新文档的检查清单

📖 详细信息: [链接到 Wiki 公告]

有问题随时在 #engineering 频道讨论 👇
```

### 4.2 培训会议大纲 (可选)

如需组织培训会议,建议议程如下:

**会议时长**: 30 分钟

**议程**:
1. **背景说明** (5 分钟)
   - 为什么合并文档
   - 合并过程概述

2. **新文档结构导览** (10 分钟)
   - 6 章内容概览
   - 5 个附录说明
   - SoT 网络图解读

3. **关键变更点** (10 分钟)
   - 5 项合并内容展示
   - 配置文件更新说明
   - AI 工具使用规范

4. **Q&A** (5 分钟)
   - 现场答疑

**会后资料**:
- 会议录屏上传到 Wiki
- 新文档 PDF 版本下载链接
- 快速参考卡片 (Cheat Sheet)

### 4.3 过渡期时间表

| 阶段 | 时间 | 关键任务 | 负责人 |
|-----|------|---------|-------|
| **准备阶段** | D-Day (2025-11-20) | - 归档旧文档<br>- 更新配置文件<br>- 发布公告 | 架构团队 |
| **并行期** | D+1 ~ D+7 | - 监控团队反馈<br>- 修正遗漏问题<br>- 解答疑问 | 架构团队 + Team Leads |
| **强制期** | D+8 开始 | - 所有新 PR 强制引用新文档<br>- Code Review 严格检查 | 全体开发者 |

---

## 5. 回退策略

### 5.1 触发回退的条件

如出现以下情况,考虑回退到旧文档:

1. **重大遗漏**: 新文档缺失关键业务规范,导致开发阻塞
2. **严重错误**: 新文档存在重大技术错误,影响系统安全/稳定性
3. **团队抵触**: 超过 50% 团队成员反馈新文档不可用

### 5.2 回退执行步骤

#### Step 5.2.1: 从归档恢复旧文档

```bash
# 恢复旧文档到原位置
git mv docs/_archive/2025-11-20_master_spec_merge/AI_AD_SYSTEM_MAIN_DOCUMENT.md docs/core/
git mv docs/_archive/2025-11-20_master_spec_merge/MASTER_DESIGN_DOCUMENT.md docs/core/

# 删除或重命名新文档
git mv docs/core/AI_AD_SYSTEM_MASTER_SPEC.md docs/core/AI_AD_SYSTEM_MASTER_SPEC.md.backup
```

#### Step 5.2.2: 恢复配置文件

```bash
# 恢复到合并前的 Git 版本
git checkout HEAD~1 -- .project-rules.md
git checkout HEAD~1 -- CLAUDE.md
git checkout HEAD~1 -- .cursorrules
```

#### Step 5.2.3: 提交回退 PR

```bash
git add -A
git commit -m "Revert: 回退 Master Spec 合并 (原因: [具体说明])"
git push origin revert/master-spec-merge

# 创建 PR,说明回退原因和后续计划
```

### 5.3 改进方案

回退后,建议执行以下改进措施:

1. **根因分析**: 识别导致回退的具体问题
2. **局部修复**: 仅修复问题部分,保留有效改进
3. **增量迁移**: 分模块逐步迁移,而非一次性合并
4. **加强 Review**: 增加更多团队成员参与文档审核

---

## 6. 验收标准

### 6.1 迁移完成检查清单

**文档归档**:
- [ ] 旧文档已移至 `docs/_archive/2025-11-20_master_spec_merge/`
- [ ] 归档目录包含 README.md 说明文件
- [ ] 旧文档顶部添加废弃声明 (如采用方案 A)

**配置更新**:
- [ ] `.project-rules.md` 已更新为新路径
- [ ] `CLAUDE.md` 已更新为新路径
- [ ] `.cursorrules` 已更新为新路径
- [ ] `README.md` 文档链接已更新
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` 已更新

**团队沟通**:
- [ ] Wiki 公告已发布
- [ ] Slack/钉钉通知已发送
- [ ] 培训会议已完成 (如有)

**技术验证**:
- [ ] 后端测试通过 (`pytest backend/tests/`)
- [ ] 前端类型检查通过 (`pnpm type-check`)
- [ ] 前端 Lint 通过 (`pnpm lint`)
- [ ] CI/CD 流程正常运行
- [ ] 自动化检查脚本 (如有) 通过

**代码扫描**:
- [ ] 已执行 3.1 节的扫描脚本
- [ ] 无旧文档路径硬编码引用
- [ ] 所有交叉链接已更新

### 6.2 验收后行动

迁移完成后 7 天内,执行以下跟进:

1. **收集反馈**: 通过 Slack 投票或问卷调查收集团队意见
2. **补充文档**: 根据反馈补充遗漏内容或优化表述
3. **更新 Wiki**: 将迁移经验总结为最佳实践文档
4. **归档本指南**: 将本迁移指南移至 `docs/_archive/migration_guides/`

---

## 7. 附录: 迁移脚本汇总

### 7.1 一键归档脚本

`scripts/migrate_master_spec.sh`:

```bash
#!/bin/bash
# 一键执行 Master Spec 迁移归档

set -e  # 遇到错误立即退出

echo "🚀 开始执行 Master Spec 迁移..."

# Step 1: 创建归档目录
echo "📁 创建归档目录..."
mkdir -p docs/_archive/2025-11-20_master_spec_merge

# Step 2: 为旧文档添加废弃声明
echo "⚠️  添加废弃声明..."

# 备份原文件
cp docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md.bak
cp docs/core/MASTER_DESIGN_DOCUMENT.md docs/core/MASTER_DESIGN_DOCUMENT.md.bak

# 在文件开头插入废弃声明
cat > /tmp/deprecation_notice.md << 'EOF'
> ⚠️ **废弃声明 (DEPRECATED)**
> **废弃日期**: 2025-11-20
> **新文档路径**: [`docs/core/AI_AD_SYSTEM_MASTER_SPEC.md`](../core/AI_AD_SYSTEM_MASTER_SPEC.md) (v2.0)
> **原因**: 已与其他主规范文档合并为统一版本
> **本文档状态**: 仅供历史参考,禁止作为开发依据
> **如需查阅最新规范**: 请访问新文档

---

EOF

# 插入到原文件开头
cat /tmp/deprecation_notice.md docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md.bak > docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md
cat /tmp/deprecation_notice.md docs/core/MASTER_DESIGN_DOCUMENT.md.bak > docs/core/MASTER_DESIGN_DOCUMENT.md

# Step 3: 移动到归档目录
echo "📦 归档旧文档..."
git mv docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md docs/_archive/2025-11-20_master_spec_merge/
git mv docs/core/MASTER_DESIGN_DOCUMENT.md docs/_archive/2025-11-20_master_spec_merge/

# Step 4: 创建归档说明文件
echo "📝 创建 README.md..."
cat > docs/_archive/2025-11-20_master_spec_merge/README.md << 'EOF'
# Master Specification 合并归档

## 归档日期
2025-11-20

## 归档原因
这两份文档已合并为统一的核心开发手册,位于:
- **新文档路径**: `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (v2.0)

## 归档文件说明

### AI_AD_SYSTEM_MAIN_DOCUMENT.md
- **原版本**: v3.x
- **最后更新**: 2025-11-17
- **行数**: 395 行

### MASTER_DESIGN_DOCUMENT.md
- **原版本**: v1.0
- **最后更新**: 2025-11-20
- **行数**: 2527 行

## 如何查阅新文档

**新文档路径**: [`docs/core/AI_AD_SYSTEM_MASTER_SPEC.md`](../../core/AI_AD_SYSTEM_MASTER_SPEC.md)

---

**维护团队**: 系统架构团队
**审核者**: [待填写]
EOF

# Step 5: 清理备份文件
rm -f docs/core/*.bak
rm -f /tmp/deprecation_notice.md

echo "✅ 归档完成!"
echo ""
echo "📋 下一步操作:"
echo "1. 检查归档目录: docs/_archive/2025-11-20_master_spec_merge/"
echo "2. 更新配置文件: .project-rules.md, CLAUDE.md, .cursorrules"
echo "3. 提交 Git: git add -A && git commit -m 'docs: 归档旧 Master Spec 文档'"
echo "4. 发布团队公告"
```

**使用方法**:
```bash
chmod +x scripts/migrate_master_spec.sh
./scripts/migrate_master_spec.sh
```

### 7.2 配置文件更新脚本

`scripts/update_doc_references.sh`:

```bash
#!/bin/bash
# 批量更新配置文件中的文档路径引用

set -e

echo "🔧 开始更新配置文件引用..."

# 定义替换映射
OLD_PATH_1="docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md"
OLD_PATH_2="docs/core/MASTER_DESIGN_DOCUMENT.md"
NEW_PATH="docs/core/AI_AD_SYSTEM_MASTER_SPEC.md"

# 需要更新的文件列表
FILES=(
  ".project-rules.md"
  "CLAUDE.md"
  ".cursorrules"
  "README.md"
  ".github/PULL_REQUEST_TEMPLATE.md"
  "docs/README.md"
)

# 执行替换
for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "📝 更新 $file..."

    # 备份原文件
    cp "$file" "$file.bak"

    # 执行替换
    sed -i "s|$OLD_PATH_1|$NEW_PATH|g" "$file"
    sed -i "s|$OLD_PATH_2|$NEW_PATH|g" "$file"

    # 检查是否有变更
    if diff "$file" "$file.bak" > /dev/null; then
      echo "   ℹ️  无需更新"
      rm "$file.bak"
    else
      echo "   ✅ 已更新"
      rm "$file.bak"
    fi
  else
    echo "   ⚠️  文件不存在,跳过"
  fi
done

echo ""
echo "✅ 配置文件更新完成!"
echo "📋 请检查以下文件:"
for file in "${FILES[@]}"; do
  echo "   - $file"
done
```

**使用方法**:
```bash
chmod +x scripts/update_doc_references.sh
./scripts/update_doc_references.sh
```

---

## 8. 执行时间表建议

| 日期 | 阶段 | 关键任务 | 执行人 |
|-----|------|---------|-------|
| **D-Day (2025-11-20)** | **迁移日** | - 创建归档目录<br>- 归档旧文档<br>- 更新配置文件<br>- 发布 Wiki 公告 | 架构团队 |
| **D+1 (2025-11-21)** | **通知日** | - 发送 Slack/钉钉通知<br>- 更新 README.md<br>- 启动 CI/CD 检查 | 架构团队 |
| **D+2 ~ D+7** | **并行期** | - 监控团队反馈<br>- 解答疑问<br>- 修正发现的问题 | 架构团队 + Leads |
| **D+8 (2025-11-28)** | **强制日** | - 所有新 PR 强制引用新文档<br>- Code Review 严格检查 | 全体开发者 |
| **D+14 (2025-12-04)** | **回顾日** | - 收集反馈问卷<br>- 总结迁移经验<br>- 归档本指南 | 架构团队 |

---

## 9. 常见问题 (FAQ)

### Q1: 我正在进行的 PR 需要修改吗?

**A**: 如果你的 PR 中引用了旧文档路径 (如在代码注释、文档链接中),请更新为新路径。**代码逻辑本身无需修改**。

### Q2: 新文档有什么实质性内容变化吗?

**A**: **无实质性内容删减**。新文档是旧文档的超集,包含:
- 旧 `AI_AD_SYSTEM_MAIN_DOCUMENT.md` 的 5 项关键内容
- 旧 `MASTER_DESIGN_DOCUMENT.md` 的完整 6 章结构
- 新增 5 个附录 (变更历史、术语表、相关资源、历史方案归档、开发承诺)

### Q3: 如何快速了解新文档结构?

**A**: 查看新文档的以下部分:
1. **目录** (第 70-103 行) - 完整结构概览
2. **第 1 章"文档说明"** - 文档定位、SoT 网络、阅读指南
3. **附录 B"术语表"** - 关键概念速查

### Q4: 发现新文档有错误怎么办?

**A**: 立即通过以下渠道反馈:
- **GitHub Issue**: 提交 Bug Report
- **Slack**: 在 #engineering 频道 @architecture-team
- **紧急情况**: 直接联系系统架构团队

### Q5: 旧文档完全不能用了吗?

**A**: 旧文档已归档至 `docs/_archive/2025-11-20_master_spec_merge/`,**仅供历史参考,禁止作为开发依据**。所有开发工作必须以新文档为准。

### Q6: AI 工具 (Cursor/Claude) 如何适配?

**A**: 确保以下配置已更新:
1. `.project-rules.md` - 引用新文档路径
2. `CLAUDE.md` - 必读文档列表指向新路径
3. `.cursorrules` - 加载文档规则更新

生成代码前,明确告知 AI 工具加载 `docs/core/AI_AD_SYSTEM_MASTER_SPEC.md` (v2.0)。

### Q7: 如果我需要回退到旧文档怎么办?

**A**: 按照本指南第 5 节"回退策略"执行:
```bash
git mv docs/_archive/2025-11-20_master_spec_merge/AI_AD_SYSTEM_MAIN_DOCUMENT.md docs/core/
git mv docs/_archive/2025-11-20_master_spec_merge/MASTER_DESIGN_DOCUMENT.md docs/core/
```

但请先提交 Issue 说明原因,避免不必要的回退。

### Q8: 新文档太长了,如何快速定位我需要的内容?

**A**: 使用以下方法:
1. **目录跳转**: 点击目录链接快速定位章节
2. **浏览器搜索**: `Ctrl+F` / `Cmd+F` 搜索关键词 (如 "充值", "日报", "权限")
3. **章节编号**: 记住关键章节号:
   - 第 2 章: 角色与权限
   - 第 3 章: 数据库规范
   - 第 4 章: 安全与认证
   - 第 5 章: 业务规则
   - 第 6 章: 开发工作流

---

## 10. 联系方式

- **技术问题**: GitHub Issue 或 Slack #engineering
- **紧急问题**: 联系系统架构团队 @architecture-team
- **文档反馈**: 提交 PR 到 `docs/core/` 目录

---

**文档维护者**: 系统架构团队
**最后更新**: 2025-11-20
**版本**: v1.0
