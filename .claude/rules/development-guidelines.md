# 开发指南规则

本文件包含开发过程中必须遵循的技术规范。

## 项目结构

```
xiaohongshu_auto_publisher/
├── n8n/                           # N8N工作流
│   ├── workflows/                 # 主工作流JSON
│   ├── sub_workflows/             # 子工作流
│   └── credentials/               # 凭证配置说明
├── scripts/                       # 辅助脚本
├── config/                        # 配置文件
│   ├── prompts/                   # AI Prompt模板
│   └── prompt_registry.json       # Prompt版本注册表
├── tests/                         # 测试用例
│   ├── golden/                    # 金数据测试集
│   └── regression/                # 回归测试脚本
└── docker-compose.yml             # Docker编排
```

## 主工作流清单

| 工作流ID | 职责 | 触发方式 |
|----------|------|----------|
| content_generator_v1 | 智能选题→内容生成→AI审核→图片生成 | Schedule(每天9:00) / Manual |
| publish_scheduler_v1 | 检查发布队列→限频检查→MCP发布 | Schedule(每小时) / Webhook |
| data_collector_v1 | 定时抓取互动数据→计算真实评分 | Schedule(每天10:00, 22:00) |

## 子工作流清单

| 子工作流ID | 职责 | 超时 |
|------------|------|------|
| sub_ai_score | 执行5步AI审核 | 120s |
| sub_hot_topics | 抓取抖音/微博热搜 | 30s |
| sub_image_gen | 生成图片描述→调用Gemini | 60s |
| sub_publish | 调用小红书MCP发布 | 120s |
| sub_notify | 发送Telegram通知 | 10s |

## Prompt 版本管理

所有Prompt必须分配唯一的PROMPT_ID:

| PROMPT_ID | 用途 |
|-----------|------|
| TOPIC_GEN | 选题生成 |
| CONTENT_GEN | 内容创作 |
| REVIEW_STEP0-5 | 审核步骤 |
| IMAGE_DESC | 图片描述生成 |
| SCORE_CALC | 评分计算 |

每次AI调用必须记录:
- prompt_id
- prompt_version

## 日志事件类型

| 事件类型 | 级别 | 描述 |
|----------|------|------|
| WORKFLOW_START | INFO | 工作流开始 |
| WORKFLOW_SUCCESS | INFO | 工作流成功 |
| WORKFLOW_FAILED | ERROR | 工作流失败 |
| AI_API_CALL | INFO | AI API调用 |
| CONTENT_CREATED | INFO | 内容生成完成 |
| PUBLISH_SUCCESS | INFO | 发布成功 |
| PUBLISH_FAILED | ERROR | 发布失败 |

## 5步AI审核流程

| 步骤 | 检查项 | 通过标准 |
|------|--------|----------|
| Step 0 | 账号定位检查 | 匹配度≥80% |
| Step 1 | 三秒测试(标题+封面) | 点击力≥24分 |
| Step 2 | 首屏测试 | 前两屏传达价值 |
| Step 3 | 全文质量 | 内容力≥20+价值感≥16 |
| Step 4 | 互动设计 | 互动分≥8分 |
| Step 5 | 平台合规 | 适配≥12+敏感词通过 |

## API集成

### Claude API
- Model: claude-sonnet-4-20250514
- Max tokens: 4000
- 限频: 1秒间隔

### Gemini API
- 用途: 3:4竖图生成
- 分辨率: 1080x1440px

### 飞书API
- 用途: 数据存储
- 表格: content_records, accounts, execution_logs

## 测试规范

### TEST模式
通过 `test_mode: true` 启用:
- 数据存储到测试表(表名加 `_test` 后缀)
- 跳过真实发布
- 通知发送到测试频道

### 回归测试触发时机
- 修改主工作流节点
- 修改子工作流
- 修改Prompt
- 每周定期全量测试

## 部署要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核 |
| 内存 | 4GB | 8GB |
| 存储 | 50GB SSD | 100GB SSD |
| 系统 | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
