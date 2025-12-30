方案3：模块化Agent设计
typescript// Agent架构设计
interface TopicSelectionAgent {
  // 1. 热点采集Agent
  fetchHotTopics(): Promise<HotTopic[]>;
  
  // 2. 相关性评估Agent
  evaluateRelevance(topic: HotTopic): Promise<RelevanceScore>;
  
  // 3. 选题规划Agent
  generateOutline(topic: HotTopic): Promise<ContentOutline>;
  
  // 4. 评分Agent
  scoreOutline(outline: ContentOutline): Promise<AIScore>;
  
  // 5. 人工审核Agent (HITL)
  requestHumanReview(outline: ContentOutline): Promise<ReviewDecision>;
}

// 工作流编排
class TopicSelectionWorkflow {
  async execute() {
    // Step 1: 获取热点
    const topics = await this.fetchAgent.fetchHotTopics();
    
    // Step 2: 批量评估相关性（并发）
    const relevantTopics = await Promise.all(
      topics.map(t => this.evaluateAgent.evaluate(t))
    ).then(results => results.filter(r => r.score >= 70));
    
    // Step 3: 生成选题大纲（Top 5）
    const outlines = await Promise.all(
      relevantTopics.slice(0, 5).map(t => this.planAgent.generate(t))
    );
    
    // Step 4: AI评分
    const scoredOutlines = await Promise.all(
      outlines.map(o => this.scoreAgent.score(o))
    );
    
    // Step 5: 保存到飞书待审核
    await this.saveToLark(scoredOutlines);
    
    // Step 6: 发送Telegram通知
    await this.notifyViaViaTelegram();
  }
}

📚 学习路径建议
阶段1：理解核心概念（1-2天）

克隆LangChain Social Media Agent，运行Demo
阅读其Prompt设计（prompts/index.ts）
理解其工作流状态机设计

阶段2：N8N集成实践（3-5天）

研究N8N AI Content Automation项目
在N8N中复现简化版工作流
测试热点抓取 → 相关性判断 → 选题生成

阶段3：Prompt工程优化（持续）

参考GenAI Agents的Plan-Execute模式
收集小红书高赞案例作为Few-shot Examples
迭代优化评分体系

阶段4：系统集成（1周）

将选题模块集成到你的v2.0文档架构中
实现飞书存储和Telegram通知
部署测试


🔑 关键技术点总结
技术点推荐来源说明Agent编排LangChain Social Media AgentLangGraph状态机设计N8N工作流N8N Content Automation节点设计、错误处理Prompt工程LangChain Prompts业务上下文、Few-shot、结构化指令HITL流程Agent Inbox人工审核UI和交互设计多Agent协作GenAI AgentsPlanning + Execution模式评分体系自行设计参考你文档中的100分制

⚡ 快速启动示例
bash# 1. 克隆LangChain Social Media Agent
git clone https://github.com/langchain-ai/social-media-agent.git
cd social-media-agent
yarn install

# 2. 配置环境变量
cp .env.quickstart.example .env
# 填入：ANTHROPIC_API_KEY, LANGSMITH_API_KEY, FIRECRAWL_API_KEY

# 3. 启动服务
yarn langgraph:in_mem:up

# 4. 测试生成帖子
yarn generate_post

# 5. 查看Agent Inbox（可选）
# 访问 https://dev.agentinbox.ai/
# 添加本地Graph: http://localhost:54367
希望这些项目能为你的小红书自动发布工具提供灵感！🚀按照以上信息 借鉴各种项目的思路和路线，你来帮我设计一个小红书上面用的，自动选题agent14:48综合多个项目经验，架构了小红书自动选题系统方案。用户要我基于之前搜索的信息，借鉴各种项目的思路，设计一个小红书自动选题Agent。
让我综合之前的信息：

用户的项目是小红书自动发布工具v2.0
使用N8N作为工作流编排工具
使用Claude作为主力LLM
已有飞书多维表格作为数据存储
有Telegram通知
目标是AI自动化和工作流优化领域

参考的项目：

LangChain Social Media Agent - 完整的内容生成流程，HITL，可定制化
N8N AI Content Automation - 端到端自动化，模块化设计
GenAI Agents - Plan-Execute模式，多Agent协作
MediaCrawler - 热点抓取
DailyHotApi - 热榜API

我需要设计一个完整的、可实施的自动选题Agent系统，包括：

系统架构
技术栈
核心模块设计
N8N工作流设计
Prompt设计
数据模型
评分体系
实施步骤

让我设计一个详细的方案。好的！基于你的小红书自动发布工具v2.0项目，我来设计一个完整的自动选题Agent系统。

🎯 小红书自动选题Agent - 完整设计方案
📋 目录

系统架构
技术栈选型
核心模块设计
N8N工作流设计
Prompt工程设计
数据模型设计
评分体系设计
实施路线图


1. 系统架构
1.1 整体架构图
┌─────────────────────────────────────────────────────────────────┐
│                       自动选题Agent系统                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        输入层 (Input Layer)                       │
├─────────────────────────────────────────────────────────────────┤
│  • 小红书热榜 (DailyHotApi)                                        │
│  • 微博热搜 (MediaCrawler)                                         │
│  • 抖音热点 (MediaCrawler)                                         │
│  • 用户自定义关键词 (飞书Config表)                                  │
│  • 行业RSS订阅 (N8N RSS Trigger)                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      处理层 (Processing Layer)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent 1:     │  │ Agent 2:     │  │ Agent 3:     │          │
│  │ 热点采集     │→ │ 相关性评估   │→ │ 选题规划     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│          │                 │                 │                    │
│          ▼                 ▼                 ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent 4:     │  │ Agent 5:     │  │ Agent 6:     │          │
│  │ 内容大纲生成 │→ │ AI评分       │→ │ 优先级排序   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      决策层 (Decision Layer)                      │
├─────────────────────────────────────────────────────────────────┤
│  • 自动通过 (score≥85)  → 直接进入创作队列                         │
│  • 人工审核 (70≤score<85) → 推送Telegram审核                      │
│  • 自动拒绝 (score<70)  → 归档并记录原因                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      存储层 (Storage Layer)                       │
├─────────────────────────────────────────────────────────────────┤
│  • 飞书多维表格 (topic_candidates)                                │
│  • 飞书多维表格 (topic_history) - 去重                            │
│  • 飞书多维表格 (content_records) - 关联                          │
└─────────────────────────────────────────────────────────────────┘
1.2 Agent协作模式
采用Plan-and-Execute + Multi-Agent混合模式：
Planner Agent (规划者)
    ↓
Executor Agents (执行者们)
    ├─ Collector Agent (采集)
    ├─ Filter Agent (过滤)
    ├─ Analyzer Agent (分析)
    ├─ Generator Agent (生成)
    └─ Scorer Agent (评分)
    ↓
Reviewer Agent (审核者) - HITL

2. 技术栈选型
2.1 核心技术栈
yaml# 工作流编排
orchestration: N8N (self-hosted)

# LLM服务
llm:
  primary: Claude Sonnet 4.5 (选题规划、内容大纲)
  secondary: Claude Haiku 4.5 (快速评估、分类)
  
# 数据抓取
crawling:
  - DailyHotApi (小红书/微博/抖音热榜)
  - MediaCrawler (深度抓取)
  - FireCrawl (网页内容提取)

# 数据存储
storage:
  - 飞书多维表格 (主数据库)
  - Redis (缓存层，去重)

# 通知渠道
notification:
  - Telegram Bot (审核通知)
  - 飞书机器人 (备选)

# 部署环境
deployment:
  - Docker (N8N容器)
  - 阿里云/腾讯云 ECS (2核4G)
2.2 关键技术决策
决策点方案理由LLM主力Claude Sonnet 4.5上下文长、推理强、成本适中热点源DailyHotApi + MediaCrawler免费+可靠，覆盖多平台缓存策略Redis 24h TTL避免重复评估相同热点评分模型100分六维度评分与v2.0文档统一，可解释性强人工介入score 70-85区间平衡自动化率和质量

3. 核心模块设计
3.1 模块架构
typescript// ============ 模块1: 热点采集Agent ============
interface TopicCollectorAgent {
  // 采集配置
  config: {
    sources: ['xiaohongshu', 'weibo', 'douyin', 'rss'];
    frequency: '2-4小时';
    batchSize: 20; // 每次采集Top 20
  };
  
  // 核心方法
  fetchHotTopics(): Promise<RawTopic[]>;
  deduplicateTopics(topics: RawTopic[]): Promise<RawTopic[]>;
  enrichTopicData(topic: RawTopic): Promise<EnrichedTopic>;
}

// 数据结构
interface RawTopic {
  id: string;
  title: string;
  source: 'xiaohongshu' | 'weibo' | 'douyin';
  rank: number;
  heat_score: number; // 平台热度值
  url?: string;
  collected_at: string;
}

interface EnrichedTopic extends RawTopic {
  keywords: string[]; // 提取的关键词
  category: string; // 自动分类
  related_topics: string[]; // 相关话题
  metadata: {
    views?: number;
    likes?: number;
    comments?: number;
  };
}

// ============ 模块2: 相关性评估Agent ============
interface RelevanceEvaluatorAgent {
  // 业务上下文（从飞书config读取）
  businessContext: {
    contentDirections: string[];
    targetAudience: string[];
    keywords: string[];
    excludeKeywords: string[];
  };
  
  // 核心方法
  evaluateRelevance(topic: EnrichedTopic): Promise<RelevanceScore>;
  batchEvaluate(topics: EnrichedTopic[]): Promise<RelevanceScore[]>;
}

interface RelevanceScore {
  topic_id: string;
  scores: {
    direction_match: number; // 内容方向匹配度 (0-100)
    audience_fit: number; // 受众匹配度 (0-100)
    keyword_relevance: number; // 关键词相关性 (0-100)
    trend_potential: number; // 趋势潜力 (0-100)
  };
  total_score: number; // 加权总分
  reasoning: string; // 评分理由
  content_angle: string; // 建议的内容角度
  is_relevant: boolean; // score >= 70
}

// ============ 模块3: 选题规划Agent ============
interface TopicPlannerAgent {
  // 生成选题大纲
  generateOutline(topic: EnrichedTopic, relevance: RelevanceScore): Promise<TopicOutline>;
  
  // 生成多个标题备选
  generateTitles(outline: TopicOutline): Promise<string[]>;
  
  // 预测互动点
  predictEngagement(outline: TopicOutline): Promise<EngagementPrediction>;
}

interface TopicOutline {
  topic_id: string;
  titles: Array<{
    text: string;
    style: '悬念式' | '数字式' | '疑问式' | '对比式';
    score: number; // 标题吸引力评分
  }>;
  structure: {
    opening: string; // 开头钩子
    key_points: string[]; // 3-5个核心要点
    closing: string; // 结尾CTA
  };
  hashtags: string[]; // 话题标签
  content_length: number; // 预估字数
  unique_angle: string; // 差异化角度
  value_proposition: string; // 价值主张
}

interface EngagementPrediction {
  predicted_interactions: {
    comments: number;
    likes: number;
    collects: number;
    shares: number;
  };
  engagement_hooks: string[]; // 互动钩子
  cta_suggestions: string[]; // CTA建议
}

// ============ 模块4: 内容大纲生成Agent ============
interface ContentOutlineAgent {
  // 生成完整内容大纲
  generateFullOutline(plan: TopicOutline): Promise<ContentOutline>;
  
  // 验证大纲质量
  validateOutline(outline: ContentOutline): Promise<ValidationResult>;
}

interface ContentOutline {
  outline_id: string;
  topic_id: string;
  
  // 内容结构
  title: string; // 最终标题
  subtitle?: string; // 副标题
  
  sections: Array<{
    section_type: 'opening' | 'body' | 'closing';
    content: string;
    word_count: number;
    key_messages: string[];
  }>;
  
  // 视觉元素
  visual_elements: {
    cover_image_keywords: string[];
    inline_images: number; // 建议配图数量
    emoji_suggestions: string[];
  };
  
  // SEO优化
  seo: {
    primary_keywords: string[];
    secondary_keywords: string[];
    suggested_hashtags: string[];
  };
  
  // 质量指标
  quality_metrics: {
    readability_score: number;
    value_density: number;
    engagement_potential: number;
  };
}

// ============ 模块5: AI评分Agent ============
interface ScoringAgent {
  // 100分六维度评分
  scoreOutline(outline: ContentOutline): Promise<AIScore>;
  
  // 批量评分
  batchScore(outlines: ContentOutline[]): Promise<AIScore[]>;
}

interface AIScore {
  outline_id: string;
  
  // 六维度评分（与v2.0文档一致）
  dimensions: {
    click_power: number;      // 点击力 (30%)
    content_quality: number;  // 内容力 (25%)
    value_sense: number;      // 价值感 (20%)
    interaction_design: number; // 互动设计 (10%)
    platform_fit: number;     // 平台适配 (15%)
  };
  
  total_score: number; // 加权总分
  
  // 详细评价
  evaluation: {
    strengths: string[];
    weaknesses: string[];
    improvement_suggestions: string[];
  };
  
  // 决策建议
  decision: 'auto_approve' | 'human_review' | 'auto_reject';
  confidence: number; // 决策置信度
}

// ============ 模块6: 优先级排序Agent ============
interface PriorityRankingAgent {
  // 综合排序
  rankTopics(scoredOutlines: ScoredOutline[]): Promise<RankedTopic[]>;
  
  // 时效性调整
  adjustForTimeliness(rankings: RankedTopic[]): Promise<RankedTopic[]>;
}

interface ScoredOutline {
  outline: ContentOutline;
  ai_score: AIScore;
  relevance_score: RelevanceScore;
  collected_at: string;
}

interface RankedTopic extends ScoredOutline {
  final_priority: number; // 最终优先级分数
  urgency_level: 'urgent' | 'normal' | 'low';
  recommended_publish_time: string;
  expiry_date: string; // 时效性截止日期
}
3.2 状态机设计
typescript// 选题状态流转
enum TopicStatus {
  COLLECTED = 'COLLECTED',           // 已采集
  EVALUATING = 'EVALUATING',         // 评估中
  RELEVANT = 'RELEVANT',             // 相关（score≥70）
  IRRELEVANT = 'IRRELEVANT',         // 不相关（score<70）
  OUTLINE_GENERATED = 'OUTLINE_GENERATED', // 大纲已生成
  AI_SCORED = 'AI_SCORED',           // 已评分
  PENDING_REVIEW = 'PENDING_REVIEW', // 待人工审核（70≤score<85）
  APPROVED = 'APPROVED',             // 已批准（score≥85或人工通过）
  REJECTED = 'REJECTED',             // 已拒绝
  IN_CONTENT_QUEUE = 'IN_CONTENT_QUEUE', // 已加入创作队列
  EXPIRED = 'EXPIRED'                // 已过期
}

// 状态转换规则
const transitions = {
  COLLECTED: ['EVALUATING'],
  EVALUATING: ['RELEVANT', 'IRRELEVANT'],
  IRRELEVANT: ['REJECTED'],
  RELEVANT: ['OUTLINE_GENERATED'],
  OUTLINE_GENERATED: ['AI_SCORED'],
  AI_SCORED: ['APPROVED', 'PENDING_REVIEW', 'REJECTED'],
  PENDING_REVIEW: ['APPROVED', 'REJECTED'],
  APPROVED: ['IN_CONTENT_QUEUE'],
  IN_CONTENT_QUEUE: [], // 终态
  REJECTED: [], // 终态
  EXPIRED: [] // 终态
};

4. N8N工作流设计
4.1 主工作流：topic_selection_main
json{
  "name": "topic_selection_main",
  "nodes": [
    {
      "id": "schedule_trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "name": "每2小时触发",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 2
            }
          ]
        }
      },
      "position": [250, 300]
    },
    {
      "id": "fetch_config",
      "type": "n8n-nodes-base.code",
      "name": "读取飞书配置",
      "parameters": {
        "jsCode": "// 从飞书config表读取业务配置\nconst config = await fetch('飞书API');\nreturn { config };"
      },
      "position": [450, 300]
    },
    {
      "id": "call_collector_subflow",
      "type": "n8n-nodes-base.executeWorkflow",
      "name": "调用采集子流程",
      "parameters": {
        "workflowId": "sub_topic_collector",
        "source": "database"
      },
      "position": [650, 300]
    },
    {
      "id": "call_evaluator_subflow",
      "type": "n8n-nodes-base.executeWorkflow",
      "name": "调用评估子流程",
      "parameters": {
        "workflowId": "sub_relevance_evaluator"
      },
      "position": [850, 300]
    },
    {
      "id": "filter_relevant",
      "type": "n8n-nodes-base.filter",
      "name": "筛选相关选题",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.relevance_score.total_score}}",
              "operation": "largerEqual",
              "value2": 70
            }
          ]
        }
      },
      "position": [1050, 300]
    },
    {
      "id": "call_planner_subflow",
      "type": "n8n-nodes-base.executeWorkflow",
      "name": "调用规划子流程",
      "parameters": {
        "workflowId": "sub_topic_planner"
      },
      "position": [1250, 300]
    },
    {
      "id": "call_outliner_subflow",
      "type": "n8n-nodes-base.executeWorkflow",
      "name": "调用大纲生成子流程",
      "parameters": {
        "workflowId": "sub_content_outliner"
      },
      "position": [1450, 300]
    },
    {
      "id": "call_scorer_subflow",
      "type": "n8n-nodes-base.executeWorkflow",
      "name": "调用评分子流程",
      "parameters": {
        "workflowId": "sub_ai_scorer"
      },
      "position": [1650, 300]
    },
    {
      "id": "decision_branch",
      "type": "n8n-nodes-base.switch",
      "name": "决策分支",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.ai_score.total_score}}",
              "operation": "largerEqual",
              "value2": 85,
              "output": 0 // 自动通过
            },
            {
              "value1": "={{$json.ai_score.total_score}}",
              "operation": "largerEqual",
              "value2": 70,
              "output": 1 // 人工审核
            }
          ]
        },
        "fallbackOutput": 2 // 自动拒绝
      },
      "position": [1850, 300]
    },
    {
      "id": "auto_approve",
      "type": "n8n-nodes-base.code",
      "name": "自动通过",
      "parameters": {
        "jsCode": "// 更新状态为APPROVED\n// 加入content_records表\nreturn { status: 'APPROVED', ...item };"
      },
      "position": [2050, 200]
    },
    {
      "id": "human_review",
      "type": "n8n-nodes-base.code",
      "name": "推送人工审核",
      "parameters": {
        "jsCode": "// 推送到Telegram\n// 更新状态为PENDING_REVIEW\nreturn { status: 'PENDING_REVIEW', ...item };"
      },
      "position": [2050, 300]
    },
    {
      "id": "auto_reject",
      "type": "n8n-nodes-base.code",
      "name": "自动拒绝",
      "parameters": {
        "jsCode": "// 更新状态为REJECTED\n// 记录拒绝原因\nreturn { status: 'REJECTED', ...item };"
      },
      "position": [2050, 400]
    },
    {
      "id": "save_to_lark",
      "type": "n8n-nodes-base.httpRequest",
      "name": "保存到飞书",
      "parameters": {
        "url": "飞书API",
        "method": "POST"
      },
      "position": [2250, 300]
    },
    {
      "id": "send_notification",
      "type": "n8n-nodes-base.telegram",
      "name": "发送Telegram通知",
      "parameters": {
        "chatId": "{{$env.TELEGRAM_CHAT_ID}}",
        "text": "✨ 新选题待审核：\n{{$json.outline.title}}\n评分：{{$json.ai_score.total_score}}\n\n👉 [点击查看详情](链接)"
      },
      "position": [2450, 300]
    }
  ],
  "connections": {
    "schedule_trigger": {
      "main": [[{ "node": "fetch_config", "type": "main", "index": 0 }]]
    },
    "fetch_config": {
      "main": [[{ "node": "call_collector_subflow", "type": "main", "index": 0 }]]
    }
    // ... 其他连接
  }
}
4.2 子工作流设计
子流程1：sub_topic_collector（热点采集）
javascript// 伪代码
async function topicCollectorWorkflow() {
  // 1. 并发调用多个热榜API
  const [xhsTopics, weiboTopics, douyinTopics] = await Promise.all([
    fetchXHSHotTopics(),  // DailyHotApi
    fetchWeiboHotTopics(), // DailyHotApi
    fetchDouyinHotTopics() // DailyHotApi
  ]);
  
  // 2. 标准化数据格式
  const normalizedTopics = [
    ...normalizeTopics(xhsTopics, 'xiaohongshu'),
    ...normalizeTopics(weiboTopics, 'weibo'),
    ...normalizeTopics(douyinTopics, 'douyin')
  ];
  
  // 3. 去重（基于标题相似度）
  const uniqueTopics = await deduplicateTopics(normalizedTopics);
  
  // 4. 缓存检查（Redis）
  const newTopics = await filterCachedTopics(uniqueTopics);
  
  // 5. 关键词提取
  const enrichedTopics = await Promise.all(
    newTopics.map(async (topic) => ({
      ...topic,
      keywords: await extractKeywords(topic.title),
      category: await classifyTopic(topic.title)
    }))
  );
  
  // 6. 保存到飞书topic_history表（记录所有抓取历史）
  await saveToLarkHistory(enrichedTopics);
  
  return enrichedTopics;
}
子流程2：sub_relevance_evaluator（相关性评估）
javascriptasync function relevanceEvaluatorWorkflow(topics) {
  // 1. 读取业务配置
  const config = await fetchBusinessConfig();
  
  // 2. 批量评估（使用Claude Haiku快速评估）
  const evaluations = await Promise.all(
    topics.map(async (topic) => {
      const prompt = buildRelevancePrompt(topic, config);
      const result = await claudeHaiku.generate(prompt);
      return parseRelevanceScore(result);
    })
  );
  
  // 3. 合并结果
  const evaluatedTopics = topics.map((topic, i) => ({
    ...topic,
    relevance_score: evaluations[i],
    is_relevant: evaluations[i].total_score >= 70
  }));
  
  return evaluatedTopics;
}
子流程3：sub_topic_planner（选题规划）
javascriptasync function topicPlannerWorkflow(relevantTopics) {
  // 1. 生成选题大纲
  const outlines = await Promise.all(
    relevantTopics.map(async (topic) => {
      const prompt = buildPlanningPrompt(topic);
      const result = await claudeSonnet.generate(prompt);
      return parseTopicOutline(result);
    })
  );
  
  // 2. 生成多个标题备选
  const outlinesWithTitles = await Promise.all(
    outlines.map(async (outline) => {
      const titles = await generateTitles(outline);
      return { ...outline, titles };
    })
  );
  
  return outlinesWithTitles;
}
子流程4：sub_content_outliner（内容大纲生成）
javascriptasync function contentOutlinerWorkflow(topicOutlines) {
  // 1. 生成完整内容大纲
  const contentOutlines = await Promise.all(
    topicOutlines.map(async (topicOutline) => {
      const prompt = buildOutlinePrompt(topicOutline);
      const result = await claudeSonnet.generate(prompt);
      return parseContentOutline(result);
    })
  );
  
  // 2. 验证大纲质量
  const validatedOutlines = await Promise.all(
    contentOutlines.map(async (outline) => {
      const validation = await validateOutline(outline);
      return { ...outline, validation };
    })
  );
  
  // 3. 过滤不合格大纲
  const qualifiedOutlines = validatedOutlines.filter(
    o => o.validation.is_valid
  );
  
  return qualifiedOutlines;
}
子流程5：sub_ai_scorer（AI评分）
javascriptasync function aiScorerWorkflow(contentOutlines) {
  // 1. 100分六维度评分
  const scores = await Promise.all(
    contentOutlines.map(async (outline) => {
      const prompt = buildScoringPrompt(outline);
      const result = await claudeSonnet.generate(prompt);
      return parseAIScore(result);
    })
  );
  
  // 2. 合并评分结果
  const scoredOutlines = contentOutlines.map((outline, i) => ({
    outline,
    ai_score: scores[i],
    decision: determineDecision(scores[i].total_score)
  }));
  
  // 3. 优先级排序
  const rankedTopics = rankByPriority(scoredOutlines);
  
  return rankedTopics;
}

5. Prompt工程设计
5.1 业务上下文Prompt（可配置）
python# 存储在飞书config表，支持动态修改
BUSINESS_CONTEXT = """
# 业务上下文配置

## 内容定位
你是一个专注于AI自动化和工作流优化的小红书创作者。

## 主要内容方向
1. **AI Agent开发**：使用Claude、GPT等大模型开发实用AI应用
2. **N8N工作流自动化**：无代码自动化工具的深度教程
3. **小红书运营技巧**：数据驱动的内容创作和运营策略
4. **效率工具推荐**：提升个人和团队生产力的AI工具

## 目标受众
- **主要受众**：25-40岁，对AI技术感兴趣的职场人士
- **次要受众**：技术爱好者、自由职业者、创业者
- **用户画像**：
  * 有一定技术基础，但不是专业开发者
  * 追求效率和自动化
  * 愿意尝试新工具和新技术
  * 有实际业务需求

## 核心价值主张
通过AI自动化工具，帮助用户：
- 节省80%的重复劳动时间
- 零代码实现复杂自动化流程
- 快速上手AI应用开发
- 建立个人知识管理系统

## 内容风格
- **语言风格**：口语化、接地气、避免过度技术术语
- **情感基调**：友好、实用、有温度
- **内容密度**：高价值密度，干货为主，避免水分
- **互动性**：强调用户参与，鼓励评论和收藏

## 关键词清单（优先关注）
AI, 自动化, 工作流, N8N, Claude, ChatGPT, Zapier, 效率工具, 
生产力, 小红书运营, 内容创作, 数据分析, Python, API, 
AI Agent, LangChain, 知识管理, 笔记工具, Notion

## 排除关键词（不相关）
游戏, 娱乐八卦, 美妆, 时尚穿搭, 美食探店, 旅游攻略, 
影视剧, 明星, 电商带货, 直播, 短视频拍摄技巧
（注：除非这些话题与AI自动化直接相关）

## 竞品分析
- **竞争优势**：深度技术+实战案例+手把手教程
- **差异化定位**：不只讲工具，更讲工作流思维
- **避免同质化**：不做简单的工具测评，强调实际落地

## 内容禁忌
- ❌ 标题党和夸大宣传
- ❌ 复制竞品内容
- ❌ 纯理论无实操
- ❌ 过度技术细节（代码超过3屏）
- ❌ 商业广告痕迹过重
"""
5.2 相关性评估Prompt
pythonRELEVANCE_EVALUATION_PROMPT = """
# 任务：评估热点话题与业务的相关性

## 业务上下文
{BUSINESS_CONTEXT}

## 热点信息
- **标题**：{topic_title}
- **来源**：{topic_source}
- **热度**：{topic_heat}
- **关键词**：{topic_keywords}
- **分类**：{topic_category}

## 评估维度（总分100）

### 1. 内容方向匹配度 (40分)
评估该热点是否属于我们的4大内容方向：
- AI Agent开发
- N8N工作流自动化
- 小红书运营技巧
- 效率工具推荐

评分标准：
- 90-100分：完全匹配，核心话题
- 70-89分：高度相关，可以深入展开
- 50-69分：部分相关，需要转换角度
- 30-49分：弱相关，需要大幅改造
- 0-29分：基本无关

### 2. 目标受众匹配度 (30分)
评估该热点对目标受众的吸引力：
- 是否是目标受众关心的话题？
- 是否能引起目标受众的共鸣？
- 是否能解决目标受众的实际问题？

### 3. 关键词相关性 (20分)
评估热点关键词与我们的关键词清单的重合度：
- 包含核心关键词（AI、自动化等）
- 不包含排除关键词
- 关键词语义相关性

### 4. 趋势潜力 (10分)
评估该热点的持续性和传播潜力：
- 是否是长期趋势？（非一次性热点）
- 是否有持续讨论价值？
- 是否可能引发二次传播？

## 输出格式（严格JSON）
{{
  "scores": {{
    "direction_match": 85,
    "audience_fit": 90,
    "keyword_relevance": 75,
    "trend_potential": 80
  }},
  "total_score": 83,
  "is_relevant": true,
  "reasoning": "该热点关于AI自动化工具的应用，完全符合我们的内容方向，目标受众对此有强烈需求...",
  "content_angle": "可以从以下角度切入：1) 工具实战教程；2) 与传统方法对比；3) 效率提升案例",
  "potential_issues": ["技术门槛可能偏高，需要降低难度"],
  "recommended_action": "strongly_recommend" // 或 "recommend" 或 "consider" 或 "skip"
}}

## 重要提示
- 评分要客观，避免所有话题都高分
- reasoning必须具体，说明为什么相关/不相关
- content_angle要可操作，不要泛泛而谈
- 如果score<70，必须在potential_issues中说明原因
"""
5.3 选题规划Prompt
pythonTOPIC_PLANNING_PROMPT = """
# 任务：基于热点生成小红书选题大纲

## 业务上下文
{BUSINESS_CONTEXT}

## 热点信息
{topic_info}

## 相关性评估
{relevance_score}

## 任务目标
生成一个适合小红书平台的内容选题大纲，包括：
1. 3个风格各异的标题备选
2. 完整的内容结构规划
3. 差异化角度和价值主张

## 输出格式（严格JSON）

{{
  "titles": [
    {{
      "text": "3分钟搭建AI自动回复机器人｜告别重复劳动",
      "style": "数字式+利益驱动",
      "hook": "3分钟、告别重复劳动",
      "target_audience": "职场人士、客服人员",
      "estimated_ctr": 8.5,
      "reasoning": "数字具体化降低门槛，利益点明确"
    }},
    {{
      "text": "老板问我为什么下班这么早？因为我用了这个工具...",
      "style": "故事式+悬念",
      "hook": "老板疑问、工具悬念",
      "target_audience": "职场打工人",
      "estimated_ctr": 9.2,
      "reasoning": "引发好奇心，代入感强"
    }},
    {{
      "text": "手动回复 VS AI自动回复：实测效率差距惊人",
      "style": "对比式+数据",
      "hook": "对比、实测、效率差距",
      "target_audience": "追求效率的用户",
      "estimated_ctr": 7.8,
      "reasoning": "对比鲜明，结果导向"
    }}
  ],
  
  "content_structure": {{
    "opening": {{
      "type": "痛点引入",
      "content": "你是不是也这样：每天被各种重复性消息轰炸，客户问题一遍又一遍回答？",
      "word_count": 50,
      "goal": "引发共鸣，建立场景"
    }},
    
    "key_points": [
      {{
        "point": "为什么需要AI自动回复？",
        "content": "数据说话：传统客服平均响应时间2分钟，AI<5秒；人工处理成本50元/小时，AI几乎为0",
        "word_count": 150,
        "value": "建立必要性，用数据说服"
      }},
      {{
        "point": "手把手教你搭建（核心干货）",
        "content": "3步完成：1)注册工具 2)配置规则 3)测试上线。每步都有截图，小白也能跟着做",
        "word_count": 300,
        "value": "实操教程，降低门槛"
      }},
      {{
        "point": "实际效果展示",
        "content": "我的真实使用数据：从每天回复200条消息→自动化处理80%→节省4小时/天",
        "word_count": 150,
        "value": "案例证明，增强信任"
      }}
    ],
    
    "closing": {{
      "type": "CTA+互动",
      "content": "评论区回复【AI客服】，我发你详细配置文档｜觉得有用记得收藏哦～",
      "word_count": 50,
      "goal": "引导互动，增加收藏"
    }}
  }},
  
  "visual_elements": {{
    "cover_image_keywords": ["对比图", "效率提升", "聊天界面截图"],
    "inline_images_count": 5,
    "image_suggestions": [
      "痛点场景：堆积的消息通知",
      "工具界面：简洁的配置页面",
      "效果对比：处理前VS处理后",
      "数据图表：时间节省统计",
      "成功案例：用户反馈截图"
    ],
    "emoji_usage": "适度使用，每2-3段1个，增强情感表达"
  }},
  
  "hashtags": [
    "#AI自动化", "#效率工具", "#职场技能",
    "#工作流优化", "#客服自动化"
  ],
  
  "unique_angle": "不讲大道理，直接上手实操；不只讲工具，更讲背后的效率思维",
  
  "value_proposition": "零门槛学会AI自动化，每天节省4小时，让重复劳动成为过去式",
  
  "differentiation": {{
    "vs_competitors": "市面上大多讲工具功能，我们讲实际场景和ROI计算",
    "unique_selling_point": "手把手教程+真实数据+可复制的配置模板"
  }},
  
  "engagement_design": {{
    "comment_hooks": [
      "你每天花多少时间回复消息？评论区聊聊",
      "还有哪些重复劳动想自动化？我来出教程"
    ],
    "cta": "评论区回复【AI客服】领取配置文档",
    "save_hook": "收藏=学会，详细步骤随时查看"
  }},
  
  "estimated_metrics": {{
    "content_length": 800,
    "reading_time": "2-3分钟",
    "target_engagement_rate": "8-12%",
    "predicted_save_rate": "高（实用教程类）"
  }}
}}

## 关键要求
1. **标题必须吸引人**：前3秒决定是否点击
2. **开头必须抓人**：前2屏必须让人看下去
3. **干货必须实用**：可操作、可复制、有价值
4. **结尾必须有钩子**：引导互动、促进收藏
5. **差异化必须明显**：与竞品内容有明显区别

## 避免踩坑
- ❌ 标题过于平淡："AI自动回复工具介绍"
- ❌ 内容过于理论："AI技术的发展历程..."
- ❌ 没有互动设计：文章结尾就结束了
- ❌ 缺乏实证数据：全是"可能"、"也许"
"""
5.4 内容大纲生成Prompt
pythonCONTENT_OUTLINE_PROMPT = """
# 任务：生成完整的内容创作大纲

## 输入
- 选题规划：{topic_plan}
- 业务上下文：{business_context}

## 任务
将选题规划扩展为可直接用于内容创作的详细大纲

## 输出格式（严格JSON）

{{
  "meta": {{
    "outline_id": "uuid",
    "topic_id": "uuid",
    "created_at": "2024-12-11T10:00:00Z",
    "estimated_creation_time": "60分钟"
  }},
  
  "title": "老板问我为什么下班这么早？因为我用了这个AI工具...",
  
  "subtitle": "3分钟搭建自动回复系统，每天节省4小时",
  
  "sections": [
    {{
      "section_id": 1,
      "section_type": "opening",
      "section_title": "痛点场景描写",
      "content": "下午6点，办公室还灯火通明。小李盯着电脑，机械地复制粘贴着回复模板。\"这已经是今天第200条消息了...\" 他叹了口气。\\n\\n你是不是也有同样的痛苦？每天被各种重复性消息轰炸：\\n• 客户问同样的问题\\n• 咨询同样的价格\\n• 索要同样的资料\\n\\n直到我发现了这个AI自动回复工具，一切都变了...",
      "word_count": 120,
      "key_messages": [
        "建立场景代入感",
        "列举3个痛点",
        "制造悬念"
      ],
      "tone": "故事化、共鸣式",
      "purpose": "抓住读者注意力，建立问题意识"
    }},
    
    {{
      "section_id": 2,
      "section_type": "body",
      "section_title": "为什么需要AI自动回复？",
      "content": "先看一组真实数据：\\n\\n📊 传统人工回复：\\n• 平均响应时间：2-5分钟\\n• 处理成本：50元/小时\\n• 错误率：5-10%（疲劳导致）\\n\\n🤖 AI自动回复：\\n• 平均响应时间：<5秒\\n• 处理成本：几乎为0\\n• 错误率：<1%\\n\\n更重要的是，AI不会疲劳，不会请假，不会情绪化。它能7×24小时待命，永远保持最佳状态。",
      "word_count": 150,
      "key_messages": [
        "数据对比说服",
        "成本效益分析",
        "AI优势总结"
      ],
      "visual_aids": [
        "数据对比表格",
        "成本计算示意图"
      ],
      "tone": "数据驱动、理性分析"
    }},
    
    {{
      "section_id": 3,
      "section_type": "body",
      "section_title": "手把手教你搭建（核心教程）",
      "content": "别担心技术门槛，我把步骤拆得很细，跟着做就行👇\\n\\n第一步：注册账号（1分钟）\\n• 访问xxx平台官网\\n• 邮箱注册，免费额度足够\\n• 【截图1：注册页面】\\n\\n第二步：配置回复规则（2分钟）\\n• 进入「自动回复」设置\\n• 添加常见问题模板\\n• 设置触发关键词\\n• 【截图2：配置界面】\\n• 【截图3：规则示例】\\n\\n第三步：测试上线（1分钟）\\n• 发送测试消息验证\\n• 调整回复话术\\n• 正式启用\\n• 【截图4：测试效果】\\n\\n⚠️ 注意事项：\\n1. 初期建议只自动化最常见的10个问题\\n2. 保留人工接管入口\\n3. 每周review一次效果",
      "word_count": 300,
      "key_messages": [
        "降低技术门槛",
        "分步骤详细说明",
        "配图辅助理解",
        "补充注意事项"
      ],
      "visual_aids": [
        "4张关键步骤截图",
        "配置模板示例",
        "注意事项清单"
      ],
      "tone": "手把手教学、友好亲切"
    }},
    
    {{
      "section_id": 4,
      "section_type": "body",
      "section_title": "实际效果展示",
      "content": "说了这么多，到底有没有用？直接看我的真实数据📈\\n\\n使用前：\\n• 每天回复消息：200条\\n• 耗时：6-8小时\\n• 效率：低，经常遗漏\\n\\n使用后（30天）：\\n• AI自动处理：160条（80%）\\n• 人工处理：40条（20%）\\n• 节省时间：4-5小时/天\\n• 响应速度：提升10倍\\n\\n【数据图表：30天效果对比】\\n\\n更惊喜的是，客户满意度还提升了！因为响应快，回复标准，很多客户都夸赞专业💯",
      "word_count": 150,
      "key_messages": [
        "真实数据验证",
        "前后对比明显",
        "额外收益"
      ],
      "visual_aids": [
        "效果对比图表",
        "客户好评截图"
      ],
      "tone": "案例分享、结果导向"
    }},
    
    {{
      "section_id": 5,
      "section_type": "closing",
      "section_title": "行动号召",
      "content": "如果你也想告别重复劳动，每天早下班4小时，现在就可以开始行动！\\n\\n💡 评论区回复【AI客服】，我发你：\\n✅ 详细配置文档（PDF）\\n✅ 常用问题模板库\\n✅ 进阶优化指南\\n\\n觉得有用的话，记得点赞收藏哦～这样就不怕找不到啦📌\\n\\n下期想看什么自动化教程？评论区告诉我！",
      "word_count": 100,
      "key_messages": [
        "明确行动指令",
        "提供额外价值",
        "引导互动"
      ],
      "cta_design": {{
        "primary_cta": "评论区回复【AI客服】",
        "secondary_cta": "点赞收藏",
        "engagement_hook": "下期内容征集"
      }},
      "tone": "激励行动、友好互动"
    }}
  ],
  
  "seo_optimization": {{
    "primary_keywords": ["AI自动回复", "客服自动化", "效率工具"],
    "secondary_keywords": ["工作流优化", "重复劳动", "智能客服"],
    "keyword_density": "2-3%",
    "hashtag_placement": "文末集中",
    "suggested_hashtags": [
      "#AI自动化", "#效率工具", "#职场技能",
      "#客服自动化", "#工作流优化"
    ]
  }},
  
  "quality_checklist": {{
    "content_completeness": true,
    "logical_flow": true,
    "value_density": true,
    "visual_richness": true,
    "engagement_design": true,
    "readability": true
  }},
  
  "estimated_quality_metrics": {{
    "readability_score": 85,
    "value_density": 90,
    "engagement_potential": 88,
    "uniqueness": 82
  }}
}}

## 关键质量标准
1. ✅ 每个section都有明确的目标和价值
2. ✅ 逻辑流畅，循序渐进
3. ✅ 干货密度高，避免废话
4. ✅ 视觉元素丰富，易于阅读
5. ✅ 互动设计巧妙，促进参与
"""
5.5 AI评分Prompt
pythonAI_SCORING_PROMPT = """
# 任务：对内容大纲进行100分六维度评分

## 评分体系（与v2.0文档一致）

### 1. 点击力 (30分)
评估标题和开头的吸引力
- **标题吸引力** (15分)
  * 10-15分：立刻想点击，有强烈好奇心或利益驱动
  * 6-9分：比较吸引，有点击欲望
  * 0-5分：平淡无奇，不太想点击

- **开头钩子** (15分)
  * 10-15分：前2屏立刻抓住注意力，有代入感
  * 6-9分：开头还可以，但不够震撼
  * 0-5分：开头平淡，容易划走

评分要点：
- 是否有数字/对比/反差/悬念？
- 是否能引发好奇心或焦虑感？
- 是否直击用户痛点？

### 2. 内容力 (25分)
评估内容的质量和深度
- **干货密度** (10分)
  * 8-10分：全是实用信息，没有废话
  * 5-7分：有干货但不够密集
  * 0-4分：内容空洞，水分大

- **逻辑性** (8分)
  * 6-8分：结构清晰，层次分明
  * 3-5分：逻辑还可以，但不够流畅
  * 0-2分：混乱，跳跃性大

- **可操作性** (7分)
  * 5-7分：看完能立刻上手操作
  * 3-4分：需要自己摸索一下
  * 0-2分：看完还是不知道怎么做

### 3. 价值感 (20分)
评估用户能获得的价值
- **问题解决能力** (10分)
  * 8-10分：彻底解决一个痛点问题
  * 5-7分：部分解决，有一定帮助
  * 0-4分：价值不明显

- **独特性** (10分)
  * 8-10分：独家视角，市面少见
  * 5-7分：有一定差异化
  * 0-4分：同质化严重

### 4. 互动设计 (10分)
评估引导用户互动的能力
- **评论引导** (5分)
  * 4-5分：有明确的评论钩子，容易引发讨论
  * 2-3分：有互动设计但不够强
  * 0-1分：没有互动设计

- **收藏/转发动机** (5分)
  * 4-5分：实用到想收藏，有用到想分享
  * 2-3分：可能会收藏，但不一定分享
  * 0-1分：看完就走，不会有后续动作

### 5. 平台适配 (15分)
评估与小红书平台的契合度
- **小红书风格** (8分)
  * 6-8分：典型小红书语言，口语化+emoji
  * 3-5分：还算接近，但不够地道
  * 0-2分：不像小红书，像公众号文章

- **合规性** (7分)
  * 6-7分：完全合规，无违规风险
  * 3-5分：可能有轻微风险
  * 0-2分：明显违规（敏感词、引导关注等）

## 输出格式（严格JSON）

{{
  "scores": {{
    "click_power": {{
      "title_attraction": 14,
      "opening_hook": 13,
      "subtotal": 27,
      "reasoning": "标题使用对话式+悬念，开头用场景描写代入感强"
    }},
    
    "content_quality": {{
      "information_density": 9,
      "logical_flow": 7,
      "actionability": 6,
      "subtotal": 22,
      "reasoning": "干货密度高，逻辑清晰，但实操步骤可以更详细"
    }},
    
    "value_sense": {{
      "problem_solving": 9,
      "uniqueness": 8,
      "subtotal": 17,
      "reasoning": "解决明确痛点，差异化角度明显"
    }},
    
    "interaction_design": {{
      "comment_guidance": 4,
      "save_share_motivation": 5,
      "subtotal": 9,
      "reasoning": "有明确CTA，福利诱饵设计巧妙"
    }},
    
    "platform_fit": {{
      "xiaohongshu_style": 7,
      "compliance": 7,
      "subtotal": 14,
      "reasoning": "语言风格接近小红书，无明显违规"
    }}
  }},
  
  "total_score": 89,
  
  "detailed_evaluation": {{
    "strengths": [
      "标题悬念设计强，点击欲望高",
      "开头场景化，代入感强",
      "干货密度高，步骤清晰",
      "数据说服力强，真实案例"
    ],
    
    "weaknesses": [
      "实操步骤可以再详细一些",
      "缺少常见问题FAQ",
      "emoji使用可以更丰富"
    ],
    
    "improvement_suggestions": [
      "在第3部分增加视频演示或动图",
      "补充5个最常见的Q&A",
      "每段开头加一个相关emoji增强情感"
    ],
    
    "risk_assessment": {{
      "compliance_risk": "低",
      "quality_risk": "低",
      "engagement_risk": "低",
      "overall_risk": "低"
    }}
  }},
  
  "decision_recommendation": {{
    "decision": "auto_approve",
    "confidence": 0.92,
    "reasoning": "总分89，各维度均衡，无明显短板，符合自动通过标准（≥85分）",
    "next_steps": [
      "直接加入创作队列",
      "分配创作优先级：高"
    ]
  }},
  
  "comparative_analysis": {{
    "vs_average_score": "+12分（平均77分）",
    "vs_top_10_percent": "接近Top 10%水平（90+分）",
    "improvement_potential": "优化后可达92-95分"
  }}
}}

## 评分原则
1. **客观公正**：不要所有内容都打高分，严格按标准
2. **有理有据**：每个评分都要有具体理由
3. **建设性**：指出问题的同时给出改进建议
4. **全局视角**：考虑内容在整体选题库中的位置
5. **风险意识**：识别潜在的合规和质量风险
"""

6. 数据模型设计
6.1 飞书多维表格结构
表1: topic_candidates (选题候选库)
yamltable_name: topic_candidates
description: 存储所有通过相关性评估的选题候选
permissions: 创作团队可读写

fields:
  # 基础信息
  - field_name: id
    field_type: 文本
    unique: true
    description: UUID

  - field_name: created_at
    field_type: 日期
    format: YYYY-MM-DD HH:mm:ss
    auto_fill: true

  - field_name: status
    field_type: 单选
    options:
      - EVALUATING
      - RELEVANT
      - OUTLINE_GENERATED
      - AI_SCORED
      - PENDING_REVIEW
      - APPROVED
      - REJECTED
      - IN_CONTENT_QUEUE
      - EXPIRED
    default: EVALUATING

  # 热点信息
  - field_name: topic_title
    field_type: 文本
    required: true
    description: 原始热点标题

  - field_name: topic_source
    field_type: 单选
    options: [xiaohongshu, weibo, douyin, rss, manual]

  - field_name: topic_url
    field_type: URL
    description: 原始热点链接

  - field_name: topic_keywords
    field_type: 多选
    description: 提取的关键词

  - field_name: topic_category
    field_type: 单选
    options: [AI工具, 自动化, 效率优化, 运营技巧, 其他]

  # 相关性评估
  - field_name: relevance_score
    field_type: 数字
    format: 整数
    range: [0, 100]
    description: 相关性总分

  - field_name: relevance_details
    field_type: 长文本
    format: JSON
    description: 详细评分和理由

  # 选题规划
  - field_name: planned_titles
    field_type: 长文本
    format: JSON
    description: 3个标题备选

  - field_name: content_angle
    field_type: 文本
    description: 内容切入角度

  - field_name: unique_selling_point
    field_type: 文本
    description: 差异化卖点

  # 内容大纲
  - field_name: final_title
    field_type: 文本
    description: 最终确定的标题

  - field_name: content_outline
    field_type: 长文本
    format: JSON
    description: 完整内容大纲

  - field_name: estimated_length
    field_type: 数字
    description: 预估字数

  # AI评分
  - field_name: ai_score_total
    field_type: 数字
    format: 整数
    range: [0, 100]
    description: AI评分总分

  - field_name: ai_score_breakdown
    field_type: 长文本
    format: JSON
    description: 六维度详细评分

  - field_name: ai_evaluation
    field_type: 长文本
    description: AI评价和建议

  # 决策信息
  - field_name: decision
    field_type: 单选
    options: [auto_approve, human_review, auto_reject]
    description: 决策结果

  - field_name: decision_reason
    field_type: 文本
    description: 决策理由

  - field_name: reviewer
    field_type: 人员
    description: 人工审核人

  - field_name: review_time
    field_type: 日期
    description: 审核时间

  - field_name: review_comment
    field_type: 长文本
    description: 审核意见

  # 优先级
  - field_name: priority_score
    field_type: 数字
    format: 小数
    description: 综合优先级分数

  - field_name: urgency_level
    field_type: 单选
    options: [urgent, normal, low]
    default: normal

  - field_name: expiry_date
    field_type: 日期
    description: 时效性截止日期

  # 关联
  - field_name: content_record_id
    field_type: 关联
    linked_table: content_records
    description: 关联的内容记录

  # 元数据
  - field_name: workflow_run_id
    field_type: 文本
    unique: true
    description: N8N工作流执行ID

  - field_name: error_log
    field_type: 长文本
    description: 错误日志

# 视图
views:
  - view_name: 待人工审核
    filter:
      - status = PENDING_REVIEW
    sort:
      - priority_score DESC
      - created_at DESC

  - view_name: 已批准待创作
    filter:
      - status = APPROVED
      - content_record_id IS NULL
    sort:
      - urgency_level ASC
      - priority_score DESC

  - view_name: 本周采集
    filter:
      - created_at >= THIS_WEEK_START
    group_by: topic_source

  - view_name: 高分选题
    filter:
      - ai_score_total >= 85
    sort:
      - ai_score_total DESC
表2: topic_history (选题历史库)
yamltable_name: topic_history
description: 记录所有抓取的热点历史，用于去重和趋势分析
permissions: 只读（系统自动写入）

fields:
  - field_name: id
    field_type: 文本
    unique: true

  - field_name: collected_at
    field_type: 日期

  - field_name: topic_title
    field_type: 文本
    index: true

  - field_name: topic_source
    field_type: 单选

  - field_name: heat_score
    field_type: 数字
    description: 平台热度值

  - field_name: is_processed
    field_type: 复选框
    default: false
    description: 是否已处理

  - field_name: relevance_score
    field_type: 数字
    description: 相关性评分

  - field_name: final_status
    field_type: 单选
    options: [approved, rejected, skipped]

# 索引
indexes:
  - name: idx_title_collected
    fields: [topic_title, collected_at]
    type: composite

  - name: idx_source_heat
    fields: [topic_source, heat_score DESC]
表3: business_config (业务配置表)
yamltable_name: business_config
description: 存储业务规则和Prompt配置，支持热更新
permissions: 管理员可写，系统可读

fields:
  - field_name: config_key
    field_type: 文本
    unique: true
    description: 配置键名

  - field_name: config_value
    field_type: 长文本
    description: 配置值（支持JSON）

  - field_name: config_type
    field_type: 单选
    options: [prompt, rule, keyword, threshold]

  - field_name: description
    field_type: 文本
    description: 配置说明

  - field_name: is_active
    field_type: 复选框
    default: true

  - field_name: updated_at
    field_type: 日期
    auto_fill: true

  - field_name: updated_by
    field_type: 人员

# 预置配置
default_configs:
  - key: BUSINESS_CONTEXT
    value: |
      你是一个专注于AI自动化和工作流优化的小红书创作者...
    type: prompt

  - key: CONTENT_DIRECTIONS
    value: ["AI Agent开发", "N8N工作流", "小红书运营", "效率工具"]
    type: rule

  - key: TARGET_KEYWORDS
    value: ["AI", "自动化", "工作流", "N8N", "Claude", "效率"]
    type: keyword

  - key: EXCLUDE_KEYWORDS
    value: ["游戏", "娱乐", "美妆", "时尚", "美食"]
    type: keyword

  - key: RELEVANCE_THRESHOLD
    value: 70
    type: threshold

  - key: AUTO_APPROVE_THRESHOLD
    value: 85
    type: threshold
6.2 Redis缓存设计
python# 去重缓存（24小时TTL）
key_pattern: topic:dedupe:{topic_hash}
value: {
  "topic_id": "uuid",
  "title": "原标题",
  "processed_at": "2024-12-11T10:00:00Z"
}
ttl: 86400  # 24小时

# 热点缓存（2小时TTL）
key_pattern: hot:source:{source}
value: [
  {
    "rank": 1,
    "title": "热点标题",
    "heat": 98765,
    "url": "..."
  }
]
ttl: 7200  # 2小时

# 配置缓存（1小时TTL）
key_pattern: config:{config_key}
value: "配置值"
ttl: 3600  # 1小时，定期从飞书同步

7. 评分体系设计
7.1 相关性评分（0-100分）
pythondef calculate_relevance_score(
    direction_match: int,    # 40%
    audience_fit: int,       # 30%
    keyword_relevance: int,  # 20%
    trend_potential: int     # 10%
) -> int:
    """
    计算相关性总分
    
    Args:
        direction_match: 内容方向匹配度 (0-100)
        audience_fit: 目标受众匹配度 (0-100)
        keyword_relevance: 关键词相关性 (0-100)
        trend_potential: 趋势潜力 (0-100)
    
    Returns:
        total_score: 加权总分 (0-100)
    """
    weights = {
        'direction_match': 0.40,
        'audience_fit': 0.30,
        'keyword_relevance': 0.20,
        'trend_potential': 0.10
    }
    
    total = (
        direction_match * weights['direction_match'] +
        audience_fit * weights['audience_fit'] +
        keyword_relevance * weights['keyword_relevance'] +
        trend_potential * weights['trend_potential']
    )
    
    return round(total)
7.2 AI内容评分（0-100分）
pythondef calculate_ai_score(
    click_power: dict,       # 30%
    content_quality: dict,   # 25%
    value_sense: dict,       # 20%
    interaction_design: dict, # 10%
    platform_fit: dict       # 15%
) -> dict:
    """
    计算AI内容评分
    
    Returns:
        {
            "total_score": 89,
            "breakdown": {...},
            "grade": "A",
            "decision": "auto_approve"
        }
    """
    # 计算各维度小计
    scores = {
        'click_power': click_power['title_attraction'] + click_power['opening_hook'],
        'content_quality': (
            content_quality['information_density'] +
            content_quality['logical_flow'] +
            content_quality['actionability']
        ),
        'value_sense': (
            value_sense['problem_solving'] +
            value_sense['uniqueness']
        ),
        'interaction_design': (
            interaction_design['comment_guidance'] +
            interaction_design['save_share_motivation']
        ),
        'platform_fit': (
            platform_fit['xiaohongshu_style'] +
            platform_fit['compliance']
        )
    }
    
    total = sum(scores.values())
    
    # 评级
    if total >= 90:
        grade = 'A+'
    elif total >= 85:
        grade = 'A'
    elif total >= 80:
        grade = 'B+'
    elif total >= 75:
        grade = 'B'
    elif total >= 70:
        grade = 'C'
    else:
        grade = 'D'
    
    # 决策
    if total >= 85:
        decision = 'auto_approve'
    elif total >= 70:
        decision = 'human_review'
    else:
        decision = 'auto_reject'
    
    return {
        'total_score': total,
        'breakdown': scores,
        'grade': grade,
        'decision': decision
    }
7.3 优先级排序算法
pythondef calculate_priority_score(
    ai_score: int,          # 基础分
    relevance_score: int,   # 相关性加成
    heat_score: int,        # 热度加成
    time_decay: float       # 时效衰减
) -> float:
    """
    计算综合优先级分数
    
    Formula:
    priority = (ai_score * 0.5 + relevance_score * 0.3 + heat_score * 0.2) * time_decay
    
    Args:
        ai_score: AI评分 (0-100)
        relevance_score: 相关性评分 (0-100)
        heat_score: 平台热度 (归一化到0-100)
        time_decay: 时效衰减系数 (0-1)
    
    Returns:
        priority_score: 优先级分数 (0-100)
    """
    # 基础分计算
    base_score = (
        ai_score * 0.5 +
        relevance_score * 0.3 +
        heat_score * 0.2
    )
    
    # 应用时效衰减
    priority = base_score * time_decay
    
    return round(priority, 2)

def calculate_time_decay(hours_since_collected: int) -> float:
    """
    计算时效衰减系数
    
    - 0-6小时：100%
    - 6-24小时：线性衰减到70%
    - 24-48小时：线性衰减到40%
    - 48小时+：固定40%
    """
    if hours_since_collected <= 6:
        return 1.0
    elif hours_since_collected <= 24:
        return 1.0 - (hours_since_collected - 6) / 18 * 0.3  # 衰减到70%
    elif hours_since_collected <= 48:
        return 0.7 - (hours_since_collected - 24) / 24 * 0.3  # 衰减到40%
    else:
        return 0.4

8. 实施路线图
8.1 阶段一：MVP核心流程（第1-2周）
目标：验证自动选题Agent的可行性
yamldeliverables:
  - N8N主工作流（简化版）
  - 5个子工作流
  - 飞书表结构
  - 核心Prompt

tasks:
  week_1:
    - 搭建N8N环境
    - 创建飞书多维表格
    - 实现热点采集子流程（仅小红书）
    - 实现相关性评估子流程
    - 测试数据流转

  week_2:
    - 实现选题规划子流程
    - 实现内容大纲生成子流程
    - 实现AI评分子流程
    - 整合主工作流
    - 端到端测试

acceptance_criteria:
  - 成功采集小红书Top 20热点
  - 相关性评估准确率≥70%
  - 生成10个选题大纲
  - AI评分合理性验证
  - 数据完整存储到飞书

metrics:
  - 工作流成功率≥80%
  - 单个选题处理时间≤3分钟
  - 相关选题筛选率20-30%
8.2 阶段二：功能完善（第3-4周）
目标：提升Agent质量和自动化率
yamldeliverables:
  - 优化后的Prompt
  - 多平台热点采集
  - Redis去重系统
  - Telegram通知
  - 人工审核流程

tasks:
  week_3:
    - 接入微博、抖音热榜
    - 实现Redis缓存去重
    - 优化相关性评估Prompt
    - 优化选题规划Prompt
    - A/B测试不同Prompt版本

  week_4:
    - 实现Telegram通知推送
    - 搭建简易审核界面（或使用飞书视图）
    - 优化AI评分算法
    - 实现优先级排序
    - 建立闭环反馈机制

acceptance_criteria:
  - 支持3个平台热点采集
  - 去重准确率≥95%
  - AI评分准确率≥80%（与人工对比）
  - 自动通过率达到40-50%
  - 人工审核时间≤2分钟/条

metrics:
  - 相关性评估准确率≥80%
  - AI评分vs人工评分误差<10分
  - 自动化处理率≥70%（无需人工干预）
8.3 阶段三：系统优化（第5-6周）
目标：提升系统稳定性和智能化水平
yamldeliverables:
  - 完整的错误处理
  - 监控和告警
  - 数据分析看板
  - Agent自我优化机制

tasks:
  week_5:
    - 实现完整错误处理和重试
    - 添加监控指标（Prometheus）
    - 搭建Grafana看板
    - 优化缓存策略
    - 性能调优

  week_6:
    - 实现Agent自我学习
    - 建立评分反馈闭环
    - 自动调整Prompt参数
    - 整理文档和SOP
    - 团队培训

acceptance_criteria:
  - 系统可用性≥95%
  - 自动恢复率≥80%
  - 监控覆盖率100%
  - 文档完整度100%

metrics:
  - 平均处理时间≤2分钟/选题
  - 错误率≤5%
  - AI评分准确率≥85%
  - 自动通过率50-60%
8.4 阶段四：规模化运行（第7-8周）
目标：规模化运营，持续优化
yamldeliverables:
  - 生产环境部署
  - 完整的运营SOP
  - 数据分析报告
  - 优化建议

tasks:
  week_7:
    - 生产环境部署
    - 定时任务配置
    - 团队权限配置
    - 备份和恢复测试
    - 灰度发布

  week_8:
    - 收集1周运行数据
    - 分析选题质量
    - 优化Prompt和规则
    - 调整决策阈值
    - 生成分析报告

acceptance_criteria:
  - 连续7天稳定运行
  - 每天产出10-20个高质量选题
  - 选题采纳率≥60%
  - 团队满意度≥80%

metrics:
  - 选题库积累100+
  - 优质选题（score≥85）占比≥30%
  - 人工审核通过率≥80%
  - 最终发布转化率≥40%
8.5 长期迭代方向
yamlfuture_enhancements:
  - 多模态输入：图片、视频热点识别
  - 竞品监控：自动跟踪竞品选题
  - 用户反馈闭环：根据发布效果调整选题策略
  - AI生成封面图：自动生成匹配的封面图
  - 跨平台适配：支持抖音、知乎等平台选题
  - 智能排期：基于历史数据预测最佳发布时间

9. 快速启动清单
9.1 环境准备（第1天）
bash# 1. 安装N8N
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n

# 2. 安装Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:alpine

# 3. 配置环境变量
cat > .env << EOF
# LLM
ANTHROPIC_API_KEY=sk-ant-xxx

# 数据抓取
DAILYHOT_API_URL=https://api-hot.imsyy.top
FIRECRAWL_API_KEY=fc-xxx

# 飞书
LARK_APP_ID=cli_xxx
LARK_APP_SECRET=xxx
LARK_TABLE_ID_CANDIDATES=tblxxx
LARK_TABLE_ID_HISTORY=tblxxx
LARK_TABLE_ID_CONFIG=tblxxx

# Telegram
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
9.2 数据库初始化（第1天）
python# 创建飞书多维表格
tables = [
    'topic_candidates',
    'topic_history',
    'business_config'
]

for table in tables:
    create_lark_table(table)
    init_table_fields(table)

# 初始化配置
init_business_config()
9.3 导入N8N工作流（第2天）
bash# 导入工作流JSON文件
n8n import:workflow --input=workflows/

# 验证工作流
n8n execute --id=topic_selection_main --test
9.4 测试运行（第2-3天）
bash# 1. 测试热点采集
curl http://localhost:5678/webhook/test-collector

# 2. 测试相关性评估
curl http://localhost:5678/webhook/test-evaluator

# 3. 测试完整流程
curl http://localhost:5678/webhook/run-full-pipeline

# 4. 查看结果
# 登录飞书查看topic_candidates表

10. 监控和优化
10.1 关键指标监控
yamlmetrics:
  # 系统指标
  - name: workflow_success_rate
    target: "≥95%"
    alert: "<90%"

  - name: avg_processing_time
    target: "≤2分钟"
    alert: ">5分钟"

  # 业务指标
  - name: relevance_accuracy
    target: "≥80%"
    measurement: 人工抽查100条对比

  - name: ai_score_accuracy
    target: "误差<10分"
    measurement: 与人工评分对比

  - name: auto_approve_rate
    target: "40-60%"
    reasoning: 太低=效率低，太高=质量风险

  # 质量指标
  - name: topic_adoption_rate
    target: "≥60%"
    description: 选题被采纳创作的比例

  - name: published_success_rate
    target: "≥80%"
    description: 创作后成功发布的比例
10.2 A/B测试框架
python# 测试不同Prompt版本
ab_tests = [
    {
        'test_id': 'prompt_v1_vs_v2',
        'versions': {
            'A': 'RELEVANCE_PROMPT_V1',
            'B': 'RELEVANCE_PROMPT_V2'
        },
        'traffic_split': 0.5,
        'metrics': ['accuracy', 'processing_time'],
        'duration': '7 days'
    },
    {
        'test_id': 'score_threshold',
        'versions': {
            'A': {'auto_approve': 85, 'auto_reject': 70},
            'B': {'auto_approve': 80, 'auto_reject': 65}
        },
        'metrics': ['auto_approve_rate', 'quality_score'],
        'duration': '14 days'
    }
]

总结
这个完整的自动选题Agent设计方案具备以下特点：
✅ 可实施性强

基于N8N，可视化工作流
模块化设计，易于测试和迭代
详细的Prompt和代码示例

✅ 可维护性高

清晰的数据模型和状态机
完整的错误处理和监控
飞书表格存储，便于管理

✅ 可扩展性好

支持多平台热点源
可动态调整配置和Prompt
预留了AI自我优化接口

✅ 智能化水平高

100分六维度评分体系
Plan-Execute Agent协作
Human-in-the-loop审核