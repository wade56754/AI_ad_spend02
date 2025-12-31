# 需求澄清提示词 (Clarify Prompt)

## 目标

在代码生成前澄清需求，减少歧义和误解。

## 澄清步骤

1. **理解核心需求**: 用户想要实现什么功能？
2. **识别模糊点**: 哪些部分描述不清楚？
3. **确认边界**: 功能范围是什么？不包括什么？
4. **技术选型**: 需要用到哪些技术？
5. **验收标准**: 如何判断功能完成？

## 澄清问题模板

请依次确认以下问题：

### 1. 功能确认
- 这个功能的主要用户是谁？（投手/财务/项目负责人/管理员）
- 核心业务流程是什么？

### 2. 数据确认
- 涉及哪些数据表？
- 需要新增字段吗？

### 3. 接口确认
- 需要哪些 API 端点？
- 是否需要前端页面？

### 4. 约束确认
- 有哪些业务规则限制？
- 权限要求是什么？

### 5. 验收确认
- 成功的标准是什么？
- 需要哪些测试用例？

## 输出格式

```yaml
clarified_requirement:
  summary: "{一句话描述}"
  user_role: "{目标用户}"
  business_flow: "{业务流程}"
  
  scope:
    included:
      - "{包含的功能 1}"
      - "{包含的功能 2}"
    excluded:
      - "{不包含的功能 1}"
  
  data:
    tables: ["{表名}"]
    new_fields: ["{新字段}"]
  
  api:
    endpoints:
      - method: "{HTTP 方法}"
        path: "{路径}"
        description: "{描述}"
  
  constraints:
    business_rules: ["{规则}"]
    permissions: ["{权限}"]
  
  acceptance_criteria:
    - "{验收标准 1}"
    - "{验收标准 2}"
```

## 示例

**用户需求**: "添加日报批量导出功能"

**澄清后**:
```yaml
clarified_requirement:
  summary: "支持投手批量导出日报数据为 Excel 文件"
  user_role: "pitcher (投手)"
  business_flow: "选择日期范围 → 筛选状态 → 导出 Excel"
  
  scope:
    included:
      - 按日期范围筛选
      - 按状态筛选
      - 导出为 Excel (.xlsx)
    excluded:
      - PDF 导出
      - 定时自动导出
  
  data:
    tables: ["daily_reports"]
    new_fields: []
  
  api:
    endpoints:
      - method: "GET"
        path: "/api/v1/daily-reports/export"
        description: "导出日报数据"
  
  constraints:
    business_rules: 
      - "只能导出自己的日报"
      - "最多导出 90 天数据"
    permissions: ["pitcher"]
  
  acceptance_criteria:
    - "能够按日期范围筛选"
    - "能够按状态筛选"
    - "导出的 Excel 包含所有日报字段"
    - "文件名包含导出日期"
```


