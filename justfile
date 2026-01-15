# AI广告代投管理系统 - 统一命令入口
# 使用方式: just <command>
# 安装just: https://just.systems/man/en/chapter_4.html

# 默认命令
default:
    @just --list

# ============ 开发环境 ============

# 启动开发环境（后端+前端+数据库）
dev:
    docker-compose up -d db
    @echo "等待数据库启动..."
    sleep 3
    just dev-backend &
    just dev-frontend

# 仅启动后端
dev-backend:
    cd backend && uvicorn main:app --reload --port 8000

# 仅启动前端
dev-frontend:
    cd frontend && pnpm run dev

# 停止所有服务
stop:
    docker-compose down

# ============ 测试 ============

# 运行全部测试
test:
    just test-unit
    just test-lint

# 单元测试（带覆盖率）
test-unit:
    cd backend && pytest -q --cov=. --cov-report=xml --cov-report=html

# 代码检查
test-lint:
    cd backend && ruff check . && ruff format --check .
    cd backend && mypy . --strict

# 验收测试
test-acceptance:
    cd backend && pytest tests/acceptance/ -v --html=reports/acceptance.html

# 类型检查
test-types:
    cd backend && mypy . --strict

# ============ 数据库 ============

# 数据库迁移（升级）
migrate:
    cd backend && alembic upgrade head

# 数据库迁移（回滚一步）
migrate-down:
    cd backend && alembic downgrade -1

# 创建新迁移
migrate-new name:
    cd backend && alembic revision --autogenerate -m "{{name}}"

# 检查迁移可回滚性
migrate-check:
    python scripts/check_migration.py

# ============ 质量门禁 ============

# PR门禁（CI使用）
ci-check:
    just test-unit
    just test-lint
    just migrate-check
    python scripts/check_changelog.py

# 上线门禁
release-check:
    just ci-check
    just test-acceptance
    @echo "请确认以下事项："
    @echo "  [ ] CHANGELOG已更新"
    @echo "  [ ] 老板已确认（PR label或release文档）"
    @echo "  [ ] 回滚点已标记"

# 标记回滚点
release-tag:
    git tag pre-release-$(date +%Y%m%d-%H%M%S)
    @echo "回滚点已标记"

# ============ 文档 ============

# 检查CHANGELOG
check-changelog:
    python scripts/check_changelog.py

# 生成API文档
docs-api:
    cd backend && python -m scripts.generate_openapi

# ============ 清理 ============

# 清理临时文件
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name .pytest_cache -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf backend/reports/*
    rm -rf frontend/.next
