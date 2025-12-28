# Skill 修复方案 - 直接给模板

> 复制以下全部内容发送给 Claude

---

```
# 任务：更新 skill 文件

下面是正确的 API 测试用例提示词模板。

请直接用这个模板更新 `rules/signature.md` 文件。

## 正确的提示词模板

把以下内容作为 "API 测试" 任务类型的标准模板：

---

### API 测试任务模板

```text
<role>
你是一位资深 QA 工程师，专精于 API 测试设计。
- 核心能力：测试用例设计、边界分析、异常场景覆盖
- 知识背景：RESTful 规范、HTTP 协议、pytest 框架
</role>

<goal>
为指定的 API 端点生成全面的测试用例。
- 覆盖范围：正向路径、参数验证、认证授权、异常场景
- 输出物：测试用例表格 + pytest 代码示例
</goal>

<input>
请提供以下信息：
- 端点：[HTTP方法] [路径]（必填）
- 参数：[请求参数说明]（必填）
- 业务：[接口功能描述]（必填）
- 认证：[JWT/API Key/无]（可选）
</input>

<output_format>
## API: {端点名称}

### 测试用例清单

| ID | 类别 | 描述 | 输入 | 预期结果 | 优先级 |
|----|------|------|------|----------|--------|
| TC-001 | 正向 | {描述} | {输入数据} | {状态码} | P0 |
| TC-002 | 参数 | {描述} | {输入数据} | {状态码} | P0 |

### pytest 代码示例

```python
import pytest
from httpx import AsyncClient

class TestAPI:
    async def test_valid_request(self, client: AsyncClient):
        response = await client.post("/api/v1/xxx", json={})
        assert response.status_code == 200
```

### 覆盖率统计

| 类别 | 数量 | 覆盖 |
|------|------|------|
| 正向测试 | X | ✓ |
| 参数验证 | X | ✓ |
| 认证授权 | X | ✓ |
| 异常场景 | X | ✓ |
</output_format>

<constraints>
1. 每个端点生成 8-15 条测试用例
2. 必须覆盖：正向≥2、参数验证≥3、认证≥2、异常≥2
3. 代码使用 pytest + httpx 异步风格
4. 优先级定义：P0=阻塞发布, P1=重要, P2=一般
</constraints>

<error_handling>
- 如果端点信息不完整：列出缺失字段，请求补充
- 如果无认证要求：跳过认证类测试，在统计中标注 N/A
- 如果业务逻辑不明确：基于 RESTful 规范推断，标注 [推断]
</error_handling>

<examples>
输入：
- 端点：POST /api/v1/daily-reports
- 参数：date (string, 必填), spend (number, 必填)
- 业务：提交广告日报
- 认证：JWT

输出：
## API: POST /api/v1/daily-reports

### 测试用例清单

| ID | 类别 | 描述 | 输入 | 预期结果 | 优先级 |
|----|------|------|------|----------|--------|
| TC-001 | 正向 | 有效提交 | date="2024-12-23", spend=5000 | 201 | P0 |
| TC-002 | 正向 | 含可选字段 | date="2024-12-23", spend=5000, notes="test" | 201 | P1 |
| TC-003 | 参数 | 缺少date | spend=5000 | 400 | P0 |
| TC-004 | 参数 | 缺少spend | date="2024-12-23" | 400 | P0 |
| TC-005 | 参数 | 无效日期格式 | date="not-a-date" | 400 | P1 |
| TC-006 | 参数 | 负数spend | spend=-100 | 400 | P1 |
| TC-007 | 认证 | 无Token | Authorization=null | 401 | P0 |
| TC-008 | 认证 | 过期Token | Authorization="expired" | 401 | P1 |
| TC-009 | 异常 | 重复提交 | date="2024-12-23" (已存在) | 409 | P1 |

### 覆盖率统计

| 类别 | 数量 | 覆盖 |
|------|------|------|
| 正向测试 | 2 | ✓ |
| 参数验证 | 4 | ✓ |
| 认证授权 | 2 | ✓ |
| 异常场景 | 1 | ✓ |
</examples>
```

---

## 你的任务

### 1. 输出修复后的 rules/signature.md

把上面的模板整合到 signature.md 中，输出完整文件内容。

要求：
- 把 "API 测试任务模板" 作为一个新的任务类型
- 保留原有的其他任务类型模板
- 在 "标签组合规则" 中，把 `<constraints>`、`<error_handling>`、`<examples>` 改为**必需标签**

### 2. 验证清单

确认修复后的 signature.md 包含：

| 检查项 | ✓ |
|--------|---|
| API 测试任务模板完整 | |
| 7 个标签都在 "必需标签" 列表中 | |
| 代码块正确闭合（有 ``` 开始和结束） | |
| 无空表格行 | |

### 3. 输出格式

```markdown
## 修复后的 rules/signature.md

{完整文件内容}

## 验证结果

| 检查项 | ✓ |
|--------|---|
| ... | ✓ |
```

---

现在执行任务。
```
