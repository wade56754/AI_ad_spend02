# Layer 3: 任务约束 - 重构 (Refactor)

## 边界定义

- 只重构被指定的模块/文件
- 保留既有业务语义，不改变外部行为
- 不新增功能，不调整 API 合同
- 不修改未被提及的代码

## API 合同定义 (Breaking Change)

以下变更视为破坏性变更:

- routes, method, status_code
- request/response schema
- error schema

## Patch 规模限制

- 每个 patch ≤ 5 文件
- 每个 patch ≤ 200 行变更

## 执行步骤

1. 先读取目标文件，理解现有结构
2. 识别要重构的部分
3. 制定重构计划
4. 逐步执行，每步验证
5. 确保测试通过

