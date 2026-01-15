#!/usr/bin/env python3
"""
使用 AI 代码工厂分析财务模块测试用例
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 财务模块测试文件列表
FINANCE_TEST_FILES = [
    "backend/tests/test_finance_profit_api.py",
    "backend/tests/services/test_finance_service.py",
    "backend/tests/services/test_finance_v2_service.py",
    "backend/tests/services/test_finance_dashboard_service.py",
    "backend/tests/services/test_profit_service_v2.py",
    "backend/tests/services/test_ledger_service.py",
    "backend/tests/test_topup_service.py",
    "backend/tests/test_topup_api.py",
    "backend/tests/test_topup_permissions.py",
    "backend/tests/test_reconciliation_api.py",
    "backend/tests/test_reconciliation_service.py",
    "backend/tests/test_reconciliation_permissions.py",
]


def analyze_tests_with_factory():
    """使用代码工厂分析测试用例"""
    print("=" * 80)
    print("🤖 AI 代码工厂 - 财务模块测试用例分析")
    print("=" * 80)
    print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator
        
        orchestrator = CodeFactoryOrchestrator(project_root=project_root)
        
        # 读取测试文件内容
        test_files_content = {}
        for test_file in FINANCE_TEST_FILES:
            file_path = project_root / test_file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    test_files_content[test_file] = f.read()[:5000]  # 限制长度
        
        requirement = f"""
        对财务模块进行全量测试分析，包括以下测试文件：
        
        {', '.join(FINANCE_TEST_FILES)}
        
        请分析：
        1. 测试用例覆盖范围（服务层、API层、权限层）
        2. 测试用例完整性（是否覆盖所有关键功能）
        3. 测试用例质量（断言、边界条件、异常处理）
        4. 测试用例组织（fixture使用、测试类结构）
        5. 缺失的测试用例（需要补充的测试场景）
        6. 测试用例改进建议
        
        测试文件内容摘要：
        {chr(10).join([f'{k}: {len(v)} 字符' for k, v in test_files_content.items()])}
        """
        
        print("📋 需求:")
        print(requirement[:500] + "...")
        print(f"\n📁 测试文件数量: {len(FINANCE_TEST_FILES)}")
        print(f"📄 已读取文件: {len(test_files_content)}")
        
        print("\n🚀 执行代码工厂工作流...\n")
        
        # 执行代码审查工作流
        result = orchestrator.execute(
            requirement=requirement,
            workflow_type="code_review"  # 使用代码审查工作流
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
                # 显示完整输出
                print(f"\n   输出:")
                print("   " + "-" * 76)
                # 格式化输出，每行添加缩进
                output_lines = output.split('\n')
                for line in output_lines[:100]:  # 限制显示前100行
                    print(f"   {line}")
                if len(output_lines) > 100:
                    remaining = len(output_lines) - 100
                    print(f"   ... (还有 {remaining} 行)")
                print("   " + "-" * 76)
        
        # 显示性能指标
        print("\n" + "-" * 80)
        print("📈 性能指标")
        print("-" * 80)
        
        metrics = result.get('performance_metrics', {})
        if metrics:
            import json
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
        else:
            print("   暂无性能指标")
        
        # 保存结果到文件
        output_file = project_root / "test-results" / f"finance_tests_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
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
    sys.exit(analyze_tests_with_factory())
