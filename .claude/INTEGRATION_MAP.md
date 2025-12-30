# 能力集成关系图 (Integration Map)

> **版本**: v1.0
> **最后更新**: 2025-12-30
> **维护者**: 架构组

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户入口层 (Commands)                        │
├─────────────────────────────────────────────────────────────────┤
│  /gen be    /gen fe    /review    /sot-check    /doc    /pc    │
└──────┬──────────┬─────────┬──────────┬──────────┬───────┬──────┘
       │          │         │          │          │       │
       ▼          ▼         ▼          ▼          ▼       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      技能层 (Skills)                              │
├─────────────────────────────────────────────────────────────────┤
│  ai-ad-be-gen  ai-ad-fe-gen  ai-master-   ai-ad-spec-  ai-ad-   │
│                              architect    governor     prompt-  │
│                                                        structurer│
└──────┬──────────┬─────────┬──────────┬──────────┬───────┬──────┘
       │          │         │          │          │       │
       ▼          ▼         ▼          ▼          ▼       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      规范层 (SoT Documents)                       │
├─────────────────────────────────────────────────────────────────┤
│  API_SOT.md    组件库    MASTER.md    所有SoT    INDEX.md       │
│  DATA_SCHEMA           BR-*.md                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Commands → Skills 映射

### 代码生成命令

```
/gen be <task>
    │
    └──► ai-ad-be-gen
            │
            ├── ai-ad-code-factory (编排)
            │       ├── ai-ad-code-searcher
            │       ├── ai-ad-code-selector
            │       ├── ai-ad-code-adapter
            │       ├── ai-ad-code-assembler
            │       └── ai-ad-code-verifier
            │
            └── 参考 SoT
                    ├── API_SOT.md
                    ├── DATA_SCHEMA.md
                    ├── ERROR_CODES_SOT.md
                    └── BR-*.md
```

```
/gen fe <task>
    │
    └──► ai-ad-fe-gen
            │
            └── 参考资源
                    ├── 组件库 (src/components/)
                    ├── 现有页面模式
                    └── 设计规范
```

```
/gen test <task>
    │
    └──► ai-ad-test-gen
            │
            └── 参考资源
                    ├── 测试模式 (tests/)
                    ├── pytest 配置
                    └── fixture 库
```

### 审查命令

```
/review <file>
    │
    └──► ai-master-architect
            │
            ├── 检查项
            │       ├── 架构规范 (MASTER.md)
            │       ├── 业务规则 (BR-*.md)
            │       ├── 代码质量
            │       └── 安全检查
            │
            └── 输出
                    ├── 问题列表
                    ├── 修复建议
                    └── 合规评分
```

```
/sot-check <file>
    │
    └──► ai-ad-spec-governor
            │
            ├── 检查内容
            │       ├── 状态值 (STATE_MACHINE.md)
            │       ├── 角色值 (6 角色白名单)
            │       ├── 错误码 (ERROR_CODES_SOT.md)
            │       └── API 契约 (API_SOT.md)
            │
            └── 输出
                    ├── 合规报告
                    ├── 违规列表
                    └── 修复建议
```

### 文档命令

```
/doc <task>
    │
    └──► ai-ad-doc-orchestrator
            │
            ├── 子技能调用
            │       ├── ai-ad-doc-architect (规划)
            │       ├── ai-project-doc-writer (编写)
            │       └── ai-doc-system-auditor (审计)
            │
            └── 参考资源
                    ├── 文档模板
                    ├── 现有文档结构
                    └── SoT 规范
```

### 流程命令

```
/dev-flow <type>
    │
    └──► ai-ad-flow-orchestrator
            │
            ├── 流程类型
            │       ├── feature (新功能开发)
            │       ├── bugfix (问题修复)
            │       ├── refactor (代码重构)
            │       └── doc (文档更新)
            │
            └── 编排步骤
                    ├── 探索 (Explore)
                    ├── 计划 (Plan)
                    ├── 执行 (Execute)
                    └── 验证 (Verify)
```

```
/pc <prompt>
    │
    └──► ai-ad-prompt-structurer
            │
            └── 优化维度
                    ├── 约束层 (Constraints)
                    ├── 任务层 (Task)
                    ├── 上下文层 (Context)
                    └── 输出格式 (Output)
```

### OpenSpec 命令

```
/openspec-proposal
    │
    └──► 创建变更提案
            ├── 生成 RFC 文档
            ├── 识别影响范围
            └── 生成检查清单

/openspec-validate
    │
    └──► 验证提案
            ├── SoT 合规检查
            ├── 依赖分析
            └── 风险评估

/openspec-apply
    │
    └──► 应用变更
            ├── 代码修改
            ├── 文档更新
            └── 测试执行

/openspec-archive
    │
    └──► 归档变更
            ├── 更新 CHANGELOG
            ├── 版本号升级
            └── 标记完成
```

---

## Skills → SoT 依赖矩阵

| Skill | MASTER | DATA_SCHEMA | STATE_MACHINE | BR-* | API_SOT | ERROR_CODES |
|-------|--------|-------------|---------------|------|---------|-------------|
| ai-ad-be-gen | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ai-ad-fe-gen | ✓ | ✓ | - | - | ✓ | - |
| ai-master-architect | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ai-ad-spec-governor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ai-ad-code-verifier | ✓ | - | ✓ | ✓ | - | ✓ |
| ai-ad-doc-orchestrator | ✓ | - | - | - | - | - |

---

## Agents 调用链

```
Task tool (subagent_type)
    │
    ├── codex-loop
    │       │
    │       └── 循环执行
    │               ├── 读取任务
    │               ├── 执行代码修改
    │               ├── 验证结果
    │               └── 继续或完成
    │
    ├── doc-architect
    │       │
    │       └── 文档规划
    │               ├── 分析需求
    │               ├── 设计结构
    │               └── 输出大纲
    │
    └── doc-fixer
            │
            └── 文档修复
                    ├── 扫描问题
                    ├── 生成修复
                    └── 应用变更
```

---

## 典型工作流

### 新功能开发

```
1. /dev-flow feature "用户登录"
       │
       ▼
2. ai-ad-flow-orchestrator (探索→计划)
       │
       ▼
3. /gen be "创建登录 API"
       │
       ▼
4. ai-ad-be-gen → ai-ad-code-factory
       │
       ▼
5. /sot-check backend/routers/auth.py
       │
       ▼
6. ai-ad-spec-governor (合规检查)
       │
       ▼
7. /review backend/routers/auth.py
       │
       ▼
8. ai-master-architect (代码审查)
```

### 文档更新

```
1. /doc "更新 API 文档"
       │
       ▼
2. ai-ad-doc-orchestrator
       │
       ├── ai-ad-doc-architect (规划)
       │
       ├── ai-project-doc-writer (编写)
       │
       └── ai-doc-system-auditor (审计)
       │
       ▼
3. 输出更新后的文档
```

### SoT 合规检查

```
1. /sot-check <file>
       │
       ▼
2. ai-ad-spec-governor
       │
       ├── 加载 SoT 文档
       │       ├── STATE_MACHINE.md (状态值)
       │       ├── MASTER.md (角色值)
       │       ├── ERROR_CODES_SOT.md (错误码)
       │       └── API_SOT.md (API 契约)
       │
       ├── 扫描代码
       │       ├── 提取状态值
       │       ├── 提取角色值
       │       ├── 提取错误码
       │       └── 提取 API 调用
       │
       └── 生成报告
               ├── 合规项 ✓
               ├── 违规项 ✗
               └── 修复建议
```

---

## 相关文档

- [CAPABILITIES.md](./CAPABILITIES.md) - 能力清单
- [skills/INDEX.md](./skills/INDEX.md) - 技能索引
- [agents/README.md](./agents/README.md) - 代理说明
- [commands/README.md](./commands/README.md) - 命令说明

---

**维护周期**: 每次新增/修改 Skill/Agent/Command 后更新
