---
description: "代码生成命令: 调用 Skill 生成后端/前端/测试代码"
argument-hint: "<type> <task-description>"
---

# 代码生成命令

调用对应的代码生成 Skill，生成符合 SoT 规范的代码。

## 参数

用户输入: `$ARGUMENTS`

格式: `<type> <task-description>`

支持的类型:
- `be` / `backend`: 调用 ai-ad-be-gen Skill 生成后端代码
- `fe` / `frontend`: 调用 ai-ad-fe-gen Skill 生成前端代码
- `test`: 调用 ai-ad-test-gen Skill 生成测试代码

## 工作流程

### Step 1: 解析参数

从 `$ARGUMENTS` 提取:
1. type: 生成类型 (be/fe/test)
2. task: 任务描述

### Step 2: 调用对应 Skill

根据 type 激活对应 Skill:

| Type | Skill | 职责 |
|------|-------|------|
| be | ai-ad-be-gen | FastAPI 路由、Service、Pydantic Schema |
| fe | ai-ad-fe-gen | React 组件、Hooks、API Client |
| test | ai-ad-test-gen | pytest 用例、Mock、集成测试 |

### Step 2.5: 防幻觉预检查 (MASTER.md v4.4 §7)

生成代码前必须执行以下检查：

**AH-01 检查**: 是否存在数据假设？
- 遇到数据缺失，不假设，标记"待确认"
- 禁止自动填充默认值

**AH-02 检查**: 是否生成自动裁决代码？
- 禁止: 自动拒绝/暂停/终止/冻结
- 允许: 仅记录、提示、高亮

**AH-03 检查**: 是否引入 SoT 未定义概念？
- 确认状态值在 8 状态机白名单中
- 确认角色值在 7 角色白名单中
- 确认错误码前缀在 16 前缀白名单中
- 如发现缺失 → **STOP** → 询问用户

**AH-04 检查**: 是否违反 Phase 1 软性原则？
- Phase 1: 仅提示+高亮+记录，不阻断
- 检测禁止模式 (raise HTTPException 4xx, suspend, freeze 等)

**AH-05 检查**: 是否存在未解决的歧义？
- 模块归属是否明确？
- 业务规则是否清晰？
- 如有歧义 → **STOP** → 列出歧义点 → 询问用户

**如任一检查失败** → BLOCKING → 停止生成 → 询问用户

### Step 3: SoT 约束检查

按 SoT 裁判链优先级检查:
1. MASTER.md v4.4: 系统全局规则
2. DATA_SCHEMA.md v5.2: 字段定义
3. STATE_MACHINE.md v2.6: 状态流转规则
4. BUSINESS_RULES.md v3.2: 业务规则
5. API_SOT.md v9.0: API 契约
6. ERROR_CODES_SOT.md v2.1: 错误码

### Step 4: 代码生成

生成代码需满足:
- 遵循项目代码风格
- 引用 SoT 版本号
- 包含必要注释
- 通过 lint 检查

## 示例

```bash
# 生成后端 API
/gen be 创建日报提交接口

# 生成前端组件
/gen fe 日报列表页面

# 生成测试用例
/gen test 日报状态流转测试
```

## 约束

- 禁止生成与 SoT 冲突的代码
- 禁止自定义错误码
- 禁止绕过状态机规则
- 禁止直接修改 models/ 目录
