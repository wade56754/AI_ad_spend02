#!/usr/bin/env python3
"""
财务模块全量测试脚本
使用 AI 代码工厂执行测试工作流
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator
import json
from datetime import datetime


def main():
    """执行财务模块全量测试"""
    
    # 初始化代码工厂编排器
    orchestrator = CodeFactoryOrchestrator(project_root=project_root)
    
    # 定义测试需求
    requirement = """
    对财务模块进行全量测试，包括：
    
    1. 财务服务测试：
       - test_finance_service.py
       - test_finance_v2_service.py
       - test_finance_dashboard_service.py
    
    2. 利润计算测试：
       - test_profit_service_v2.py
       - test_finance_profit_api.py
    
    3. 账本服务测试：
       - test_ledger_service.py
       - test_ledger_posting_service.py
    
    4. 充值管理测试：
       - test_topup_service.py
       - test_topup_api.py
       - test_topup_permissions.py
    
    5. 对账管理测试：
       - test_reconciliation_api.py
       - test_reconciliation_service.py
       - test_reconciliation_permissions.py
    
    6. 权限测试：
       - test_topup_permissions.py
       - test_reconciliation_permissions.py
    
    测试要求：
    - 运行所有财务模块相关的测试用例
    - 生成详细的测试报告
    - 检查测试覆盖率
    - 识别失败的测试用例
    - 提供修复建议
    """
    
    print("=" * 80)
    print("🎯 AI 代码工厂 - 财务模块全量测试")
    print("=" * 80)
    print(f"\n📋 需求: {requirement[:200]}...")
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 执行测试工作流
    try:
        result = orchestrator.execute(
            requirement=requirement,
            workflow_type="bug_fixing"  # 使用 bug_fixing 工作流，包含 test-automator
        )
        
        # 输出结果
        print("\n" + "=" * 80)
        print("📊 执行结果")
        print("=" * 80)
        print(f"\n✅ 状态: {result.get('status', 'unknown')}")
        print(f"\n🔄 工作流类型: {result.get('workflow_type', 'unknown')}")
        
        # 显示代理执行结果
        print("\n" + "-" * 80)
        print("📝 代理执行详情")
        print("-" * 80)
        
        execution_results = result.get('execution_results', [])
        for i, exec_result in enumerate(execution_results, 1):
            agent_id = exec_result.get('agent_id', 'unknown')
            success = exec_result.get('success', False)
            status_icon = "✅" if success else "❌"
            
            print(f"\n{i}. {status_icon} {agent_id}")
            print(f"   状态: {'成功' if success else '失败'}")
            
            if exec_result.get('tokens_used'):
                print(f"   Token 使用: {exec_result.get('tokens_used')}")
            
            if exec_result.get('execution_time'):
                print(f"   执行时间: {exec_result.get('execution_time'):.2f}s")
            
            if exec_result.get('error'):
                print(f"   错误: {exec_result.get('error')}")
            
            if exec_result.get('output'):
                output = exec_result.get('output', '')
                if len(output) > 200:
                    output = output[:200] + "..."
                print(f"   输出预览: {output}")
        
        # 显示性能指标
        print("\n" + "-" * 80)
        print("📈 性能指标")
        print("-" * 80)
        
        metrics = result.get('performance_metrics', {})
        if metrics:
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
        else:
            print("   暂无性能指标")
        
        # 保存结果到文件
        output_file = project_root / "test-results" / f"finance_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        print("\n" + "=" * 80)
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return 0 if result.get('status') == 'completed' else 1
        
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
