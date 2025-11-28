# 链式提示词设计参考

## 何时使用链式提示词

| 场景 | 单提示词 | 链式提示词 |
|------|----------|------------|
| 简单问答 | ✅ | ❌ |
| 单步转换 | ✅ | ❌ |
| 多步分析 | ❌ | ✅ |
| 需要中间验证 | ❌ | ✅ |
| 复杂决策流程 | ❌ | ✅ |
| 自我纠正任务 | ❌ | ✅ |

**经验法则**：如果任务需要 3 个以上独立思考步骤，考虑链式拆解。

## 链式设计原则

1. **单一职责**：每个步骤只做一件事
2. **明确交接**：用 XML 标签传递步骤间的数据
3. **可独立调试**：每个步骤可单独测试
4. **失败隔离**：一个步骤失败不影响其他步骤的诊断

## 链式模板

### 基础链式结构

```xml
<chain name="[链名称]" description="[链功能描述]">

<step order="1" name="[步骤名]">
  <goal>本步骤的目标</goal>
  <input>期望的输入格式</input>
  <process>处理逻辑说明</process>
  <output tag="step1_result">输出格式，供后续步骤使用</o>
</step>

<step order="2" name="[步骤名]" depends_on="step1_result">
  <goal>本步骤的目标</goal>
  <input>使用 step1_result</input>
  <process>处理逻辑说明</process>
  <output tag="step2_result">输出格式</o>
</step>

<final_output>
  综合 step1_result 和 step2_result 生成最终输出
</final_output>

</chain>
```

## 常见链式模式

### 模式 1：研究 → 分析 → 建议

适用于：需要先收集信息再做决策的场景

```xml
<chain name="research-analyze-recommend">

<step order="1" name="research">
  <goal>收集相关信息</goal>
  <output tag="findings">
    - 发现1
    - 发现2
    - 发现3
  </o>
</step>

<step order="2" name="analyze" depends_on="findings">
  <goal>分析 findings 中的模式和关系</goal>
  <output tag="analysis">
    - 洞察1
    - 洞察2
    - 风险点
  </o>
</step>

<step order="3" name="recommend" depends_on="analysis">
  <goal>基于 analysis 提出可执行建议</goal>
  <output tag="recommendations">
    1. 建议1（优先级/影响/成本）
    2. 建议2（优先级/影响/成本）
  </o>
</step>

</chain>
```

### 模式 2：生成 → 审查 → 优化（自我纠正）

适用于：高质量输出需求，需要自我检查

```xml
<chain name="generate-review-refine">

<step order="1" name="generate">
  <goal>生成初稿</goal>
  <output tag="draft">初始内容</o>
</step>

<step order="2" name="review" depends_on="draft">
  <goal>以批评者视角审查 draft</goal>
  <criteria>
    - 准确性检查
    - 完整性检查
    - 一致性检查
    - 格式规范检查
  </criteria>
  <output tag="issues">
    - 问题1：描述 + 位置 + 严重性
    - 问题2：描述 + 位置 + 严重性
  </o>
</step>

<step order="3" name="refine" depends_on="draft,issues">
  <goal>修复 issues 中的所有问题</goal>
  <output tag="final">优化后的最终版本</o>
</step>

</chain>
```

### 模式 3：提取 → 转换 → 加载 (ETL)

适用于：数据处理和格式转换

```xml
<chain name="etl-pipeline">

<step order="1" name="extract">
  <goal>从源数据提取关键信息</goal>
  <input>原始数据（文档/表格/API响应）</input>
  <output tag="raw_data" format="json">
    结构化的原始数据
  </o>
</step>

<step order="2" name="transform" depends_on="raw_data">
  <goal>清洗和转换数据</goal>
  <operations>
    - 去重
    - 格式标准化
    - 字段映射
    - 数据验证
  </operations>
  <output tag="clean_data" format="json">
    清洗后的数据
  </o>
</step>

<step order="3" name="load" depends_on="clean_data">
  <goal>输出为目标格式</goal>
  <output tag="final_output">
    最终格式（报告/表格/API请求）
  </o>
</step>

</chain>
```

### 模式 4：分治并行

适用于：可以独立处理的多个子任务

```xml
<chain name="divide-and-conquer">

<step order="1" name="divide">
  <goal>将任务分解为独立子任务</goal>
  <output tag="subtasks">
    - subtask_1
    - subtask_2
    - subtask_3
  </o>
</step>

<parallel depends_on="subtasks">
  <step name="process_1" input="subtask_1">
    <output tag="result_1">子结果1</o>
  </step>
  <step name="process_2" input="subtask_2">
    <output tag="result_2">子结果2</o>
  </step>
  <step name="process_3" input="subtask_3">
    <output tag="result_3">子结果3</o>
  </step>
</parallel>

<step order="final" name="merge" depends_on="result_1,result_2,result_3">
  <goal>合并所有子结果</goal>
  <output tag="merged_result">综合结果</o>
</step>

</chain>
```

## 项目特定链式模式

### ASDD 文档治理链

```xml
<chain name="asdd-doc-governance">

<step order="1" name="scan">
  <goal>扫描所有 Markdown 文档</goal>
  <scope>root/*.md, docs/**/*.md, .claude/*.md</scope>
  <output tag="doc_inventory">文档清单 + 元数据</o>
</step>

<step order="2" name="classify" depends_on="doc_inventory">
  <goal>按 ASDD 6 层分类每个文档</goal>
  <categories>
    - frozen（已冻结，只读）
    - active（活跃，可编辑）
    - outdated（过时，待归档）
    - orphan（孤儿，无引用）
    - conflicting（冲突，需解决）
  </categories>
  <output tag="classification">分类结果</o>
</step>

<step order="3" name="validate" depends_on="classification">
  <goal>验证引用完整性和版本一致性</goal>
  <checks>
    - baseline 是否正确
    - SoT 版本号是否匹配
    - 引用路径是否有效
  </checks>
  <output tag="issues">问题列表（P0/P1/P2）</o>
</step>

<step order="4" name="remediate" depends_on="classification,issues">
  <goal>执行修复操作</goal>
  <actions>
    - 归档 outdated 文档
    - 修复 broken refs
    - 标准化 frontmatter
  </actions>
  <output tag="changes">变更记录</o>
</step>

<step order="5" name="report" depends_on="changes">
  <goal>生成治理报告</goal>
  <output tag="governance_report">
    Global_Doc_Governance_Report.md
  </o>
</step>

</chain>
```

## 调试技巧

1. **步骤隔离测试**：单独运行每个步骤，验证输入输出
2. **添加检查点**：在关键步骤后输出中间结果
3. **失败回退**：定义步骤失败时的处理策略
4. **日志追踪**：记录每个步骤的执行状态

```xml
<step order="2" name="validate">
  <on_success>继续执行 step 3</on_success>
  <on_failure>
    <action>输出已完成的部分结果</action>
    <action>记录失败原因</action>
    <action>提示用户人工介入</action>
  </on_failure>
</step>
```
