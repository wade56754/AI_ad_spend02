"""
使用 AI 代码工厂审查所有 API
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.skills.code_factory.core.orchestrator import CodeFactoryOrchestrator

def review_all_apis():
    """审查所有 API 路由文件"""
    
    # API 文件列表
    api_files = [
        "backend/routers/ad_accounts.py",
        "backend/routers/ad_spend.py",
        "backend/routers/agents.py",
        "backend/routers/ai_analytics.py",
        "backend/routers/authentication.py",
        "backend/routers/channels.py",
        "backend/routers/daily_reports.py",
        "backend/routers/dashboard.py",
        "backend/routers/finance_profit.py",
        "backend/routers/finance_v2.py",
        "backend/routers/fund.py",
        "backend/routers/health.py",
        "backend/routers/import_jobs.py",
        "backend/routers/ledger.py",
        "backend/routers/monthly_settlements.py",
        "backend/routers/profit.py",
        "backend/routers/project_members.py",
        "backend/routers/project_templates.py",
        "backend/routers/projects.py",
        "backend/routers/reconciliation_control.py",
        "backend/routers/reconciliation.py",
        "backend/routers/reports.py",
        "backend/routers/settlements.py",
        "backend/routers/spend.py",
        "backend/routers/suppliers.py",
        "backend/routers/topup.py",
        "backend/routers/transfers.py",
        "backend/routers/users.py",
        "backend/routers/weekly_briefs.py",
        "backend/routers/weekly_reports.py",
    ]
    
    print("=" * 80)
    print("AI 代码工厂 - API 审查工作流")
    print("=" * 80)
    print(f"\n审查范围: {len(api_files)} 个 API 路由文件")
    print(f"工作流类型: code_review (代码审查)")
    print(f"执行代理: code-reviewer, security-auditor, performance-engineer")
    print("\n" + "=" * 80)
    
    # 创建编排器
    try:
        orchestrator = CodeFactoryOrchestrator()
        print("[OK] 代码工厂编排器初始化成功\n")
    except Exception as e:
        print(f"[ERROR] 代码工厂编排器初始化失败: {e}")
        print("\n提示: 如果使用模拟模式，将返回模拟审查结果")
        return
    
    # 构建审查需求
    requirement = f"""
审查所有 API 路由文件的代码质量、安全性和性能。

审查范围:
- 共 {len(api_files)} 个 API 路由文件
- 文件路径: backend/routers/

审查重点:
1. 代码质量:
   - 是否符合项目规范 (AGENTS.md, .cursorrules)
   - 错误处理是否完善
   - 输入验证是否充分
   - 依赖注入是否统一
   - 日志记录是否规范

2. 安全性:
   - 权限检查是否完整
   - 输入验证是否充分
   - SQL 注入风险
   - 敏感信息泄露风险
   - 认证授权是否正确

3. 性能:
   - N+1 查询问题
   - 数据库查询优化
   - 响应序列化优化
   - 缓存使用是否合理

4. SoT 合规性:
   - 是否符合 API_SOT.md v9.4
   - 错误码是否来自 ERROR_CODES_SOT.md v2.2
   - 状态机是否符合 STATE_MACHINE.md v2.8
   - 角色定义是否符合 AUTH_SPEC.md v2.1

请生成详细的审查报告，包括:
- 每个文件的问题列表 (P0/P1/P2)
- 具体的问题描述和位置
- 修复建议
- 总体评估
"""
    
    # 执行代码审查工作流
    print("[START] 开始执行代码审查工作流...\n")
    
    try:
        result = orchestrator.execute(
            requirement=requirement,
            workflow_type="code_review"
        )
        
        print("\n" + "=" * 80)
        print("审查结果")
        print("=" * 80)
        
        # 显示执行状态
        print(f"\n[STATUS] 执行状态: {result.get('status', 'unknown')}")
        
        # 显示执行结果
        execution_results = result.get('execution_results', [])
        if execution_results:
            print(f"\n执行了 {len(execution_results)} 个代理任务\n")
            for i, exec_result in enumerate(execution_results):
                agent_id = exec_result.get('agent_id', f'agent_{i}')
                success = exec_result.get('success', False)
                output = exec_result.get('output', '')
                error = exec_result.get('error', '')
                
                print(f"{'='*80}")
                print(f"代理: {agent_id}")
                print(f"{'='*80}")
                print(f"状态: {'[OK] 成功' if success else '[ERROR] 失败'}")
                
                if output:
                    print(f"\n输出:\n{output[:500]}...")  # 只显示前500字符
                
                if error:
                    print(f"\n[ERROR] 错误: {error}")
                
                if 'tokens_used' in exec_result:
                    print(f"\n指标:")
                    print(f"  - Token 使用: {exec_result.get('tokens_used', 'N/A')}")
                    print(f"  - 执行时间: {exec_result.get('execution_time', 'N/A')}s")
        else:
            # 如果没有 execution_results，尝试从 agents 字段获取
            agents_result = result.get('agents', {})
            if isinstance(agents_result, list):
                agents_dict = {}
                for i, agent_result in enumerate(agents_result):
                    agent_id = agent_result.get('agent_id', f'agent_{i}')
                    agents_dict[agent_id] = agent_result
                agents_result = agents_dict
            
            if agents_result:
                for agent_id, agent_result in agents_result.items():
                    print(f"\n{'='*80}")
                    print(f"代理: {agent_id}")
                    print(f"{'='*80}")
                    print(f"状态: {agent_result.get('status', 'unknown')}")
                    
                    if 'output' in agent_result:
                        print(f"\n输出:\n{agent_result['output']}")
                    
                    if 'error' in agent_result:
                        print(f"\n[ERROR] 错误: {agent_result['error']}")
        
        # 显示性能指标
        if 'metrics' in result:
            metrics = result['metrics']
            print(f"\n{'='*80}")
            print("总体性能指标")
            print(f"{'='*80}")
            print(f"  - 总 Token: {metrics.get('total_tokens', 'N/A')}")
            print(f"  - 平均时间: {metrics.get('avg_time', 'N/A')}s")
            print(f"  - 错误率: {metrics.get('error_rate', 'N/A')}%")
            print(f"  - 缓存命中率: {metrics.get('cache_hit_rate', 'N/A')}%")
        
        # 保存审查报告
        report_file = project_root / "docs" / "integration" / "API_REVIEW_REPORT.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# API 审查报告\n\n")
            f.write(f"生成时间: {result.get('timestamp', 'N/A')}\n\n")
            f.write(f"## 执行状态\n\n{result.get('status', 'unknown')}\n\n")
            
            # 优先使用 execution_results
            execution_results = result.get('execution_results', [])
            if execution_results:
                for exec_result in execution_results:
                    agent_id = exec_result.get('agent_id', 'unknown')
                    f.write(f"## {agent_id}\n\n")
                    f.write(f"状态: {'成功' if exec_result.get('success') else '失败'}\n\n")
                    if 'output' in exec_result:
                        f.write(f"{exec_result['output']}\n\n")
                    if 'error' in exec_result:
                        f.write(f"错误: {exec_result['error']}\n\n")
            else:
                # 回退到 agents 字段
                agents_result = result.get('agents', {})
                if isinstance(agents_result, list):
                    agents_dict = {}
                    for i, agent_result in enumerate(agents_result):
                        agent_id = agent_result.get('agent_id', f'agent_{i}')
                        agents_dict[agent_id] = agent_result
                    agents_result = agents_dict
                
                if agents_result:
                    for agent_id, agent_result in agents_result.items():
                        f.write(f"## {agent_id}\n\n")
                        if 'output' in agent_result:
                            f.write(f"{agent_result['output']}\n\n")
            
            if 'metrics' in result:
                f.write("## 性能指标\n\n")
                f.write(f"- 总 Token: {result['metrics'].get('total_tokens', 'N/A')}\n")
                f.write(f"- 平均时间: {result['metrics'].get('avg_time', 'N/A')}s\n")
                f.write(f"- 错误率: {result['metrics'].get('error_rate', 'N/A')}%\n")
        
        print(f"\n[SAVED] 审查报告已保存到: {report_file}")
        
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    review_all_apis()

