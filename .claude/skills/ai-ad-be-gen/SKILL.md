---
name: ai-ad-be-gen
version: "2.0"
status: production
layer: Skill

sot_dependencies:
  required:
    - docs/2.sot/DATA_SCHEMA.md
    - docs/2.sot/STATE_MACHINE.md
    - docs/2.sot/API_SOT.md
    - docs/2.sot/BUSINESS_RULES.md
    - docs/2.sot/ERROR_CODES_SOT.md
  optional:
    - docs/2.sot/LEDGER_SOT.md
    - docs/2.sot/AUTH_SPEC.md

output_boundaries:
  writable:
    - backend/schemas/**
    - backend/services/**
    - backend/routers/**
  forbidden:
    - backend/models/**
    - migrations/**
    - .env*

baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.0, SoT Freeze v2.6
---

# BE-Gen Skill - 后端代码生成

## 1. Purpose

后端代码生成 Skill，负责在 SoT 约束下生成 FastAPI 后端代码。

**核心职责**:
- 根据任务描述生成 Schema/Service/Router 三层代码
- 严格遵循 SoT 文档约束（状态机、数据模型、错误码等）
- 不生成 models 层代码（禁区）

## 2. Input Contract

```typescript
interface BEGenInput {
  task: string;           // 任务描述，如 "实现充值审批 API"
  target_files: string[]; // 目标文件列表（相对于 backend/）
  context?: {
    sot_snapshot?: Record<string, string>;  // SoT 文档内容快照
    existing_code?: Record<string, string>; // 现有代码快照
  };
}
```

**校验规则**:
- `task` 不能为空
- `target_files` 至少有一个文件
- 文件路径必须在可写区域内

## 3. Output Contract

```typescript
interface BEGenOutput {
  success: boolean;
  data?: {
    changes: Record<string, string>;  // 文件路径 -> 新内容
    notes: string[];                   // 自检说明
    sot_refs: string[];               // 引用的 SoT 条款
  };
  error?: string;
}
```

## 4. Constraints (必须遵守的边界)

### 4.1 代码边界

| 区域 | 权限 | 说明 |
|------|------|------|
| `backend/schemas/**` | ✅ 可写 | Pydantic 模型 |
| `backend/services/**` | ✅ 可写 | 业务逻辑层 |
| `backend/routers/**` | ✅ 可写 | FastAPI 路由 |
| `backend/models/**` | ❌ 禁止 | 数据库模型 |
| `migrations/**` | ❌ 禁止 | 数据库迁移 |

### 4.2 SoT 遵循规则

1. **状态枚举**: 必须使用 `STATE_MACHINE.md` 中定义的状态
2. **错误码**: 必须使用 `ERROR_CODES_SOT.md` 中定义的错误码
3. **数据字段**: 必须与 `DATA_SCHEMA.md` 中的定义一致
4. **业务规则**: 必须实现 `BUSINESS_RULES.md` 中的规则
5. **API 规范**: 必须符合 `API_SOT.md` 中的端点定义

### 4.3 技术栈约束

- FastAPI 0.100+
- SQLAlchemy 2.x (声明式映射)
- Pydantic v2
- 异步优先 (async/await)

## 5. Prompt Template

```xml
<SYSTEM>
你是"后端开发 Agent"，负责在现有 FastAPI + SQLAlchemy + Pydantic v2 项目中实现/重构接口和 Service。

必须遵守的规则：
1. DATA_SCHEMA / STATE_MACHINE / BUSINESS_RULES / API_SOT / ERROR_CODES 作为唯一事实来源
2. 不自行发明新的枚举值、状态机、字段
3. 统一 ErrorCode 枚举与错误响应结构
4. 严格类型标注，避免 any、裸 dict
5. 不生成 models/ 目录下的代码（这是禁区）
6. 必须在代码注释中标注 SoT 引用（如 # SoT: STATE_MACHINE.md#topup）

技术栈假设：
- FastAPI
- SQLAlchemy 2.x（声明式映射）
- Pydantic v2
- 异步优先
</SYSTEM>

<CONTEXT>
<DOC name="MASTER">
{{MASTER}}
</DOC>

<DOC name="DATA_SCHEMA">
{{DATA_SCHEMA}}
</DOC>

<DOC name="STATE_MACHINE">
{{STATE_MACHINE}}
</DOC>

<DOC name="BUSINESS_RULES">
{{BUSINESS_RULES}}
</DOC>

<DOC name="API_SOT">
{{API_SOT}}
</DOC>

<DOC name="ERROR_CODES">
{{ERROR_CODES}}
</DOC>

<DOC name="LEDGER_SOT" optional="true">
{{LEDGER_SOT}}
</DOC>

<DOC name="AUTH_SPEC" optional="true">
{{AUTH_SPEC}}
</DOC>

<EXISTING_FILES>
{{EXISTING_FILES}}
</EXISTING_FILES>
</CONTEXT>

<TASK>
{{TASK}}
</TASK>

<THINKING_CHAIN>
请按以下步骤思考：

1. **SoT 映射**
   - 从 API_SOT 定位本次要实现的 API 端点
   - 从 BUSINESS_RULES 找到相关业务规则 (BR-XXX-YYY)
   - 从 STATE_MACHINE 确认状态转换约束
   - 从 DATA_SCHEMA 确认字段类型和约束

2. **代码规划**
   - 确定需要修改/创建的文件
   - 规划三层结构：Schema → Service → Router
   - 确认错误码和异常处理

3. **代码生成**
   - 生成 Pydantic Schema (带 SoT 注释)
   - 生成 Service 层业务逻辑 (带 SoT 注释)
   - 生成 Router 层端点 (带 SoT 注释)

4. **自检**
   - 检查状态枚举是否与 STATE_MACHINE 一致
   - 检查错误码是否在 ERROR_CODES 中定义
   - 检查字段类型是否与 DATA_SCHEMA 一致
   - 检查是否有禁区代码

5. **输出**
   - 生成 changes 字典
   - 记录引用的 SoT 条款
   - 记录潜在风险点
</THINKING_CHAIN>

<OUTPUT_FORMAT>
只输出一段 JSON，格式如下：

{
  "changes": [
    {
      "file": "backend/schemas/topup.py",
      "content": "完整的文件内容"
    },
    {
      "file": "backend/services/topup_service.py",
      "content": "完整的文件内容"
    },
    {
      "file": "backend/routers/topups.py",
      "content": "完整的文件内容"
    }
  ],
  "notes": [
    "自检说明1",
    "自检说明2"
  ],
  "sot_refs": [
    "STATE_MACHINE.md#topup: pending → approved",
    "BUSINESS_RULES.md#BR-TP-001",
    "ERROR_CODES_SOT.md#TOPUP_001"
  ]
}
</OUTPUT_FORMAT>
```

## 6. Self-Check Checklist

生成代码后，必须进行以下自检：

| 检查项 | 验证方法 | P0/P1 |
|--------|---------|-------|
| 状态枚举一致性 | 对比 STATE_MACHINE.md | P0 |
| 错误码合规 | 查找 ERROR_CODES_SOT.md | P0 |
| 字段类型匹配 | 对比 DATA_SCHEMA.md | P0 |
| 禁区检查 | 不生成 models/migrations | P0 |
| 权限检查 | 对比 AUTH_SPEC.md | P1 |
| 账本规则 | 对比 LEDGER_SOT.md | P1 |

## 7. Example

### Input
```json
{
  "task": "实现充值审批 API",
  "target_files": [
    "schemas/topup.py",
    "services/topup_service.py",
    "routers/topups.py"
  ]
}
```

### Expected Output
```json
{
  "changes": [
    {
      "file": "backend/schemas/topup.py",
      "content": "from enum import Enum\nfrom pydantic import BaseModel\nfrom typing import Optional\nfrom uuid import UUID\nfrom datetime import datetime\n\n\nclass TopupStatus(str, Enum):\n    \"\"\"状态枚举 - SoT: STATE_MACHINE.md#topup\"\"\"\n    PENDING = \"pending\"\n    APPROVED = \"approved\"\n    REJECTED = \"rejected\"\n    EXECUTED = \"executed\"\n    FAILED = \"failed\"\n\n\nclass TopupApproveRequest(BaseModel):\n    comment: Optional[str] = None\n\n\nclass TopupApproveResponse(BaseModel):\n    id: UUID\n    status: TopupStatus\n    approved_by: UUID\n    approved_at: datetime\n"
    }
  ],
  "notes": [
    "状态枚举已对齐 STATE_MACHINE.md#topup",
    "需要确保 ledger_entries 写入事务正确"
  ],
  "sot_refs": [
    "STATE_MACHINE.md#topup",
    "BUSINESS_RULES.md#BR-TP-001"
  ]
}
```

## 8. Version History

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2025-12-06 | 重构：对齐 AI_CODE_FACTORY_DEV_GUIDE_v2.0，增加 SoT refs 输出 |
| v1.0 | 2025-11-01 | 初始版本 |

---

**文档控制**: Owner: wade | Baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.0
