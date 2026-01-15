#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SessionStart Hook - 会话开始时的提醒
"""
import sys
import os
import io

# 在 Windows 上设置 UTF-8 输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    """会话开始时输出 SoT 文档列表和 Phase 1 约束提醒"""

    print("=" * 80)
    print("🎯 AI 广告代投系统 - SoT 裁判链 (v4.4)")
    print("=" * 80)
    print()

    print("📚 SoT 文档优先级顺序：")
    print("  1. docs/sot/MASTER.md v4.4 - 系统全局规则")
    print("  2. docs/1.overview/BUSINESS_FLOW_MANAGEMENT.md - 业务流程管理")
    print("  3. docs/1.overview/MVP_PHASE_DESIGN.md - MVP 阶段设计")
    print("  4. docs/sot/STATE_MACHINE.md v2.6 - 状态机规范")
    print("  5. docs/sot/DATA_SCHEMA.md v5.2 - 数据模型")
    print("  6. docs/sot/DATA_SCHEMA.md v5.11 §3.4.4 - 账本规则")
    print("  7. docs/sot/BUSINESS_RULES.md v3.2 - 业务规则")
    print("  8. docs/sot/API_SOT.md v9.0 - API 规范")
    print("  9. docs/sot/ERROR_CODES_SOT.md v2.1 - 错误码")
    print(" 10. docs/sot/AUTH_SPEC.md v2.0 - 认证授权")
    print()

    print("⚠️  Phase 1（照亮阶段）核心约束：")
    print("  ❌ 禁止任何自动阻断/拒绝/暂停/冻结功能")
    print("  ❌ 禁止自动惩罚机制（扣分、禁用账户等）")
    print("  ❌ 禁止强制审批流程（仅记录和提示）")
    print("  ✅ 允许：记录事实、展示状态、提示异常")
    print("  ✅ 允许：高亮警告、数据统计、趋势分析")
    print()

    print("👥 业务层角色（6 个，PRD v5.1）：")
    print("  • ceo - 老板：资金安全、公司盈亏、最终决策")
    print("  • project_owner - 项目负责人：日报审核、项目盈亏、资金使用效率")
    print("  • finance - 财务：资金出入准确、数据真实、对账")
    print("  • pitcher - 投手：CPL 达标、日报准确、执行投放")
    print("  • account_manager - 户管：账户分配、账户状态监控")
    print("  • admin - 管理员：系统配置（不参与业务）")
    print()
    print("🔧 技术层角色（4 个，MASTER.md v4.6）：")
    print("  • admin, finance, account_manager, media_buyer")
    print("  • project_owner 通过 is_project_owner=true 判断")
    print()

    print("🛡️  AI 防幻觉原则（MASTER.md §7）：")
    print("  AH-01: 禁止假设数据一致 - 遇到缺失标记\"待确认\"")
    print("  AH-02: 禁止自动做管理裁决 - 不生成自动拒绝/暂停代码")
    print("  AH-03: 禁止引入 SoT 未定义概念 - 发现缺失→停止→询问")
    print("  AH-04: 必须遵循 Phase 1 软性原则 - 提示+高亮+记录")
    print("  AH-05: 遇到歧义必须停止并询问 - 停止→列出歧义→询问")
    print()

    print("=" * 80)
    print("✅ Hook 提醒完成 - 请遵循以上约束进行开发")
    print("=" * 80)
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
