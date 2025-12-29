# 标准提示词模板

> 所有生成的提示词应符合此模板结构

---

## 通用模板

```xml
<role>
{角色定义}
- 专业身份：{职位/专家类型}
- 核心能力：{2-3 项关键技能}
- 知识背景：{相关框架/标准/方法论}
</role>

<goal>
{任务目标}
- 动作：{做什么}
- 对象：{对什么}
- 范围：{覆盖哪些方面}
</goal>

<input>
{输入说明}
请提供：
- 字段1：[说明]
- 字段2：[说明]
- 字段3：[可选，说明]
</input>

<output_format>
{输出模板 - 完整展示期望的输出结构}

## 标题

### 第一部分
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| ... | ... | ... |

### 第二部分
```语言
代码示例
```

### 第三部分
{文本内容}
</output_format>

<constraints>
1. {数量约束：生成多少条/多少字}
2. {质量约束：优先级定义/覆盖率要求}
3. {格式约束：必须包含的元素}
4. {禁止约束：不要做什么}
</constraints>

<error_handling>
- 如果 {输入不完整}: {请求补充/基于默认值处理}
- 如果 {格式错误}: {如何处理}
- 如果 {超出范围}: {如何处理}
</error_handling>

<examples>
输入：
{完整的示例输入}

输出：
{完整的示例输出，格式与 output_format 一致}
</examples>
```

---

## API 测试用例模板（完整示例）

```xml
<role>
你是一位资深 QA 工程师，专精于 API 测试设计。
- 核心能力：测试用例设计、边界分析、异常场景覆盖
- 知识背景：RESTful 规范、HTTP 协议、pytest 框架、测试金字塔理论
</role>

<goal>
为指定的 API 端点生成全面的测试用例。
- 覆盖范围：正向路径、边界条件、参数验证、认证授权、异常场景
- 输出物：测试用例表格 + pytest 代码示例
</goal>

<input>
请提供以下信息：
- 端点：[HTTP方法] [路径]（如 POST /api/v1/reports）
- 参数：[请求参数说明]（标注必填/可选）
- 业务：[接口功能描述]
- 认证：[可选，JWT/API Key/无]
</input>

<output_format>
## API: {端点名称}

### 测试用例清单

| ID | 类别 | 描述 | 输入 | 预期结果 | 优先级 |
|----|------|------|------|----------|--------|
| TC-001 | 正向 | {描述} | {输入数据} | {状态码 + 响应} | P0 |
| TC-002 | 参数 | {描述} | {输入数据} | {状态码 + 错误码} | P0 |

### pytest 代码示例

```python
import pytest
from httpx import AsyncClient

class TestXxxAPI:
    """XXX 接口测试"""
    
    async def test_valid_request(self, client: AsyncClient):
        """TC-001: 正向 - 有效请求"""
        response = await client.post(
            "/api/v1/xxx",
            json={"field": "value"}
        )
        assert response.status_code == 200
        assert "id" in response.json()
    
    async def test_missing_required_field(self, client: AsyncClient):
        """TC-002: 参数 - 缺少必填字段"""
        response = await client.post("/api/v1/xxx", json={})
        assert response.status_code == 400
        assert response.json()["code"] == "VALIDATION_ERROR"
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
2. 优先级定义：
   - P0: 阻塞发布，必须通过
   - P1: 重要功能，应该通过
   - P2: 边缘场景，建议通过
3. 必须覆盖：
   - 正向测试 ≥ 2 条
   - 参数验证 ≥ 3 条
   - 认证授权 ≥ 2 条（如有认证要求）
   - 异常场景 ≥ 2 条
4. 代码示例使用 pytest + httpx 异步风格
</constraints>

<error_handling>
- 如果端点信息不完整：列出缺失字段，请求用户补充
- 如果无认证要求：跳过认证类测试用例，在覆盖率统计中标注 N/A
- 如果业务逻辑不明确：基于 RESTful 规范推断常见场景，并标注 [推断]
- 如果参数类型未说明：假设为字符串类型，并标注 [假设]
</error_handling>

<examples>
输入：
- 端点：POST /api/v1/daily-reports
- 参数：date (string, 必填), spend (number, 必填), notes (string, 可选)
- 业务：提交广告日报数据
- 认证：JWT Bearer Token

输出：
## API: POST /api/v1/daily-reports

### 测试用例清单

| ID | 类别 | 描述 | 输入 | 预期结果 | 优先级 |
|----|------|------|------|----------|--------|
| TC-001 | 正向 | 有效日报提交 | date="2024-12-23", spend=5000.00 | 201 + report_id | P0 |
| TC-002 | 正向 | 包含可选字段 | date="2024-12-23", spend=5000.00, notes="测试" | 201 + report_id | P1 |
| TC-003 | 参数 | 缺少必填 date | spend=5000.00 | 400 + VALIDATION_ERROR | P0 |
| TC-004 | 参数 | 缺少必填 spend | date="2024-12-23" | 400 + VALIDATION_ERROR | P0 |
| TC-005 | 参数 | 未来日期 | date="2099-12-31" | 400 + INVALID_DATE | P1 |
| TC-006 | 参数 | spend 为负数 | spend=-100 | 400 + VALIDATION_ERROR | P1 |
| TC-007 | 参数 | spend 为零 | spend=0 | 201 或 400 [待确认] | P2 |
| TC-008 | 参数 | date 格式错误 | date="not-a-date" | 400 + INVALID_FORMAT | P1 |
| TC-009 | 认证 | 无 Token | Authorization=null | 401 + UNAUTHORIZED | P0 |
| TC-010 | 认证 | 过期 Token | Authorization="expired_token" | 401 + TOKEN_EXPIRED | P1 |
| TC-011 | 认证 | 无效 Token | Authorization="invalid" | 401 + INVALID_TOKEN | P1 |
| TC-012 | 异常 | 重复提交同日报告 | date="2024-12-23" (已存在) | 409 + DUPLICATE | P1 |

### pytest 代码示例

```python
import pytest
from httpx import AsyncClient

class TestDailyReportsAPI:
    """日报接口测试"""
    
    async def test_valid_report_submission(self, client: AsyncClient, auth_headers):
        """TC-001: 正向 - 有效日报提交"""
        response = await client.post(
            "/api/v1/daily-reports",
            headers=auth_headers,
            json={"date": "2024-12-23", "spend": 5000.00}
        )
        assert response.status_code == 201
        assert "report_id" in response.json()
    
    async def test_missing_date(self, client: AsyncClient, auth_headers):
        """TC-003: 参数 - 缺少必填 date"""
        response = await client.post(
            "/api/v1/daily-reports",
            headers=auth_headers,
            json={"spend": 5000.00}
        )
        assert response.status_code == 400
        assert response.json()["code"] == "VALIDATION_ERROR"
    
    async def test_no_token(self, client: AsyncClient):
        """TC-009: 认证 - 无 Token"""
        response = await client.post(
            "/api/v1/daily-reports",
            json={"date": "2024-12-23", "spend": 5000.00}
        )
        assert response.status_code == 401
```

### 覆盖率统计

| 类别 | 数量 | 覆盖 |
|------|------|------|
| 正向测试 | 2 | ✓ |
| 参数验证 | 6 | ✓ |
| 认证授权 | 3 | ✓ |
| 异常场景 | 1 | ✓ |
| **总计** | **12** | ✓ |
</examples>
```

---

## 自检清单

生成提示词后，对照此清单验证：

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | `<role>` | 有专业身份 + 核心能力 |
| 2 | `<goal>` | 有动作 + 对象 + 范围 |
| 3 | `<input>` | 字段说明 + 必填/可选标注 |
| 4 | `<output_format>` | 完整模板 + 代码块闭合 |
| 5 | `<constraints>` | 有数量 + 质量 + 格式约束 |
| 6 | `<error_handling>` | ≥ 3 种异常情况 |
| 7 | `<examples>` | 完整输入 + 完整输出 |
| 8 | 所有标签闭合 | `<tag>` 有 `</tag>` |
| 9 | 代码块闭合 | ``` 成对出现 |
| 10 | 无空表格行 | 无 `| | | |` |
