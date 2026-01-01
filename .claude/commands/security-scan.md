# /security-scan - 安全扫描

> **版本**: v1.0
> **优先级**: 中
> **依赖**: bandit (Python), eslint-plugin-security (JS/TS)

---

## 用途

扫描代码中的安全漏洞，包括 OWASP Top 10、敏感信息泄露、不安全的依赖等。

---

## 使用方式

```bash
/security-scan                    # 扫描整个项目
/security-scan <file>             # 扫描指定文件
/security-scan <dir>              # 扫描指定目录
/security-scan --backend          # 仅后端
/security-scan --frontend         # 仅前端
/security-scan --deps             # 仅依赖检查
/security-scan --severity high    # 仅高危漏洞
```

---

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `<file>` | 目标文件 | `backend/routers/auth.py` |
| `<dir>` | 目标目录 | `backend/` |
| `--backend` | 仅后端代码 | |
| `--frontend` | 仅前端代码 | |
| `--deps` | 仅依赖检查 | |
| `--severity` | 过滤严重级别 | `high`, `medium`, `low` |
| `--format` | 输出格式 | `table`, `json`, `sarif` |

---

## 检查项目

### OWASP Top 10

| 类别 | 检查内容 |
|------|---------|
| A01 访问控制 | 权限检查缺失、IDOR |
| A02 加密失败 | 明文密码、弱加密 |
| A03 注入 | SQL、命令、XSS |
| A04 不安全设计 | 业务逻辑漏洞 |
| A05 安全配置 | 默认密码、调试开启 |
| A06 脆弱组件 | 已知漏洞依赖 |
| A07 认证失败 | 弱密码、会话管理 |
| A08 数据完整性 | 反序列化、CI/CD |
| A09 日志监控 | 敏感信息日志 |
| A10 SSRF | 服务端请求伪造 |

### 后端专项 (Python/FastAPI)

| 检查项 | 说明 |
|--------|------|
| SQL 注入 | 原始 SQL 拼接 |
| 命令注入 | os.system, subprocess |
| 路径遍历 | 文件操作未验证 |
| 敏感信息 | 硬编码密钥、token |
| CORS 配置 | 过于宽松的源 |
| JWT 安全 | 弱密钥、无过期 |

### 前端专项 (TypeScript/React)

| 检查项 | 说明 |
|--------|------|
| XSS | dangerouslySetInnerHTML |
| 敏感存储 | localStorage 存密码 |
| 不安全链接 | target="_blank" 无 rel |
| 明文传输 | HTTP 请求 |
| 依赖漏洞 | npm audit |

---

## 示例

### 全项目扫描

```bash
/security-scan
```

输出:
```
🔒 安全扫描报告
================

扫描范围: 全项目
扫描文件: 156 个
扫描时间: 12.3s

┌──────────────────────────────────────────────────────────┐
│ 发现 5 个安全问题                                         │
├──────────┬────────┬──────────────────────────────────────┤
│ 严重级别 │ 数量   │ 说明                                 │
├──────────┼────────┼──────────────────────────────────────┤
│ 🔴 高危  │ 1      │ SQL 注入风险                         │
│ 🟡 中危  │ 2      │ 硬编码密钥、XSS                      │
│ 🟢 低危  │ 2      │ 不安全链接                           │
└──────────┴────────┴──────────────────────────────────────┘

详细信息:

🔴 [HIGH] backend/services/report_service.py:45
   SQL 注入风险: 使用字符串拼接构建 SQL
   修复建议: 使用参数化查询

🟡 [MEDIUM] backend/config.py:12
   硬编码密钥: JWT_SECRET 直接写在代码中
   修复建议: 使用环境变量

...
```

### 仅检查依赖

```bash
/security-scan --deps
```

输出:
```
📦 依赖安全检查
===============

后端 (requirements.txt):
  ✅ 无已知漏洞

前端 (package.json):
  ⚠️ 发现 2 个漏洞:
    - lodash < 4.17.21 (原型污染)
    - axios < 1.6.0 (SSRF)

修复命令:
  npm audit fix
```

---

## 与 SoT 集成

安全扫描会额外检查 SoT 相关安全规则:

1. **角色权限**: 检查是否有越权访问
2. **数据隔离**: 检查是否有跨项目/账户访问
3. **审计日志**: 检查敏感操作是否记录

---

## 输出

1. 终端报告
2. `security-report.json` (可选)
3. SARIF 格式 (可选，用于 GitHub Security)
