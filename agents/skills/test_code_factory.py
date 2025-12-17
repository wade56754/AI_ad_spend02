#!/usr/bin/env python3
"""
代码工厂测试脚本

测试 SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY 完整流程
"""

import sys
import json
import logging
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_search_skill():
    """测试搜索 Skill"""
    print("\n" + "="*60)
    print("Phase 1: SEARCH (搜索)")
    print("="*60)

    from agents.skills.code_searcher_skill import CodeSearcherSkill

    searcher = CodeSearcherSkill(PROJECT_ROOT)

    # 测试需求
    requirement = "添加日报批量导出 Excel 功能"

    result = searcher.search(
        requirement=requirement,
        sources={"local_project": True, "code_library": True, "github": False},
        max_candidates=5
    )

    print(f"\n需求: {requirement}")
    print(f"成功: {result.get('success')}")

    if result.get('success'):
        candidates = result['data'].get('candidates', [])
        print(f"找到候选: {len(candidates)} 个")

        for i, c in enumerate(candidates[:3], 1):
            print(f"\n  [{i}] {c.get('id', 'N/A')}")
            print(f"      来源: {c.get('source', 'N/A')}")
            print(f"      路径: {c.get('path', 'N/A')}")
            print(f"      相关度: {c.get('relevance_score', 0)}")
            print(f"      原因: {c.get('match_reason', 'N/A')[:50]}...")
    else:
        print(f"错误: {result.get('error')}")

    return result


def test_selector_skill(search_result):
    """测试选型 Skill"""
    print("\n" + "="*60)
    print("Phase 2: SELECT (选型)")
    print("="*60)

    from agents.skills.code_selector_skill import CodeSelectorSkill
    from agents.skills.code_searcher_skill import SearchCandidate

    if not search_result.get('success') or not search_result['data'].get('candidates'):
        print("跳过: 没有候选代码")
        return None

    selector = CodeSelectorSkill()

    # 转换候选为对象
    candidates = []
    for c in search_result['data']['candidates']:
        candidates.append(SearchCandidate(
            id=c.get('id', ''),
            source=c.get('source', ''),
            path=c.get('path', ''),
            relevance_score=c.get('relevance_score', 0),
            snippet=c.get('snippet', ''),
            match_reason=c.get('match_reason', ''),
            tech_stack_match=c.get('tech_stack_match', 80),
            adaptation_hint=c.get('adaptation_hint'),
        ))

    requirement = "添加日报批量导出 Excel 功能"

    result = selector.select(
        candidates=candidates,
        requirement=requirement
    )

    print(f"\n成功: {result.get('success')}")

    if result.get('success'):
        selected = result['data'].get('selected', {})
        scores = result['data'].get('scores', {})

        print(f"\n选中: {selected.get('id', 'N/A')}")
        print(f"路径: {selected.get('path', 'N/A')}")
        print(f"\n评分:")
        print(f"  - 技术栈匹配: {scores.get('tech_stack', 0):.2f}")
        print(f"  - 功能覆盖度: {scores.get('coverage', 0):.2f}")
        print(f"  - 适配成本: {scores.get('adaptation_cost', 0):.2f}")
        print(f"  - 代码质量: {scores.get('quality', 0):.2f}")
        print(f"  - 总分: {scores.get('total', 0):.2f}")

        plan = result['data'].get('adaptation_plan', {})
        print(f"\n适配方案:")
        print(f"  - 预估复用率: {plan.get('estimated_adaptation_rate', 'N/A')}")
    else:
        print(f"错误: {result.get('error')}")

    return result


def test_adapter_skill(selection_result):
    """测试适配 Skill"""
    print("\n" + "="*60)
    print("Phase 3: ADAPT (适配)")
    print("="*60)

    from agents.skills.code_adapter_skill import CodeAdapterSkill
    from agents.skills.code_searcher_skill import SearchCandidate
    from agents.skills.code_selector_skill import AdaptationPlan

    if not selection_result or not selection_result.get('success'):
        print("跳过: 没有选中代码")
        return None

    adapter = CodeAdapterSkill(PROJECT_ROOT)

    selected = selection_result['data']['selected']
    plan_data = selection_result['data']['adaptation_plan']

    reference = SearchCandidate(
        id=selected.get('id', ''),
        source=selected.get('source', ''),
        path=selected.get('path', ''),
        relevance_score=selected.get('relevance_score', 0),
        snippet=selected.get('snippet', ''),
        match_reason=selected.get('match_reason', ''),
        tech_stack_match=selected.get('tech_stack_match', 80),
        adaptation_hint=selected.get('adaptation_hint'),
    )

    adaptation_plan = AdaptationPlan(
        base_code=plan_data.get('base_code', ''),
        source=plan_data.get('source', ''),
        estimated_adaptation_rate=plan_data.get('estimated_adaptation_rate', '80%'),
        adaptation_hint=plan_data.get('adaptation_hint'),
    )

    requirement = "添加日报批量导出 Excel 功能"

    result = adapter.adapt(
        reference=reference,
        requirement=requirement,
        adaptation_plan=adaptation_plan
    )

    print(f"\n成功: {result.get('success')}")

    if result.get('success'):
        adapted_files = result['data'].get('adapted_files', [])
        summary = result['data'].get('summary', {})

        print(f"适配文件数: {len(adapted_files)}")
        print(f"适配率: {summary.get('adaptation_rate', 'N/A')}")

        for f in adapted_files[:2]:
            print(f"\n  文件: {f.get('file_path', 'N/A')}")
            content = f.get('content', '')
            print(f"  内容预览: {content[:100]}..." if len(content) > 100 else f"  内容: {content}")
    else:
        print(f"错误: {result.get('error')}")

    return result


def test_assembler_skill(adaptation_result):
    """测试组装 Skill"""
    print("\n" + "="*60)
    print("Phase 4: ASSEMBLE (组装)")
    print("="*60)

    from agents.skills.code_assembler_skill import CodeAssemblerSkill, AdaptedFile

    if not adaptation_result or not adaptation_result.get('success'):
        print("跳过: 没有适配代码")
        return None

    assembler = CodeAssemblerSkill(PROJECT_ROOT)

    adapted_files = []
    for f in adaptation_result['data'].get('adapted_files', []):
        adapted_files.append(AdaptedFile(
            file_path=f.get('file_path', ''),
            content=f.get('content', ''),
            adaptations=[],
            source_attribution=None,
        ))

    requirement = "添加日报批量导出 Excel 功能"

    result = assembler.assemble(
        adapted_files=adapted_files,
        requirement=requirement,
        scope="backend"
    )

    print(f"\n成功: {result.get('success')}")

    if result.get('success'):
        module = result['data'].get('assembled_module', {})

        print(f"模块名: {module.get('name', 'N/A')}")
        print(f"文件数: {len(module.get('files', []))}")

        for f in module.get('files', [])[:3]:
            print(f"\n  文件: {f.get('path', 'N/A')}")
            print(f"  操作: {f.get('action', 'N/A')}")
    else:
        print(f"错误: {result.get('error')}")

    return result


def test_verifier_skill(assembly_result):
    """测试验证 Skill"""
    print("\n" + "="*60)
    print("Phase 5: VERIFY (验证)")
    print("="*60)

    from agents.skills.code_verifier_skill import CodeVerifierSkill, AssembledFile

    if not assembly_result or not assembly_result.get('success'):
        print("跳过: 没有组装代码")
        return None

    verifier = CodeVerifierSkill(PROJECT_ROOT)

    assembled_files = []
    module = assembly_result['data'].get('assembled_module', {})
    for f in module.get('files', []):
        assembled_files.append(AssembledFile(
            path=f.get('path', ''),
            content=f.get('content', ''),
            action=f.get('action', 'create'),
            dependencies=f.get('dependencies', []),
        ))

    requirement = "添加日报批量导出 Excel 功能"

    result = verifier.verify(
        assembled_files=assembled_files,
        requirement=requirement,
        auto_fix=True,
        max_fix_iterations=3
    )

    print(f"\n成功: {result.get('success')}")

    if result.get('data'):
        report = result['data'].get('verification_report', {})
        summary = report.get('summary', {})

        print(f"\n验证报告:")
        print(f"  - 总问题数: {summary.get('total_issues', 0)}")
        print(f"  - 已修复: {summary.get('fixed', 0)}")
        print(f"  - 剩余: {summary.get('remaining', 0)}")
        print(f"  - 通过: {summary.get('passed', False)}")

        remaining = result['data'].get('remaining_issues', [])
        if remaining:
            print(f"\n剩余问题 ({len(remaining)}):")
            for issue in remaining[:3]:
                print(f"  - [{issue.get('severity', 'N/A')}] {issue.get('file', 'N/A')}:{issue.get('line', 0)}")
                print(f"    {issue.get('message', 'N/A')[:60]}")

    return result


def test_full_pipeline():
    """测试完整流程"""
    print("\n" + "#"*60)
    print("#  代码工厂 v2.0 - 完整流程测试")
    print("#"*60)

    from agents.skills.code_factory_skill import code_factory_skill

    requirement = "添加日报批量导出 Excel 功能，支持按日期范围筛选"

    print(f"\n测试需求: {requirement}")
    print("-"*60)

    result = code_factory_skill(
        requirement=requirement,
        scope="backend",
        search_sources={
            "github": True,        # GitHub 可靠代码优先
            "code_library": True,  # 已验证参考代码
            "local_project": True, # 本项目AI生成代码 (优先级最低)
        },
        auto_fix_iterations=3,
        output_mode="files"
    )

    print("\n" + "="*60)
    print("最终结果")
    print("="*60)

    print(f"\n成功: {result.get('success')}")
    print(f"错误: {result.get('error', 'None')}")

    metadata = result.get('metadata', {})
    print(f"\n完成阶段: {metadata.get('phases_completed', [])}")
    print(f"总耗时: {metadata.get('total_time_ms', 0):.2f}ms")

    final_files = result.get('data', {}).get('final_files', [])
    print(f"\n生成文件数: {len(final_files)}")

    for f in final_files[:5]:
        print(f"\n  文件: {f.get('path', 'N/A')}")
        print(f"  操作: {f.get('action', 'N/A')}")
        print(f"  来源: {f.get('source_refs', [])}")

    return result


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  AI 代码工厂 v2.0 - 测试套件")
    print("="*60)
    print(f"\n项目路径: {PROJECT_ROOT}")

    # 选择测试模式
    mode = "full"  # "step" 或 "full"

    if mode == "step":
        # 分步测试
        print("\n>>> 分步测试模式")

        # Phase 1: Search
        search_result = test_search_skill()

        # Phase 2: Select
        selection_result = test_selector_skill(search_result)

        # Phase 3: Adapt
        adaptation_result = test_adapter_skill(selection_result)

        # Phase 4: Assemble
        assembly_result = test_assembler_skill(adaptation_result)

        # Phase 5: Verify
        verify_result = test_verifier_skill(assembly_result)

    else:
        # 完整流程测试
        print("\n>>> 完整流程测试模式")
        result = test_full_pipeline()

    print("\n" + "="*60)
    print("  测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
