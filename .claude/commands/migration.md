# /migration - 数据库迁移助手

> **版本**: v1.0
> **优先级**: 中
> **依赖**: Alembic, SQLAlchemy

---

## 用途

辅助数据库迁移操作，包括生成迁移脚本、验证数据一致性、回滚管理等。

---

## 使用方式

```bash
/migration generate <name>        # 生成迁移脚本
/migration validate               # 验证迁移安全性
/migration apply                  # 应用迁移
/migration rollback               # 回滚上一次迁移
/migration history                # 查看迁移历史
/migration diff                   # 对比模型与数据库
```

---

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `generate` | 生成迁移 | `/migration generate add_status_field` |
| `validate` | 验证迁移 | 检查数据安全性 |
| `apply` | 应用迁移 | 执行待迁移脚本 |
| `rollback` | 回滚 | 撤销最近迁移 |
| `history` | 历史 | 查看迁移记录 |
| `diff` | 差异 | 模型 vs 数据库 |
| `--dry-run` | 预览 | 不实际执行 |

---

## 子命令详解

### generate - 生成迁移

```bash
/migration generate add_status_field
```

工作流程:
1. 分析 `backend/models/` 中的模型变更
2. 对比当前数据库 schema
3. 生成 Alembic 迁移脚本
4. 添加 SoT 兼容性检查

输出:
```
🔄 生成迁移脚本
===============

检测到模型变更:
  + DailyReport.new_status (String)
  ~ DailyReport.amount (Numeric → Decimal)
  - DailyReport.old_field

生成文件:
  migrations/versions/20260102_add_status_field.py

⚠️ 注意事项:
  - 删除字段需要数据备份
  - 类型变更可能导致数据丢失

请审查后运行: /migration apply
```

### validate - 验证迁移

```bash
/migration validate
```

检查项:
1. **数据安全**: 是否有数据丢失风险
2. **索引影响**: 大表添加索引的锁表时间
3. **外键约束**: 级联删除风险
4. **回滚可行性**: 是否可逆

输出:
```
🔍 迁移验证
==========

待迁移: 2 个脚本

1. 20260102_add_status_field.py
   ✅ 数据安全: 仅添加字段
   ✅ 索引影响: 无
   ✅ 回滚可行: 是

2. 20260101_change_amount_type.py
   ⚠️ 数据安全: 类型变更可能丢失精度
   ✅ 索引影响: 无
   ✅ 回滚可行: 是

建议:
  - 在非高峰期执行
  - 先在测试环境验证
```

### apply - 应用迁移

```bash
/migration apply
```

输出:
```
🚀 应用迁移
==========

迁移 1/2: 20260102_add_status_field.py
  执行中... ✅ 完成 (0.3s)

迁移 2/2: 20260101_change_amount_type.py
  执行中... ✅ 完成 (1.2s)

迁移完成!
  成功: 2
  失败: 0
  耗时: 1.5s

当前版本: 20260102_add_status_field
```

### rollback - 回滚

```bash
/migration rollback
```

输出:
```
⏪ 回滚迁移
==========

回滚: 20260102_add_status_field.py
  执行中... ✅ 完成

当前版本: 20260101_change_amount_type
```

### history - 历史

```bash
/migration history
```

输出:
```
📜 迁移历史
==========

  ✅ 20260102_add_status_field (当前)
  ✅ 20260101_change_amount_type
  ✅ 20251230_add_project_table
  ✅ 20251225_initial
```

### diff - 差异

```bash
/migration diff
```

输出:
```
📊 模型 vs 数据库差异
====================

新增:
  + DailyReport.pending_review (待生成迁移)

修改:
  ~ User.role: VARCHAR(20) → VARCHAR(50) (待生成迁移)

删除:
  (无)

运行 /migration generate <name> 生成迁移
```

---

## SoT 集成

迁移会自动检查:

1. **DATA_SCHEMA.md 一致性**: 模型是否与 SoT 定义一致
2. **状态机兼容**: 新状态是否在 STATE_MACHINE.md 中定义
3. **字段命名**: 是否符合 SoT 命名规范

---

## 最佳实践

### 迁移命名

```
<date>_<action>_<target>.py

示例:
20260102_add_status_to_daily_report.py
20260102_remove_deprecated_field.py
20260102_change_amount_precision.py
```

### 生产环境迁移

```bash
# 1. 先验证
/migration validate

# 2. 预览
/migration apply --dry-run

# 3. 备份
pg_dump -Fc mydb > backup.dump

# 4. 执行
/migration apply

# 5. 验证
/migration diff  # 应该无差异
```

---

## 输出

1. 迁移脚本 (`migrations/versions/`)
2. 执行日志
3. 验证报告
