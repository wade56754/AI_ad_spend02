# AI 使用规则（Claude / Cursor / GitHub Copilot）

📌 模型生成代码时必须：
- 主动对照 docs/core/* 下 SoT 文件进行行为校验
- 使用 API_DEVELOPMENT_FLOW 流程开发接口
- 使用 DATA_SCHEMA 进行字段检查
- 遇到冲突时停止生成并给出理由，不允许胡编填补

📌 禁止行为：
- 修改或创设数据库结构
- 引入不被规范允许的字段/角色/模型
- 自创 API 设计风格或响应格式
- 忽略架构文件直接生成实现代码
