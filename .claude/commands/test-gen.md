# /test-gen - 测试自动生成

> **版本**: v1.0
> **优先级**: 高
> **依赖**: pytest, jest/vitest

---

## 用途

自动为代码生成测试用例，支持后端 pytest 和前端 jest/vitest。

---

## 使用方式

```bash
/test-gen <file>              # 为指定文件生成测试
/test-gen <file> --unit       # 仅单元测试
/test-gen <file> --integration # 集成测试
/test-gen <file> --e2e        # 端到端测试
/test-gen <module>            # 为整个模块生成测试
```

---

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `<file>` | 目标文件路径 | `backend/services/daily_report.py` |
| `<module>` | 模块名称 | `daily-reports` |
| `--unit` | 仅生成单元测试 | |
| `--integration` | 仅生成集成测试 | |
| `--e2e` | 仅生成端到端测试 | |
| `--coverage` | 分析并补充覆盖率 | |

---

## 示例

### 后端测试生成

```bash
# 为服务生成测试
/test-gen backend/services/daily_report_service.py

# 为路由生成集成测试
/test-gen backend/routers/daily_reports.py --integration
```

### 前端测试生成

```bash
# 为组件生成测试
/test-gen frontend/src/features/daily-reports/components/DailyReportForm.tsx

# 为 hook 生成测试
/test-gen frontend/src/features/daily-reports/hooks/useDailyReports.ts
```

---

## 生成规则

### 后端 (pytest)

1. **命名**: `test_<module>_<function>.py`
2. **位置**: `backend/tests/` 对应目录
3. **依赖**: 自动 mock 数据库和外部服务
4. **覆盖**: 正常路径 + 边界条件 + 错误处理

### 前端 (vitest)

1. **命名**: `<Component>.test.tsx`
2. **位置**: 与组件同目录或 `__tests__/`
3. **依赖**: 自动 mock API 调用
4. **覆盖**: 渲染 + 交互 + 状态变化

---

## 测试模板

### 后端单元测试

```python
import pytest
from unittest.mock import Mock, patch
from backend.services.{module}_service import {Service}

class Test{Service}:
    @pytest.fixture
    def service(self):
        return {Service}(db=Mock())

    def test_{function}_success(self, service):
        # Arrange
        # Act
        # Assert
        pass

    def test_{function}_invalid_input(self, service):
        with pytest.raises(ValueError):
            pass
```

### 前端组件测试

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { {Component} } from './{Component}'

describe('{Component}', () => {
  it('renders correctly', () => {
    render(<{Component} />)
    expect(screen.getByRole('...')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    render(<{Component} />)
    fireEvent.click(screen.getByRole('button'))
    // Assert
  })
})
```

---

## SoT 合规

生成的测试必须验证:

1. **角色权限**: 测试 6 角色白名单
2. **状态流转**: 测试状态机转换
3. **Phase 1 约束**: 无自动阻断逻辑

---

## 输出

1. 测试文件生成到对应目录
2. 运行测试验证通过
3. 输出覆盖率报告
