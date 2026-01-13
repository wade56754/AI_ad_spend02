"""
Hooks 集成测试

测试 Claude Code 增强层的核心功能:
1. Memory Bank 初始化和持久化
2. Session Context 保存/加载
3. Rules 生成
4. Pre-commit 检查
5. Fast Verify

版本: v7.0
"""

import pytest
import tempfile
from pathlib import Path
import json

from agents.skills.code_factory.context import (
    MemoryBank,
    SessionContext,
    ProgressTracker,
)
from agents.skills.code_factory.hooks import (
    RulesGenerator,
    PreCommitHook,
    FastVerifier,
    quick_verify,
)


class TestMemoryBank:
    """Memory Bank 测试"""
    
    @pytest.fixture
    def temp_memory_dir(self):
        """创建临时 memory 目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_initialization(self, temp_memory_dir):
        """测试初始化"""
        mb = MemoryBank(temp_memory_dir)
        
        # 检查模板文件创建
        assert (temp_memory_dir / "project-brief.md").exists()
        assert (temp_memory_dir / "progress.md").exists()
        assert (temp_memory_dir / "current-task.md").exists()
    
    def test_update_progress(self, temp_memory_dir):
        """测试进度更新"""
        mb = MemoryBank(temp_memory_dir)
        
        mb.update_progress("task-001", "completed", "实现了用户认证")
        
        progress = mb.get_progress_summary()
        assert "task-001" in progress
        assert "completed" in progress
    
    def test_log_decision(self, temp_memory_dir):
        """测试决策记录"""
        mb = MemoryBank(temp_memory_dir)
        
        mb.log_decision(
            decision="使用 TDD 开发",
            reason="提高代码质量",
            alternatives=["先写代码后测试"],
        )
        
        decisions = mb.get_decisions()
        assert "使用 TDD 开发" in decisions
        assert "提高代码质量" in decisions
    
    def test_set_current_task(self, temp_memory_dir):
        """测试设置当前任务"""
        mb = MemoryBank(temp_memory_dir)
        
        mb.set_current_task(
            task_id="task-002",
            title="实现日报提交",
            description="添加日报提交 API",
            steps=["写测试", "实现接口", "验证"],
        )
        
        current = (temp_memory_dir / "current-task.md").read_text(encoding="utf-8")
        assert "task-002" in current
        assert "实现日报提交" in current


class TestSessionContext:
    """Session Context 测试"""
    
    @pytest.fixture
    def temp_session_dir(self):
        """创建临时 session 目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "context.json"
    
    def test_create_new_session(self, temp_session_dir):
        """测试创建新会话"""
        session = SessionContext.load_or_create(temp_session_dir)
        
        assert session.session_id is not None
        assert len(session.session_id) == 8
        assert session.started_at is not None
    
    def test_save_and_load(self, temp_session_dir):
        """测试保存和加载"""
        # 创建并保存
        session1 = SessionContext.load_or_create(temp_session_dir)
        session1.current_task = "test-task"
        session1.completed_steps = ["step1"]
        session1.save(temp_session_dir)
        
        # 重新加载
        session2 = SessionContext.load(temp_session_dir)
        
        assert session2 is not None
        assert session2.session_id == session1.session_id
        assert session2.current_task == "test-task"
        assert "step1" in session2.completed_steps
    
    def test_start_task(self, temp_session_dir):
        """测试开始任务"""
        session = SessionContext.load_or_create(temp_session_dir)
        
        session.start_task(
            task_id="task-001",
            title="测试任务",
            steps=["步骤1", "步骤2", "步骤3"],
        )
        
        assert session.current_task == "task-001"
        assert len(session.pending_steps) == 3
        assert len(session.completed_steps) == 0
    
    def test_complete_step(self, temp_session_dir):
        """测试完成步骤"""
        session = SessionContext.load_or_create(temp_session_dir)
        session.start_task("task-001", "测试", ["步骤1", "步骤2"])
        
        session.complete_step("步骤1", "完成了步骤1")
        
        assert "步骤1" not in session.pending_steps
        assert len(session.completed_steps) == 1


class TestRulesGenerator:
    """Rules 生成器测试"""
    
    @pytest.fixture
    def temp_rules_path(self):
        """创建临时 rules 路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "rules.md"
    
    def test_generate_content(self, temp_rules_path):
        """测试生成内容"""
        generator = RulesGenerator(temp_rules_path)
        content = generator.generate()
        
        # 检查必要内容
        assert "TDD" in content
        assert "SoT" in content
        assert "admin" in content
        assert "raw_submitted" in content
        assert "supervisor" in content  # 禁止角色
    
    def test_save_file(self, temp_rules_path):
        """测试保存文件"""
        generator = RulesGenerator(temp_rules_path)
        saved_path = generator.save()
        
        assert saved_path.exists()
        content = saved_path.read_text(encoding="utf-8")
        assert len(content) > 0


class TestFastVerifier:
    """快速验证器测试"""
    
    def test_verify_clean_code(self):
        """测试验证干净代码"""
        verifier = FastVerifier()
        
        clean_code = '''
def get_user(user_id: int):
    """获取用户"""
    return User.query.get(user_id)
'''
        
        issues = verifier.verify_content(clean_code)
        assert len(issues) == 0
    
    def test_detect_forbidden_role(self):
        """测试检测禁止角色"""
        verifier = FastVerifier()
        
        bad_code = '''
user.role = "supervisor"
'''
        
        issues = verifier.verify_content(bad_code)
        assert len(issues) > 0
        assert any("supervisor" in str(i) for i in issues)
    
    def test_detect_forbidden_state(self):
        """测试检测禁止状态"""
        verifier = FastVerifier()
        
        bad_code = '''
report.status = "draft"
'''
        
        issues = verifier.verify_content(bad_code)
        assert len(issues) > 0
        assert any("draft" in str(i) for i in issues)
    
    def test_detect_balance_modification(self):
        """测试检测余额修改"""
        verifier = FastVerifier()
        
        bad_code = '''
account.balance -= 100
'''
        
        issues = verifier.verify_content(bad_code)
        assert len(issues) > 0
        assert any("balance" in str(i) for i in issues)
    
    def test_skip_deprecated_definitions(self):
        """测试跳过废弃定义"""
        verifier = FastVerifier()
        
        # 这种代码是定义禁止列表，应该被跳过
        code = '''
DEPRECATED_ROLES = ["supervisor", "manager"]
FORBIDDEN_STATES = {"draft", "pending"}
'''
        
        issues = verifier.verify_content(code)
        # 定义禁止列表的代码不应该被标记
        assert len(issues) == 0


class TestPreCommitHook:
    """Pre-commit Hook 测试"""
    
    def test_should_check_python_files(self):
        """测试应该检查 Python 文件"""
        hook = PreCommitHook()
        
        assert hook.should_check_file("backend/services/user.py")
        assert hook.should_check_file("frontend/src/App.tsx")
        assert not hook.should_check_file("README.md")
        assert not hook.should_check_file("package.json")
    
    def test_skip_test_files(self):
        """测试跳过测试文件"""
        hook = PreCommitHook()
        
        assert not hook.should_check_file("tests/test_user.py")
        assert not hook.should_check_file("backend/user_test.py")
        assert not hook.should_check_file("conftest.py")


class TestProgressTracker:
    """进度追踪器测试"""
    
    @pytest.fixture
    def temp_progress_file(self):
        """创建临时进度文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "progress.md"
    
    def test_start_task(self, temp_progress_file):
        """测试开始任务"""
        tracker = ProgressTracker(temp_progress_file)
        
        tracker.start_task("task-001", "实现用户认证")
        
        content = tracker.get_progress()
        assert "task-001" in content
        assert "进行中" in content
    
    def test_complete_task(self, temp_progress_file):
        """测试完成任务"""
        tracker = ProgressTracker(temp_progress_file)
        
        tracker.complete_task(
            "task-001",
            "用户认证功能已完成",
            files_changed=["auth.py", "auth_test.py"],
        )
        
        content = tracker.get_progress()
        assert "task-001" in content
        assert "完成" in content
    
    def test_generate_report(self, temp_progress_file):
        """测试生成报告"""
        tracker = ProgressTracker(temp_progress_file)
        
        tracker.start_task("task-001", "任务1")
        tracker.complete_task("task-001", "完成")
        tracker.block_task("task-002", "依赖未就绪")
        
        report = tracker.generate_report()
        
        assert report["completed"] >= 1
        assert report["blocked"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
