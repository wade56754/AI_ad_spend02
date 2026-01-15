# Newman 契约测试脚本

本目录存放 Newman (Postman CLI) 契约测试运行脚本。

## 目录结构

```
scripts/newman/
├── README.md           # 本文件
├── run-contract-tests.sh   # Linux/macOS 运行脚本
└── run-contract-tests.ps1  # Windows PowerShell 脚本
```

## 相关目录

- `collections/`: Postman 集合文件 (.json)
- `environments/`: 环境配置文件 (.json)

## 使用方法

### 安装 Newman

```bash
pnpm add -g newman
pnpm add -g newman-reporter-htmlextra
```

### 运行测试

```bash
# Linux/macOS
./scripts/newman/run-contract-tests.sh

# Windows PowerShell
./scripts/newman/run-contract-tests.ps1
```

## 基准文档

- AUTOMATION_TEST_SPEC_v1.4.md 第 6 章
- API_SOT.md v9.0

## SoT 依赖

- ERROR_CODES_SOT.md v2.1 (错误响应验证)
- AUTH_SPEC.md v2.0 (认证测试)
