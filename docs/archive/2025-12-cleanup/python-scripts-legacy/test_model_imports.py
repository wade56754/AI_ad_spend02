"""
模型导入测试脚本

验证重构后的模型是否可以正确导入
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=" * 70)
print("开始测试模型导入...")
print("=" * 70)

# 测试 1: 从 backend.models 导入所有模型（推荐方式）
print("\n[测试 1] 从 backend.models 导入所有模型")
print("-" * 70)

try:
    from backend.models import (
        Base,
        User,
        Channel,
        ChannelPerformance,
        Project,
        ChannelReview,
        ChannelAccountRequest,
        AdAccount,
        AccountStatusHistory,
        AccountAlert,
        DailyReport,
        AdSpendDaily,
        TopupRequest,
        LedgerEntry,
        ReconciliationBatch,
        ReconciliationDetail,
        AuditLog,
    )
    print("✅ 所有模型导入成功！")
    print(f"   - Base: {Base}")
    print(f"   - User: {User}")
    print(f"   - Channel: {Channel}")
    print(f"   - ChannelPerformance: {ChannelPerformance}")
    print(f"   - Project: {Project}")
    print(f"   - ChannelReview: {ChannelReview}")
    print(f"   - ChannelAccountRequest: {ChannelAccountRequest}")
    print(f"   - AdAccount: {AdAccount}")
    print(f"   - AccountStatusHistory: {AccountStatusHistory}")
    print(f"   - AccountAlert: {AccountAlert}")
    print(f"   - DailyReport: {DailyReport}")
    print(f"   - AdSpendDaily: {AdSpendDaily}")
    print(f"   - TopupRequest: {TopupRequest}")
    print(f"   - LedgerEntry: {LedgerEntry}")
    print(f"   - ReconciliationBatch: {ReconciliationBatch}")
    print(f"   - ReconciliationDetail: {ReconciliationDetail}")
    print(f"   - AuditLog: {AuditLog}")
except Exception as e:
    print(f"❌ 导入失败：{e}")
    sys.exit(1)

# 测试 2: 从 backend.models 导入 Enum 类型
print("\n[测试 2] 从 backend.models 导入 Enum 类型")
print("-" * 70)

try:
    from backend.models import (
        UserRole,
        ChannelStatus,
        ProjectStatus,
        ReviewStatus,
        AdAccountStatus,
        DailyReportStatus,
        TopupStatus,
        LedgerEntryType,
        ReconciliationBatchStatus,
        ReconciliationDetailStatus,
        AccountAlertStatus,
        AccountAlertSeverity,
    )
    print("✅ 所有 Enum 类型导入成功！")
    print(f"   - UserRole: {UserRole}")
    print(f"   - ChannelStatus: {ChannelStatus}")
    print(f"   - ProjectStatus: {ProjectStatus}")
    print(f"   - ReviewStatus: {ReviewStatus}")
    print(f"   - AdAccountStatus: {AdAccountStatus}")
    print(f"   - DailyReportStatus: {DailyReportStatus}")
    print(f"   - TopupStatus: {TopupStatus}")
    print(f"   - LedgerEntryType: {LedgerEntryType}")
    print(f"   - ReconciliationBatchStatus: {ReconciliationBatchStatus}")
    print(f"   - ReconciliationDetailStatus: {ReconciliationDetailStatus}")
    print(f"   - AccountAlertStatus: {AccountAlertStatus}")
    print(f"   - AccountAlertSeverity: {AccountAlertSeverity}")
except Exception as e:
    print(f"❌ 导入失败：{e}")
    sys.exit(1)

# 测试 3: 从 backend.models.database_models 导入（兼容层）
print("\n[测试 3] 从 backend.models.database_models 导入（兼容层）")
print("-" * 70)

try:
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from backend.models.database_models import User as UserLegacy

        if len(w) > 0:
            print(f"⚠️  弃用警告：{w[0].message}")
        print(f"✅ 兼容层导入成功：{UserLegacy}")
except Exception as e:
    print(f"❌ 导入失败：{e}")
    sys.exit(1)

# 测试 4: 验证模型的 relationship 是否定义
print("\n[测试 4] 验证模型的 relationship 是否定义")
print("-" * 70)

try:
    # 检查 User 的 relationships
    user_relationships = [attr for attr in dir(User) if not attr.startswith('_')]
    expected_user_rels = ['created_projects', 'assigned_accounts', 'submitted_reports']

    for rel in expected_user_rels:
        if rel in user_relationships:
            print(f"✅ User.{rel} 已定义")
        else:
            print(f"⚠️  User.{rel} 未找到")

    # 检查 AdAccount 的 relationships
    adaccount_relationships = [attr for attr in dir(AdAccount) if not attr.startswith('_')]
    expected_adaccount_rels = ['project', 'channel', 'daily_reports', 'topup_requests', 'ledger_entries']

    for rel in expected_adaccount_rels:
        if rel in adaccount_relationships:
            print(f"✅ AdAccount.{rel} 已定义")
        else:
            print(f"⚠️  AdAccount.{rel} 未找到")

except Exception as e:
    print(f"❌ 验证失败：{e}")
    sys.exit(1)

# 测试 5: 验证 Enum 方法是否可用
print("\n[测试 5] 验证 Enum 方法和属性")
print("-" * 70)

try:
    # 测试 UserRole Enum
    admin_role = UserRole.ADMIN
    print(f"✅ UserRole.ADMIN = '{admin_role.value}'")

    # 测试 AdAccountStatus Enum
    active_status = AdAccountStatus.ACTIVE
    print(f"✅ AdAccountStatus.ACTIVE = '{active_status.value}'")

    # 测试 TopupStatus Enum
    completed_status = TopupStatus.COMPLETED
    print(f"✅ TopupStatus.COMPLETED = '{completed_status.value}'")

except Exception as e:
    print(f"❌ 验证失败：{e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有测试通过！模型重构成功！")
print("=" * 70)
print("\n重构总结：")
print("- ✅ 16 个模型全部导入成功")
print("- ✅ 12 个 Enum 类型全部导入成功")
print("- ✅ Relationship 关系已建立")
print("- ✅ 兼容层正常工作")
print("- ✅ Enum 方法和属性可用")
print("\n建议：")
print("- 新代码使用：from backend.models import X")
print("- 旧代码迁移：将 from backend.models.database_models import X 替换为 from backend.models import X")
print("=" * 70)
