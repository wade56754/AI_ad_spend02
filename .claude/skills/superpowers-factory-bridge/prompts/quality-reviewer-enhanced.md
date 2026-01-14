# Quality Reviewer with SuperClaude Enhancement

> **用途**: 质量审查子代理提示词模板 (带 SuperClaude 增强)
> **调用方式**: Task tool (review)

## 子代理调度模板

```
Task tool (review):
  description: "Review Task N for code quality"
  prompt: |
    你正在使用 SuperClaude 分析审查 Task N 的代码质量。

    ## 预审查: SuperClaude 分析

    首先执行 /sc:analyze 对变更文件进行分析:
    /sc:analyze <changed_files>

    ## 质量维度

    ### 1. 代码质量 (Code Quality)

    检查项:
    - [ ] 命名清晰 (描述是什么，而非怎么做)
    - [ ] 无魔法数字
    - [ ] 错误处理完善
    - [ ] 类型注解完整

    示例 - 好的命名:
    ```python
    # ✅ 好
    def calculate_profit_margin(revenue: Decimal, cost: Decimal) -> Decimal:
        pass

    # ❌ 差
    def calc(r, c):
        pass
    ```

    ### 2. 测试质量 (Testing Quality)

    检查项:
    - [ ] 测试验证行为 (而非 mock 行为)
    - [ ] 边界情况覆盖
    - [ ] TDD 遵循 (测试先于代码)

    反模式检测:
    ```python
    # ❌ 反模式: 测试 mock 行为而非真实行为
    def test_bad():
        mock.return_value = expected
        result = service.method()
        assert result == expected  # 这只测试了 mock

    # ✅ 正确: 测试真实行为
    def test_good():
        # 设置真实数据
        db.add(entity)
        # 调用方法
        result = service.method()
        # 验证真实结果
        assert result.status == 'expected'
    ```

    ### 3. 模式合规 (Pattern Compliance)

    检查项:
    - [ ] 遵循现有模式
    - [ ] 使用注册组件 (COMPONENT_REGISTRY.md)
    - [ ] 无反模式

    后端模式:
    ```
    Router (HTTP 适配器) → Service (业务逻辑) → Model (数据持久化)
    ```

    前端模式:
    ```
    Page → Components → Hooks → Services → API
    ```

    ### 4. 安全性 (Security)

    检查项:
    - [ ] 无 SQL 注入漏洞
    - [ ] 无硬编码凭证
    - [ ] 输入验证存在

    危险模式检测:
    ```python
    # ❌ SQL 注入风险
    query = f"SELECT * FROM users WHERE id = {user_id}"

    # ✅ 安全的参数化查询
    query = select(User).where(User.id == user_id)
    ```

    ### 5. 性能 (Performance)

    检查项:
    - [ ] 无 N+1 查询
    - [ ] 适当使用 eager loading
    - [ ] 无不必要的数据库调用

    N+1 检测:
    ```python
    # ❌ N+1 问题
    for project in projects:
        accounts = project.ad_accounts  # 每次循环都查询

    # ✅ Eager loading
    projects = session.query(Project).options(
        joinedload(Project.ad_accounts)
    ).all()
    ```

    ## 质量评分

    计算公式:
    ```
    score = (passing_checks / total_checks) * 100
    ```

    判定标准:
    - score >= 90: 优秀 (PASS)
    - score >= 75: 合格 (PASS with recommendations)
    - score < 75: 不合格 (FAIL with required fixes)

    ## 输出格式

    ### 质量报告

    | 维度 | 检查项 | 状态 | 详情 |
    |------|-------|------|------|
    | 代码质量 | 命名 | ✅/❌ | [说明] |
    | 代码质量 | 魔法数字 | ✅/❌ | [说明] |
    | 测试质量 | 行为验证 | ✅/❌ | [说明] |
    | 测试质量 | 边界覆盖 | ✅/❌ | [说明] |
    | 模式合规 | 层次遵循 | ✅/❌ | [说明] |
    | 安全性 | SQL 注入 | ✅/❌ | [说明] |
    | 性能 | N+1 查询 | ✅/❌ | [说明] |

    **质量评分**: XX/100

    **总体结果**: PASS / FAIL

    ### 改进建议

    1. [建议 1]
    2. [建议 2]
    3. [建议 3]
```

## 使用示例

```
Task tool (review):
  description: "Review Task 3: TopupService.approve for code quality"
  prompt: |
    你正在使用 SuperClaude 分析审查 Task 3: TopupService.approve 的代码质量。

    ## 变更文件
    - backend/services/topup_service.py
    - backend/tests/services/test_topup_service.py

    ## 预审查: SuperClaude 分析

    /sc:analyze backend/services/topup_service.py backend/tests/services/test_topup_service.py

    ## 质量维度检查

    ### 1. 代码质量
    - [ ] approve 方法命名清晰
    - [ ] 无魔法数字 (状态值应来自常量)
    - [ ] 异常处理完善 (TopupPermissionError, TopupStateError)
    - [ ] 类型注解: 参数和返回值都有注解

    ### 2. 测试质量
    - [ ] test_approve_success 验证真实状态变更
    - [ ] test_approve_invalid_role 测试权限拒绝
    - [ ] test_approve_invalid_status 测试状态转换拒绝

    ### 3. 模式合规
    - [ ] Service 层不直接处理 HTTP
    - [ ] 使用 Repository/Model 访问数据

    ### 4. 安全性
    - [ ] 角色检查在方法开始处
    - [ ] 无直接 SQL 拼接

    ### 5. 性能
    - [ ] 单次数据库查询获取充值申请
    - [ ] 无循环内查询

    ## 输出质量报告
```

## 审查原则

1. **客观评分**: 基于检查项计算分数
2. **可操作建议**: 每个问题都有改进建议
3. **SuperClaude 增强**: 利用 /sc:analyze 深度分析
4. **模式优先**: 遵循已建立的代码模式
5. **安全第一**: 安全问题是阻断项
