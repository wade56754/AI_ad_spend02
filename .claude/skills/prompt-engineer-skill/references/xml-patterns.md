# XML 标签模式参考

## 核心标签体系

### 结构标签

| 标签 | 用途 | 嵌套级别 |
|------|------|----------|
| `<system>` | 角色定义和行为准则 | 顶层 |
| `<task>` | 任务描述和目标 | 顶层 |
| `<context>` | 背景信息和约束 | 顶层 |
| `<rules>` | 规则和限制 | 顶层 |
| `<examples>` | 示例集合 | 顶层 |
| `<output_format>` | 输出格式要求 | 顶层 |
| `<procedure>` | 步骤流程 | 顶层 |

### 嵌套标签

```xml
<rules>
  <immutable>不可更改的规则</immutable>
  <mutable>可调整的规则</mutable>
  <must>必须做的</must>
  <must_not>禁止做的</must_not>
</rules>

<examples>
  <example type="good">正面示例</example>
  <example type="bad">负面示例</example>
</examples>

<procedure>
  <step order="1" name="步骤名">步骤内容</step>
  <step order="2" name="步骤名" depends_on="1">步骤内容</step>
</procedure>
```

## 标签命名规范

1. **使用小写和连字符**：`<output_format>` 而非 `<OutputFormat>`
2. **语义化命名**：标签名应清晰表达内容类型
3. **保持一致性**：同一提示词中相同概念使用相同标签
4. **在指令中引用**：如 "请使用 `<context>` 中的信息"

## 常见模式

### 模式 1：条件分支

```xml
<workflow>
  <condition if="文件类型是 PDF">
    执行 PDF 处理流程
  </condition>
  <condition if="文件类型是 DOCX">
    执行 DOCX 处理流程
  </condition>
  <default>
    提示不支持的文件类型
  </default>
</workflow>
```

### 模式 2：优先级标注

```xml
<objectives>
  <objective priority="P0">必须完成的核心目标</objective>
  <objective priority="P1">重要但非阻断的目标</objective>
  <objective priority="P2">可选的增强目标</objective>
</objectives>
```

### 模式 3：输入输出分离

```xml
<io_spec>
  <input>
    <format>JSON 对象</format>
    <required_fields>id, name, status</required_fields>
    <optional_fields>description, tags</optional_fields>
  </input>
  <output>
    <format>Markdown 报告</format>
    <sections>摘要, 详情, 建议</sections>
  </output>
</io_spec>
```

## 反模式（避免）

### ❌ 标签过度嵌套

```xml
<!-- 不好：嵌套过深，难以阅读 -->
<task>
  <sub_task>
    <details>
      <item>
        <description>内容</description>
      </item>
    </details>
  </sub_task>
</task>
```

### ✅ 扁平化结构

```xml
<!-- 好：保持 2-3 层嵌套 -->
<task>
  <objective>目标描述</objective>
  <steps>
    <step>步骤1</step>
    <step>步骤2</step>
  </steps>
</task>
```

### ❌ 重复定义

```xml
<!-- 不好：同一信息出现在多处 -->
<context>用户是管理员</context>
<rules>因为用户是管理员，所以...</rules>
```

### ✅ 引用而非重复

```xml
<!-- 好：在一处定义，其他地方引用 -->
<context id="user_role">用户是管理员</context>
<rules>根据 <context> 中的用户角色...</rules>
```
