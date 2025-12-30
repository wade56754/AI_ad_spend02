# Layer 3: 任务约束 - 新功能 (Feature)

## 边界定义

- 只实现被要求的功能，不添加"顺便"的改进
- 使用项目已有的模式和抽象
- 不引入新的依赖，除非明确要求

## 代码结构

### 后端 (FastAPI)

```
backend/
├── schemas/{module}.py      # Pydantic 模型
├── services/{module}.py     # 业务逻辑
├── routers/{module}.py      # API 路由
└── models/{table}.py        # 数据库模型
```

### 前端 (Next.js)

```
frontend/src/
├── types/{module}.ts        # TypeScript 类型
├── lib/api/{module}.ts      # API 调用
├── hooks/use{Module}.ts     # React Hooks
├── components/{Module}/     # 组件
└── app/{route}/page.tsx     # 页面
```

## SoT 标注规范

所有生成的代码必须使用标准来源标注:

```python
# SoT: STATE_MACHINE.md#daily_report
# SoT: DATA_SCHEMA.md#daily_reports.amount
# SoT: ERROR_CODES_SOT.md#RPT-001
```

