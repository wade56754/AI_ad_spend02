# Tasks: update-reconciliation-sot-7-role

> **状态**: Completed
> **优先级**: P1
> **完成日期**: 2025-12-26

---

## 1. 文档更新

### 1.1 RECONCILIATION_SOT.md 升级

- [x] 1.1.1 更新文档版本头: `v1.0 → v2.0`
- [x] 1.1.2 更新 §1.1 文档职责中的角色引用
- [x] 1.1.3 更新 §4.2 流程角色权限表
  - 移除 `data_operator` 角色
  - 添加 `ceo`, `project_owner`, `supervisor`, `pitcher` 角色
  - 将 `media_buyer` 重命名为 `pitcher`
- [x] 1.1.4 重写 §12.1 角色权限矩阵为 7 角色版本
- [x] 1.1.5 更新 §12.2 RLS 策略示例 SQL
- [x] 1.1.6 添加变更记录: v2.0 changelog

### 1.2 关联文档检查

- [x] 1.2.1 确认 RECONCILIATION_CONTROL_CENTER_ARCHITECTURE.md v2.1 已对齐
- [x] 1.2.2 确认 AUTH_SPEC.md v2.0 定义了 7 角色

---

## 2. 代码验证 (可选)

### 2.1 权限检查验证

- [ ] 2.1.1 检查 `backend/core/permissions.py` 角色定义
- [ ] 2.1.2 检查对账相关 Router 的权限装饰器

---

## 3. 回归测试

- [ ] 3.1 运行对账模块相关测试
- [ ] 3.2 验证权限控制正确性

---

## 4. 归档

- [ ] 4.1 运行 `openspec archive update-reconciliation-sot-7-role --yes`

---

## Notes

- 本变更不涉及数据库迁移
- 本变更不涉及 API 端点变更
- 状态机定义保持不变 (5 状态)
- 文档更新已于 2025-12-26 完成
