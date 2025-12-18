"""
代码工厂 v3.0 集成测试
"""

import sys
import io
from pathlib import Path

# 设置 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 使用 ASCII 兼容的符号
OK = "[OK]"
FAIL = "[FAIL]"

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        from agents.skills.code_factory import (
            # 核心
            TaskList, Task, TaskStatus,
            SecurityValidator, SoTComplianceChecker,
            SessionManager, SessionType,
            CodeFactory, FactoryConfig,
            # 子 Skill
            CodeSearcher, SearchResult,
            CodeSelector, SelectionResult,
            CodeAdapter, AdaptResult,
            CodeAssembler, AssembleResult,
            CodeVerifier, VerifyResult, VerifyDecision,
        )
        print(f"{OK} 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"{FAIL} 导入失败: {e}")
        return False


def test_searcher():
    """测试搜索器"""
    print("\n" + "=" * 60)
    print("测试 2: CodeSearcher (SEARCH 阶段)")
    print("=" * 60)

    from agents.skills.code_factory import CodeSearcher

    searcher = CodeSearcher(
        project_root=project_root,
        code_library_path=project_root / "code-library",
        enable_github=False,
    )

    # 测试搜索
    result = searcher.search(
        requirement="实现用户充值 API",
        sources={"local_project": True, "code_library": True, "github": False},
        max_candidates=3,
    )

    print(f"  搜索成功: {result.success}")
    print(f"  候选数量: {len(result.candidates)}")
    print(f"  统计: 本地 {result.stats.local_matches}, 资料库 {result.stats.library_matches}")

    if result.candidates:
        print(f"  最佳候选: {result.candidates[0].path}")

    return result.success


def test_selector():
    """测试选型器"""
    print("\n" + "=" * 60)
    print("测试 3: CodeSelector (SELECT 阶段)")
    print("=" * 60)

    from agents.skills.code_factory import CodeSelector, SearchCandidate

    selector = CodeSelector(project_root=project_root)

    # 创建模拟候选
    candidates = [
        SearchCandidate(
            id="test-1",
            source="local_project",
            path="backend/services/topup_service.py",
            snippet="class TopupService:\n    def create_topup(self, ...):",
            relevance_score=85,
            tech_stack_match=90,
            language="python",
            full_content="class TopupService:\n    def create_topup(self, amount: float):\n        pass",
            match_reason="关键词匹配: topup, service",
        ),
        SearchCandidate(
            id="test-2",
            source="code_library",
            path="patterns/crud_service.py",
            snippet="class CRUDService:\n    def create(self, ...):",
            relevance_score=70,
            tech_stack_match=80,
            language="python",
            full_content="class CRUDService:\n    def create(self, data: dict):\n        pass",
            match_reason="通用 CRUD 模式",
        ),
    ]

    result = selector.select(
        candidates=candidates,
        requirement="实现用户充值 API",
    )

    print(f"  选型成功: {result.success}")
    if result.selected:
        print(f"  选中: {result.selected.path}")
        print(f"  总分: {result.scores.total:.1f}")
        print(f"    - 技术栈: {result.scores.tech_stack_match:.1f}")
        print(f"    - 功能覆盖: {result.scores.feature_coverage:.1f}")
        print(f"    - 适配成本: {result.scores.adaptation_cost:.1f}")
        print(f"    - 代码质量: {result.scores.code_quality:.1f}")

    return result.success


def test_adapter():
    """测试适配器"""
    print("\n" + "=" * 60)
    print("测试 4: CodeAdapter (ADAPT 阶段)")
    print("=" * 60)

    from agents.skills.code_factory import CodeAdapter, SearchCandidate, AdaptationPlan

    adapter = CodeAdapter(project_root=project_root)

    # 创建模拟候选和适配方案
    candidate = SearchCandidate(
        id="test-1",
        source="code_library",
        path="patterns/crud_service.py",
        snippet="",
        relevance_score=80,
        tech_stack_match=85,
        language="python",
        match_reason="用户服务模式匹配",
        full_content='''
class UserService:
    """用户服务"""

    class Config:
        orm_mode = True

    @validator("email")
    def validate_email(cls, v):
        return v

    def get_user(self, user_id: int):
        return session.query(User).filter_by(id=user_id).first()

    def create_user(self, data):
        return {"success": True, "data": data}
''',
    )

    plan = AdaptationPlan(
        base_code=candidate.path,
        source=candidate.source,
        modifications_needed=[],
        estimated_adaptation_rate="75%",
    )

    result = adapter.adapt(
        candidate=candidate,
        adaptation_plan=plan,
        requirement="实现用户服务",
    )

    print(f"  适配成功: {result.success}")
    if result.adapted_files:
        af = result.adapted_files[0]
        print(f"  目标文件: {af.file_path}")
        print(f"  适配项数: {len(af.adaptations)}")
        if result.summary:
            print(f"  按类型统计: {result.summary.by_type}")

        # 显示部分适配
        for a in af.adaptations[:3]:
            print(f"    [{a.type}] {a.reason}")

    return result.success


def test_assembler():
    """测试组装器"""
    print("\n" + "=" * 60)
    print("测试 5: CodeAssembler (ASSEMBLE 阶段)")
    print("=" * 60)

    from agents.skills.code_factory import CodeAssembler, AdaptedFile

    assembler = CodeAssembler(project_root=project_root)

    # 使用空适配文件测试模板生成
    result = assembler.assemble(
        adapted_files=[],
        requirement="实现充值记录查询 API",
        scope="backend",
        include_tests=True,
    )

    print(f"  组装成功: {result.success}")
    if result.module:
        print(f"  模块名: {result.module.name}")
        print(f"  文件数: {len(result.module.files)}")
        for f in result.module.files:
            print(f"    - {f.path} ({f.action})")

    if result.repo_map:
        print(f"  新建文件: {len(result.repo_map.new_files)}")

    if result.integration_guide:
        print(f"  集成步骤: {len(result.integration_guide.steps)}")

    return result.success


def test_verifier():
    """测试验证器"""
    print("\n" + "=" * 60)
    print("测试 6: CodeVerifier (VERIFY 阶段)")
    print("=" * 60)

    from agents.skills.code_factory import CodeVerifier, AdaptedFile, VerifyDecision

    verifier = CodeVerifier(
        project_root=project_root,
        auto_fix=True,
        strict_mode=False,
    )

    # 测试代码
    test_code = '''
"""测试服务"""
from typing import Optional

class TestService:
    """测试服务类"""

    def __init__(self):
        self.data = {}

    def get_item(self, item_id: int) -> Optional[dict]:
        """获取项目"""
        return self.data.get(item_id)

    def create_item(self, data: dict) -> dict:
        """创建项目"""
        item_id = len(self.data) + 1
        self.data[item_id] = data
        return {"id": item_id, **data}
'''

    adapted_files = [
        AdaptedFile(
            file_path="backend/services/test_service.py",
            content=test_code,
            adaptations=[],
            source_attribution=None,
        )
    ]

    result = verifier.verify(
        adapted_files=adapted_files,
        requirement="测试验证器",
    )

    print(f"  验证成功: {result.success}")
    print(f"  决策: {result.decision.value}")
    print(f"  统计: {result.summary}")

    for fr in result.file_results:
        status = OK if fr.decision in (VerifyDecision.APPROVED, VerifyDecision.FIX_APPLIED) else FAIL
        print(f"    {status} {fr.file_path}: {fr.decision.value}")
        if fr.issues:
            for issue in fr.issues[:3]:
                print(f"      - [{issue.code}] L{issue.line}: {issue.message}")

    return result.success


def test_factory_config():
    """测试工厂配置"""
    print("\n" + "=" * 60)
    print("测试 7: CodeFactory 配置与初始化")
    print("=" * 60)

    from agents.skills.code_factory import CodeFactory, FactoryConfig

    config = FactoryConfig(
        project_dir=project_root,
        search_sources={"local_project": True, "code_library": True, "github": False},
        auto_continue=False,
        enable_security=True,
        enable_sot_check=True,
        output_mode="preview",
        verbose=True,
    )

    factory = CodeFactory(config)

    print(f"  版本: {factory.VERSION}")
    print(f"  项目目录: {factory.project_dir}")
    print(f"  子 Skill 状态:")
    print(f"    - Searcher: {OK if factory.searcher else FAIL}")
    print(f"    - Selector: {OK if factory.selector else FAIL}")
    print(f"    - Adapter: {OK if factory.adapter else FAIL}")
    print(f"    - Assembler: {OK if factory.assembler else FAIL}")
    print(f"    - Verifier: {OK if factory.verifier else FAIL}")
    print(f"  阶段处理器: {list(factory.phase_handlers.keys())}")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI 代码工厂 v3.0 集成测试")
    print("=" * 60)

    tests = [
        ("模块导入", test_imports),
        ("搜索器", test_searcher),
        ("选型器", test_selector),
        ("适配器", test_adapter),
        ("组装器", test_assembler),
        ("验证器", test_verifier),
        ("工厂配置", test_factory_config),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  {FAIL} 测试异常: {e}")

    # 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    passed_count = sum(1 for _, p, _ in results if p)
    total_count = len(results)

    for name, passed, error in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {name}")
        if error:
            print(f"         错误: {error}")

    print(f"\n总计: {passed_count}/{total_count} 通过")

    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
