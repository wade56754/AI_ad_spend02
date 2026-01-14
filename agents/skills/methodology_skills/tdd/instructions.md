# TDD 方法论指南

## 铁律

**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

这是 TDD 的核心原则，没有任何例外。

## Red-Green-Refactor 循环

### 1. RED - 写一个失败的测试

```python
def test_should_calculate_total():
    # Arrange
    calculator = Calculator()
    
    # Act
    result = calculator.add(2, 3)
    
    # Assert
    assert result == 5
```

运行测试，确认它失败了。

### 2. 验证 RED

确认测试失败是因为预期的原因 (功能未实现)，而不是因为:
- 语法错误
- 导入错误
- 环境问题

### 3. GREEN - 写最小代码使测试通过

```python
class Calculator:
    def add(self, a, b):
        return a + b  # 最小实现
```

**关键**: 只写使测试通过的最小代码，不要过度设计。

### 4. 验证 GREEN

运行所有测试，确认:
- 新测试通过
- 旧测试没有被破坏

### 5. REFACTOR - 清理代码

现在可以重构代码，同时保持所有测试通过:
- 改善命名
- 消除重复
- 简化逻辑

## 反模式

### ❌ 测试后补

```python
# 错误: 先写了实现
class Calculator:
    def add(self, a, b):
        return a + b

# 然后才写测试 (这不是 TDD!)
def test_add():
    assert Calculator().add(2, 3) == 5
```

### ❌ 跳过红色阶段

```python
# 错误: 测试和实现同时写
def test_add():
    assert Calculator().add(2, 3) == 5

class Calculator:
    def add(self, a, b):
        return a + b
```

### ❌ 过度实现

```python
# 错误: 实现了太多功能
def test_add():
    assert Calculator().add(2, 3) == 5

class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):  # 没有测试要求这个!
        return a - b
```

## 检查清单

- [ ] 写测试之前，确认功能未实现
- [ ] 运行测试，确认失败
- [ ] 验证失败原因正确
- [ ] 只写最小代码使测试通过
- [ ] 运行所有测试，确认通过
- [ ] 重构 (可选)，保持测试通过

## 与 SoT 集成

在本项目中，TDD 需要遵守 SoT 约束:

1. **状态机**: 测试状态转换时使用 `STATE_MACHINE.md` 定义的 8 状态
2. **角色**: 测试权限时使用 `AUTH_SPEC.md` 定义的 6 角色
3. **错误码**: 测试错误处理时使用 `ERROR_CODES_SOT.md` 定义的错误码
