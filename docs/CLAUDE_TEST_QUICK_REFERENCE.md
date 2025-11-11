# 🤖 Claude Code 测试工作快速参考

## ⚡ 一键启动

```bash
# 启动交互式测试菜单
python scripts/claude_test_starter.py

# 快速运行所有测试
python run_tests.py --coverage
```

## 🔧 常用 Claude 提示

### 测试失败时
```claude
测试失败，请帮我：
1. 分析错误原因
2. 提供修复代码
3. 优化测试性能
```

### 需要生成测试时
```claude
请为 [功能名] 生成完整的测试用例，包括：
- 正常场景
- 边界条件
- 异常处理
```

### 性能优化
```claude
这些测试运行太慢，请：
1. 分析性能瓶颈
2. 优化数据库查询
3. 减少重复代码
```

## 📊 测试命令速查

| 功能 | 命令 | 说明 |
|------|------|------|
| 运行所有测试 | `python run_tests.py` | 执行完整测试套件 |
| 单元测试 | `python run_tests.py --type unit` | 只运行单元测试 |
| 覆盖率报告 | `python run_tests.py --coverage` | 生成HTML覆盖率报告 |
| 并行执行 | `python run_tests.py --parallel 4` | 4个进程并行执行 |
| 失败测试 | `python run_tests.py --lf` | 只运行上次失败的测试 |
| 特定文件 | `python run_tests.py --file tests/test_models.py` | 运行特定文件 |
| 生成报告 | `python run_tests.py --html-report` | 生成HTML测试报告 |

## 🚨 常见问题快速处理

### 1. 数据库连接错误
```claude
数据库连接失败，请：
1. 检查 .env 文件配置
2. 验证数据库服务状态
3. 修复连接字符串
```

### 2. 导入错误
```claude
导入模块失败，请：
1. 检查 PYTHONPATH
2. 验证文件路径
3. 修复循环导入
```

### 3. 权限错误
```claude
权限验证失败，请：
1. 检查 JWT_SECRET
2. 验证令牌格式
3. 确认用户权限
```

### 4. 性能问题
```claude
测试太慢，请：
1. 使用 fixtures 复用数据
2. 添加数据库索引
3. 优化查询语句
4. 使用 parallel 并行执行
```

## 💡 高效技巧

### 1. 批量修复
```claude
批量修复所有测试中的：
- 导入错误
- 类型注解
- 文档字符串
```

### 2. 测试模板生成
```claude
为所有 API 端点生成标准测试模板，包括：
- GET/POST/PUT/DELETE
- 认证测试
- 参数验证
- 错误处理
```

### 3. 覆盖率优化
```claude
分析覆盖率报告，为未覆盖的代码：
- 生成测试用例
- 增加边界测试
- 添加异常处理
```

## 📈 进度跟踪技巧

### 1. 实时更新
```claude
请更新测试进度：
- 完成阶段1.1，通过率100%
- 耗时25分钟
- 修复了2个问题
```

### 2. 生成日报
```claude
生成今日测试报告，包括：
- 执行的测试
- 通过率
- 发现的问题
- 修复方案
```

## 🔍 调试技巧

### 1. 详细输出
```bash
pytest -v -s tests/test_models.py::TestUser
```

### 2. 进入调试
```bash
pytest --pdb tests/test_models.py::TestUser::test_create
```

### 3. 只运行失败
```bash
pytest --lf -v
```

## 📝 文件位置速查

| 文件 | 路径 | 说明 |
|------|------|------|
| 测试清单 | `docs/TEST_TASK_CHECKLIST_CLAUDE.md` | Claude优化版任务清单 |
| 测试框架 | `tests/README.md` | 测试框架说明 |
| 覆盖率报告 | `htmlcov/index.html` | HTML覆盖率报告 |
| 测试日志 | `tests.log` | 测试执行日志 |
| 启动脚本 | `scripts/claude_test_starter.py` | 测试启动器 |

## 🎯 最佳实践

### 1. 先运行冒烟测试
```bash
python run_tests.py --file tests/test_smoke.py
```

### 2. 按阶段逐步执行
- 不要一次性运行所有测试
- 每个阶段完成后检查通过率
- 遇到问题立即修复

### 3. 保持沟通
- 及时告诉 Claude 遇到的问题
- 提供足够的上下文
- 请求具体的解决方案

## 🆘 求助提示

如果遇到无法解决的问题：
```claude
我遇到了以下问题：
[详细描述问题]
[提供错误信息]
[说明已尝试的解决方法]
请提供详细的解决方案
```

---

**记住**：Claude Code 是您的智能测试助手，充分利用它的能力可以让测试工作事半功倍！