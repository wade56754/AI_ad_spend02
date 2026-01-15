# AI Ad API Automation Test Skill

API 自动化测试编排与执行 Skill，基于 [sanbercode-api-automation-boilerplate](https://github.com/jfrelis/sanbercode-api-automation-boilerplate) 模式。

## 概述

本 Skill 支持两种测试模式：

1. **pytest 模式**：生成符合 `AUTOMATION_TEST_SPEC_v1.4` 规范的 Python 测试代码
2. **Newman 模式**：使用 Postman Collection 执行契约测试（可选扩展）

## 目录结构

```
.claude/skills/ai-ad-api-automation-test/
├── SKILL.md                           # Skill 定义文件
├── README.md                          # 本文件
└── templates/                         # 模板文件
    ├── newman_runner.js               # Newman 执行脚本
    ├── package.json                   # npm 依赖配置
    ├── daily_report_api.postman_collection.json  # Postman Collection 示例
    └── local.postman_environment.json # 环境配置示例
```

## 使用方式

### 1. 生成 pytest 测试代码

```
使用 ai-ad-api-automation-test，
mode = GENERATE，
target_module = "daily_report"，
test_level = "L2"。

生成完整的 API 测试文件。
```

### 2. 运行 pytest 测试

```
使用 ai-ad-api-automation-test，
mode = RUN，
test_level = "L2"。

执行 L2 API 测试并输出结果。
```

### 3. 使用 Newman 执行契约测试

#### 安装依赖

```bash
cd scripts/newman
npm install
```

#### 设置目录结构

```bash
mkdir -p collections environments reports
```

#### 执行测试

```bash
# 本地测试
npm run test:local

# 指定 Collection
npm run test:daily-report

# 全部测试
npm run test:all
```

### 4. 生成测试报告

```
使用 ai-ad-api-automation-test，
mode = REPORT，
output_format = "html"。

生成包含覆盖率和 SoT 对齐检查的完整报告。
```

## SoT 对齐

所有测试必须对齐以下 SoT 文档：

| 优先级 | 文档 | 用途 |
|--------|------|------|
| P0 | STATE_MACHINE.md v2.6 | 状态枚举、流转规则 |
| P0 | DATA_SCHEMA.md v5.2 | 数据结构约束 |
| P1 | API_SOT.md v9.0 | API 端点契约 |
| P1 | ERROR_CODES_SOT.md v2.1 | 错误码定义 |
| P1 | DATA_SCHEMA.md v5.11 §3.4.4 | 账本分录规则 |
| P3 | AUTH_SPEC.md v2.0 | 角色权限矩阵 |

## 参考资料

- [sanbercode-api-automation-boilerplate](https://github.com/jfrelis/sanbercode-api-automation-boilerplate)
- [Newman Documentation](https://learning.postman.com/docs/collections/using-newman-cli/command-line-integration-with-newman/)
- [newman-reporter-htmlextra](https://www.npmjs.com/package/newman-reporter-htmlextra)
- 项目内 `docs/testing/AUTOMATION_TEST_SPEC_v1.4.md`

## 版本

- **v1.0** (2025-12-01): 初始版本
