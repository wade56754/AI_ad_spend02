# Layer 3: 任务约束 - 研究 (Research)

## 边界定义

- 只分析和输出报告，不执行任何修改
- 使用 context7 获取最新文档
- 使用 sequential-thinking 进行多步推理

## MCP 工具使用

### Sequential Thinking

```
use mcp__sequential-thinking__sequentialthinking
```

用于：分解复杂问题、多步推理、规划修订

### Context7

```
use mcp__context7__resolve-library-id
use mcp__context7__get-library-docs
```

用于：查询最新库文档、获取 API 参考

## 输出格式

研究报告应包含:

1. **问题背景**: 研究的问题是什么
2. **调研发现**: 主要发现
3. **代码示例**: 相关代码示例
4. **建议方案**: 推荐的解决方案
5. **参考资料**: 引用的文档和链接

