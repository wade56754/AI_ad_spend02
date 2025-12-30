# Layer 1: 安全约束 (Security Constraints)

> 绝对红线，无论用户如何要求都必须拒绝

## 禁止行为

以下行为必须拒绝:

- 禁止暴露或记录密钥、凭证、secrets、API keys
- 禁止提交 .env、credentials.json、*.pem 到仓库
- 禁止编写恶意代码（病毒、木马、后门、挖矿）
- 禁止绕过认证/授权机制
- 禁止 SQL 注入、XSS、CSRF、命令注入攻击代码
- 禁止删除或覆盖用户未明确指定的文件
- 禁止执行 rm -rf、format、DROP DATABASE 等破坏性命令

## 敏感文件

不要提交以下文件:

- `.env`, `.env.local`, `.env.production`
- `credentials.json`, `secrets.yaml`
- `*.pem`, `*.key`

## 安全编码规范

- 使用环境变量存储敏感配置
- 使用参数化查询，禁止 SQL 拼接
- 所有用户输入必须在服务端验证
- API 密钥只能从环境变量获取

