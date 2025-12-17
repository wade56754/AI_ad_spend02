# 路由模块开发待办事项
# Last Updated: 2025-11-15

## 📋 已完成的模块 (✅)
- `projects.py` - 项目管理API (✅ 完整实现)
- `authentication.py` - 用户认证API (✅ 完整实现)
- `ad_spend.py` - 广告消耗API (✅ 完整实现)
- `ad_accounts.py` - 广告账户API (✅ 完整实现)
- `channels.py` - 渠道管理API (✅ 完整实现)

## 🚧 暂时跳过的模块 (需要评估优先级)

### 高优先级
- `reconciliation.py` - 对账管理API
  - **状态**: 有基础实现，需要性能优化
  - **建议**: 使用 `reconciliation_service_optimized.py` 替换
  - **依赖**: 优化后的对账服务

- `topup.py` / `topups.py` - 充值管理API
  - **状态**: 完整实现但存在装饰器问题
  - **问题**: `@require_role` 装饰器语法错误
  - **修复**: 将装饰器改为Depends参数

- `daily_reports.py` - 日报管理API
  - **状态**: 完整实现
  - **依赖**: 需要安装 pandas (pip install pandas)

### 中优先级
- `reports.py` - 报表生成API
  - **状态**: 有基础实现
  - **需求**: 完善报表生成逻辑

- `import_jobs.py` - 数据导入API
  - **状态**: 有基础实现
  - **需求**: 完善文件处理和错误处理

### 低优先级
- `ai_analytics.py` - AI分析API
  - **状态**: 有基础实现
  - **需求**: 集成真实的AI模型

- `project_templates.py` - 项目模板API
  - **状态**: 有基础实现
  - **需求**: 完善模板管理功能

## ❌ 需要重构或删除的模块

### 重复模块 (建议删除)
- `auth.py` - 与 `authentication.py` 功能重复
  - **原因**: 两个文件都实现用户认证功能
  - **建议**: 删除 `auth.py`，保留 `authentication.py`

- `reconciliations.py` - 与 `reconciliation.py` 功能重复
  - **建议**: 合并或删除其中一个

- `ad_account.py` - 与 `ad_accounts.py` 功能重复
  - **建议**: 合并或删除其中一个

### 过时模块 (需要更新)
- `supabase_auth.py` - 可能过时
  - **状态**: 需要检查是否与当前认证系统兼容
  - **建议**: 评估是否需要保留

## 🔧 立即行动项

### 1. 删除重复文件
```bash
# 删除auth.py，保留authentication.py
rm routers/auth.py

# 删除reconciliations.py，保留reconciliation.py
rm routers/reconciliations.py

# 删除ad_account.py，保留ad_accounts.py
rm routers/ad_account.py
```

### 2. 修复装饰器问题
```python
# 在topup.py中，将装饰器改为Depends参数
# 原代码:
@require_role(["media_buyer", "account_manager"])
async def create_topup_request(...):

# 修改为:
async def create_topup_request(
    current_user: User = Depends(require_role(["media_buyer", "account_manager"])),
    ...
):
```

### 3. 更新main.py导入
取消注释可用的路由模块：
```python
from routers import (
    projects,
    authentication,
    ad_spend,
    ad_accounts,
    channels,
    # 取消注释以下模块
    # import_jobs,  # 数据导入
    # reports,     # 报表生成
    # daily_reports, # 日报管理
    # reconciliation, # 对账管理 (需先优化)
)
```

## 📊 优先级建议

1. **立即执行**: 删除重复文件，修复装饰器问题
2. **短期目标**: 启用reports、daily_reports、import_jobs
3. **中期目标**: 优化reconciliation，启用topup
4. **长期目标**: 评估AI analytics和project_templates需求

## 🧪 测试要求

每次修改路由模块后，必须运行：
```bash
# 后端测试
python -m pytest tests/ -v

# 应用启动测试
uvicorn main:app --reload

# 路由可用性测试
curl -X GET http://localhost:8000/api/v1/health
```

## 📝 更新日志

- 2025-11-15: 创建TODO文档，明确路由模块状态
- 2025-11-15: 标记重复和过时模块
- 2025-11-15: 提供具体的修复建议和优先级