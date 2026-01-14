# 系统化调试指南

## 原则

**NEVER guess. Always validate.**

调试不是猜测游戏，而是系统化的科学方法。

## 4 阶段流程

### 阶段 1: REPRODUCE (复现)

**目标**: 可靠地复现问题

```
[ ] 获取错误信息完整内容
[ ] 确定复现步骤
[ ] 创建最小复现案例
[ ] 记录环境信息
```

**产出**: 复现脚本或步骤

```python
# 最小复现案例
def reproduce_issue():
    """
    复现步骤:
    1. 创建 DailyReport
    2. 提交日报
    3. 状态变为 trend_pending (应该是 raw_submitted)
    """
    report = DailyReport(...)
    report.submit()  # BUG: 状态跳变
    assert report.status == "raw_submitted"  # 失败
```

### 阶段 2: HYPOTHESIZE (假设)

**目标**: 形成可验证的假设

```
假设 1: 状态机转换逻辑有误
  - 原因: submit() 可能直接设置为 trend_pending
  - 验证: 检查 submit() 源码

假设 2: 数据库触发器干预
  - 原因: 可能有 AFTER INSERT 触发器
  - 验证: 检查数据库触发器

假设 3: 事件监听器副作用
  - 原因: 可能有监听 submitted 事件的处理器
  - 验证: 检查事件订阅
```

**规则**: 
- 记录所有假设
- 按可能性排序
- 不要同时验证多个假设

### 阶段 3: VALIDATE (验证)

**目标**: 系统地验证每个假设

```python
# 验证假设 1
def test_hypothesis_1():
    """假设: submit() 直接设置 trend_pending"""
    # 添加日志追踪
    with mock.patch.object(DailyReport, 'submit') as m:
        report = DailyReport(...)
        report.submit()
        # 检查 submit 内部调用
        print(m.call_args_list)
```

**记录**:
```
假设 1: ❌ 排除 - submit() 正确设置 raw_submitted
假设 2: ✅ 确认 - 触发器将状态改为 trend_pending
```

### 阶段 4: FIX (修复)

**目标**: 修复问题并验证不引入新问题

```python
# 修复
def fix_trigger():
    """修复触发器逻辑"""
    # 1. 移除错误的触发器
    # 2. 或修改触发器条件
    pass

# 验证修复
def test_fix_works():
    """验证原问题已修复"""
    report = DailyReport(...)
    report.submit()
    assert report.status == "raw_submitted"

def test_fix_no_regression():
    """验证没有引入新问题"""
    # 运行所有相关测试
    pass
```

## 检查清单

- [ ] 问题可复现
- [ ] 假设已记录
- [ ] 根因已确认
- [ ] 修复已验证
- [ ] 回归测试通过

## 常见陷阱

### ❌ 猜测修复

```python
# 错误: 没有验证假设就修复
def quick_fix():
    # "可能是这个问题"
    report.status = "raw_submitted"  # 掩盖问题
```

### ❌ 只修不测

```python
# 错误: 修复后没有验证
def fix_without_test():
    fix_the_bug()
    # 没有验证修复是否生效
    # 没有验证是否引入新问题
```

### ❌ 修改太多

```python
# 错误: 一次修改多处
def fix_everything():
    fix_trigger()
    fix_submit()
    fix_listener()
    # 无法确定哪个修复生效
```
