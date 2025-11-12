# Repository Guidelines

## 项目结构与模块
- `backend/`：FastAPI 后端（`routers/`、`models/`、`core/`、`utils/`、`services/`、`middleware/`）。
- `app/`：Next.js 15 前端（App Router），UI 在 `components/`，共享逻辑在 `lib/`。
- `tests/`：Pytest 测试集；标记与发现规则见 `pytest.ini`。
- `docs/`：架构、部署与开发文档。
- `scripts/`：本地工具与测试脚本。

## 构建、运行与测试
- 后端环境：`python -m venv venv && venv\Scripts\activate`（Win）后执行 `pip install -r requirements.txt -r requirements-test.txt`。
- 启动后端：`uvicorn backend.main:app --reload`（读取 `.env`）。
- 运行测试：`pytest`；覆盖率：`pytest --cov=backend --cov-report=term-missing`；快捷集：`python run_tests.py --type unit|integration|smoke`。
- 前端安装：`pnpm install`（无则用 `npm ci`）。
- 前端开发/构建/检查：`pnpm dev`、`pnpm build`、`pnpm lint`。

## 代码风格与命名
- Python：使用 `black`、`isort`、`flake8`、`mypy`；模块/文件与函数/变量用 `snake_case`，类用 `PascalCase`；通用工具放在 `backend/utils/`。
- TypeScript/React：ESLint 配置见 `eslint.config.mjs`（`next/core-web-vitals`），2 空格缩进；组件 `PascalCase`，文件 `kebab-case`（如 `update-password-form.tsx`）。

## 测试规范
- 框架：`pytest`，常用标记有 `unit`、`integration`、`functional`、`api`、`database`、`security`、`performance`、`smoke`。
- 命名：文件 `tests/test_*.py`，函数 `test_*`。
- 覆盖率：使用 `run_tests.py --coverage` 目标≥70%；HTML 报告在 `htmlcov/`。

## 提交与合并请求
- 提交信息遵循 Conventional Commits：`feat:`、`fix:`、`docs:`、`test:`、`chore:`；主题≤72字符。
- PR 要求：清晰描述、关联 Issue、测试计划/输出、UI 截图（如适用）；确保 `pytest` 通过且 `pnpm lint` 无警告。

## 安全与配置
- 配置由 `backend/core/config.py` 从 `.env` 读取：需含 `DATABASE_URL`、`JWT_SECRET`（≥64）、`ENCRYPTION_KEY`（≥32）、`SUPABASE_URL`、`SUPABASE_KEY`、`ALLOWED_ORIGINS`。
- 禁止提交密钥；按环境维护独立 `.env` 文件。

## 用户级别规则
- 与用户及外部协作者全程使用中文交流（Issue/PR 描述与讨论、用户文档、命令示例）。
- 变更尽量小而聚焦；涉及后端行为的改动必须在 `tests/` 增补或更新对应测试。
