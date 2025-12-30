# 项目规则：小红书自动发布工具

本文件定义了项目的核心规则和约束，Claude 在开发过程中必须遵守。

## 项目概述

- **项目名称**: 小红书自动发布工具 (XHS_AutoPublisher_v2)
- **技术栈**: N8N + Claude API + Gemini API + 飞书多维表格 + 小红书MCP + Telegram

## 核心目标

| 维度 | 目标 | 指标 |
|------|------|------|
| 效率 | 内容提效 | 2-3h→15min |
| 质量 | 质量稳定 | 通过率≥85% |
| 可靠性 | 系统稳定 | 成功率≥90% |
| 扩展性 | 多账号 | 支持3-5账号 |

## 功能模块优先级

| 优先级 | 模块 |
|--------|------|
| **P0** | 智能选题、内容创作+AI审核、数据存储(飞书)、通知(Telegram) |
| **P1** | 图片生成、热点抓取、半自动发布(MCP) |
| **P2** | 智能定时、互动数据回流、AI评分闭环 |

## N8N 命名规范

| 对象 | 规则 | 示例 |
|------|------|------|
| 工作流 | [功能]_[版本] | content_generator_v1 |
| 节点 | [动词]_[对象] | fetch_hot_topics |
| 变量 | camelCase | selectedTopicId |
| 凭证 | [服务]_[环境] | claude_api_prod |
| 子流程 | sub_[功能] | sub_ai_score |

## 数据表结构

### content_records (内容记录表)
核心字段: id, title, content_body, tags, ai_score, status, account_id, workflow_run_id

### accounts (账号管理表)
核心字段: id, name, status, last_publish_at, publish_count_today

### execution_logs (执行日志表)
核心字段: timestamp, level, workflow_id, event_type, message, context

## 状态机

### 内容状态
- DRAFT → AI_REVIEWED (score≥70) / REJECTED (score<70)
- AI_REVIEWED → PENDING_APPROVAL (人工确认)
- PENDING_APPROVAL → PUBLISHING → PUBLISHED / FAILED

### 账号状态
- ACTIVE: 可发布
- COOLDOWN: 暂停发布
- SUSPENDED: 禁止发布
- BANNED: 封禁

## 限频策略

- 单账号: 最多3篇/天
- 最小间隔: 4小时
- 触发冷却: 连续发布3篇 → COOLDOWN 8小时

## AI 评分体系 (100分)

| 维度 | 权重 |
|------|------|
| 点击力 | 30% |
| 内容力 | 25% |
| 价值感 | 20% |
| 平台适配 | 15% |
| 互动设计 | 10% |

通过标准: ≥80分可发布, 70-79需优化, <70重新生成

## 错误处理策略

| 层级 | 方式 | 场景 |
|------|------|------|
| 节点级 | Continue On Fail | API调用 |
| 工作流级 | Error Trigger | 全局异常 |
| 业务级 | 条件分支+重试 | AI失败/发布失败 |

## 安全规范

- API密钥: 使用环境变量或N8N凭证管理
- 禁止硬编码敏感信息
- .env 文件不提交到版本控制

## 参考文档

详细规范请参考:
- DEVELOPMENT_GUIDE.md - 完整开发指南
- xiaohongshu_auto_publisher_requirements_v2.0.docx.md - 需求文档
