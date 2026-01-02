# 同步进度文档

从 Task Master MCP 同步任务卡到 `memory-bank/progress.md`。

## 使用方法

```
/sync-progress
```

## 执行逻辑

1. 调用 Task Master MCP 获取所有任务
2. 按模块分类统计任务状态
3. 生成 progress.md 文档
4. 显示同步结果

## 自动同步场景

以下操作会自动触发同步：
- 完成任务卡 (`set_task_status` → done)
- 启动新任务 (`set_task_status` → in-progress)
- 解析 PRD 生成任务后

## 执行步骤

请执行以下操作：

### 步骤 1: 获取 Task Master 任务

使用 `mcp__taskmaster-ai__get_tasks` 工具获取所有任务：

```
projectRoot: 当前项目根目录
withSubtasks: true
```

### 步骤 2: 分析任务数据

统计以下指标：
- 总任务数
- 已完成任务数
- 进行中任务数
- 待开始任务数
- 各模块完成率

### 步骤 3: 生成 progress.md

根据任务数据生成 progress.md，包含：

1. **总体进度** - 进度条和完成率
2. **模块进度** - 按模块分类的任务列表
3. **已完成任务** - 最近完成的任务
4. **当前进行中** - 正在处理的任务
5. **下一步计划** - 高优先级待办任务
6. **同步信息** - 时间戳和元数据

### 步骤 4: 更新文件

将生成的内容写入 `memory-bank/progress.md`。

### 步骤 5: 显示结果

输出同步摘要：
```
✅ 进度同步完成!
   - 总任务: XX
   - 已完成: XX (XX%)
   - 进行中: XX
   - 待开始: XX
```

## 输出格式

生成的 progress.md 格式示例：

```markdown
# AI 广告代投管理系统 - 进度记录

> **最后更新**: YYYY-MM-DD HH:MM
> **数据来源**: Task Master MCP (自动同步)

## 1. 总体进度

任务完成率: ████████░░░░░░░░░░░░ 40%

| 指标 | 数值 |
|------|------|
| 总任务数 | 25 |
| 已完成 | 10 / 25 |
| 完成率 | 40% |

## 2. 模块进度

### M0 基础设施
进度: ████████████░░░ 80% (4/5)

| 任务卡 | 描述 | 状态 | 优先级 |
|--------|------|------|--------|
| TASK-AUTH-001 | 用户登录/登出 | ✅ done | 🔴 |
...
```

## 配置

同步脚本位于 `scripts/sync_progress.py`，可通过以下方式运行：

```bash
python scripts/sync_progress.py --project-root /path/to/project
```

## 注意事项

- 同步会覆盖现有 progress.md（旧文件备份为 .bak）
- 已取消的任务不计入完成率
- 时间戳使用本地时间
