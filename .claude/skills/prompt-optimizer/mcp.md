# MCP 工具使用指南

## 工具概览

| 工具 | 触发词 | 用途 |
|------|--------|------|
| **Sequential Thinking** | "使用 sequential thinking" | 复杂问题分解 |
| **Context7** | "use context7" | 最新库文档 |
| **Fetch** | 提供 URL | 抓取网页 |

---

## Sequential Thinking

**适用场景**: 复杂提示词设计、多角色系统、长链工作流

**触发方式**:
```
/pc 使用 sequential thinking 设计多角色客服系统提示词
```

**工具参数**:
```typescript
sequentialthinking({
  thought: string,           // 当前思考
  nextThoughtNeeded: boolean,// 是否继续
  thoughtNumber: number,     // 步骤编号
  totalThoughts: number      // 预估总步骤
})
```

**典型流程**:
```
Step 1: 识别任务类型
Step 2: 分析使用场景
Step 3: 确定组件结构
Step 4: 设计输入输出
Step 5: 添加约束条件
Step 6: 生成初版
Step 7: 验证优化
```

---

## Context7

**适用场景**: 编程相关提示词、需要最新 API 文档

**触发方式**:
```
/pc 创建 FastAPI 测试提示词。use context7
```

**常用库 ID**:

| 库 | ID |
|----|----|
| pytest | `/pytest-dev/pytest` |
| FastAPI | `/fastapi/fastapi` |
| React | `/facebook/react` |
| Next.js | `/vercel/next.js` |
| LangChain | `/langchain-ai/langchain` |

**工具调用**:
```typescript
resolve_library_id({ libraryName: "pytest" })
get_library_docs({ libraryId: "/pytest-dev/pytest", topic: "fixtures" })
```

---

## Fetch

**适用场景**: 参考外部最佳实践、竞品分析

**触发方式**:
```
/pc 参考 https://docs.anthropic.com/.../prompt-engineering 优化我的提示词
```

**工具调用**:
```typescript
fetch_markdown({ url: "https://example.com" })  // 推荐
fetch_url({ url: "https://example.com" })       // 原始 HTML
```

---

## 组合使用

### 深度研究模式
```
/pc 使用 sequential thinking 分析需求，
use context7 获取 LangChain 文档，
参考 https://python.langchain.com/docs/tutorials/
创建 RAG 系统提示词
```

**执行流程**:
1. Sequential Thinking 分解需求
2. Fetch 抓取参考资料
3. Context7 获取最新 API
4. 综合生成提示词

### 迭代优化模式
```
1. [Sequential Thinking] 分析现有提示词问题
2. [Fetch] 获取类似优秀案例
3. [Context7] 验证 API 是否最新
4. 生成优化版本
```

---

## 注意事项

- **Context7**: 默认 5000 tokens，可指定 topic 缩小范围
- **Fetch**: 部分网站加载较慢
- **Sequential Thinking**: 复杂问题建议 5-10 步
- 三个工具可单独或组合使用
