# 代码改进提示词 (Improve Prompt)

## 目标

基于用户反馈，增量改进现有代码，而不是重写。

## 改进原则

### 1. 最小化变更
- 只修改必要的部分
- 保持现有代码风格
- 不引入不必要的重构

### 2. 向后兼容
- 不破坏现有 API 接口
- 不改变数据库 Schema（除非明确要求）
- 保持测试通过

### 3. 增量迭代
- 每次改进一个功能点
- 可验证的小步骤
- 便于回滚

## 改进流程

```
1. 理解反馈 → 2. 定位代码 → 3. 评估影响 → 4. 实施改进 → 5. 验证结果
```

### Step 1: 理解反馈
- 用户具体要改什么？
- 问题的根本原因是什么？
- 期望的结果是什么？

### Step 2: 定位代码
- 哪些文件需要修改？
- 涉及哪些函数/类？
- 有哪些依赖关系？

### Step 3: 评估影响
- 修改会影响哪些其他功能？
- 是否需要更新测试？
- 是否需要数据迁移？

### Step 4: 实施改进
- 生成最小化的 diff
- 保持代码风格一致
- 添加必要的注释

### Step 5: 验证结果
- 相关测试是否通过？
- 功能是否符合预期？
- 是否引入新问题？

## 改进类型

### 功能增强
```python
# 改进前
def get_reports(db: Session) -> List[Report]:
    return db.query(Report).all()

# 改进后 - 添加分页
def get_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[Report]:
    return db.query(Report).offset(skip).limit(limit).all()
```

### 性能优化
```python
# 改进前 - N+1 查询问题
reports = db.query(Report).all()
for report in reports:
    print(report.user.name)  # 每次触发额外查询

# 改进后 - 预加载
from sqlalchemy.orm import joinedload

reports = db.query(Report).options(joinedload(Report.user)).all()
for report in reports:
    print(report.user.name)  # 已预加载，无额外查询
```

### Bug 修复
```python
# 改进前 - 边界条件未处理
def calculate_rate(total: int, count: int) -> float:
    return total / count  # ZeroDivisionError 风险

# 改进后 - 添加保护
def calculate_rate(total: int, count: int) -> float:
    if count == 0:
        return 0.0
    return total / count
```

### 代码质量
```python
# 改进前 - 硬编码
if status == "submitted":
    ...

# 改进后 - 使用枚举
# SoT: STATE_MACHINE.md#daily_report
from enums import ReportStatus

if status == ReportStatus.RAW_SUBMITTED:
    ...
```

## 输出格式

```diff
--- a/backend/services/report_service.py
+++ b/backend/services/report_service.py
@@ -10,6 +10,7 @@ class ReportService:
     def get_reports(
         self,
         db: Session,
+        skip: int = 0,
+        limit: int = 100,
     ) -> List[Report]:
-        return db.query(Report).all()
+        return db.query(Report).offset(skip).limit(limit).all()
```

## 改进清单

改进代码后必须确认:

- [ ] 变更范围最小化
- [ ] 现有测试仍然通过
- [ ] API 接口保持兼容
- [ ] 代码风格保持一致
- [ ] 添加了必要的测试
- [ ] 更新了相关文档


