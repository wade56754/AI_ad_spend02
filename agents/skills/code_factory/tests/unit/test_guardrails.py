"""
Guardrails 模块单元测试

基准文档: MASTER.md v4.6
版本: v4.2
"""

import pytest
from pathlib import Path

from agents.skills.code_factory.guardrails.recovery_loop import (
    EditGuardrails,
    EditResult,
    EditStatus,
)
from agents.skills.code_factory.guardrails.stats_tracker import GuardrailsStats


class TestEditGuardrails:
    """编辑守卫测试"""

    def test_check_valid_python_code(self, temp_dir):
        """测试有效 Python 代码检查"""
        guardrails = EditGuardrails(max_retries=3)

        valid_code = '''
def hello():
    return "world"
'''
        errors = guardrails._check_content(valid_code, ".py")
        assert len(errors) == 0

    def test_check_invalid_python_syntax(self, temp_dir):
        """测试无效 Python 语法检查"""
        guardrails = EditGuardrails(max_retries=3)

        invalid_code = '''
def hello(
    return "world"
'''
        errors = guardrails._check_content(invalid_code, ".py")
        assert len(errors) > 0

    def test_apply_edit_success(self, temp_dir):
        """测试成功编辑"""
        guardrails = EditGuardrails(max_retries=3)

        test_file = temp_dir / "test.py"
        new_content = '''
def hello():
    return "world"
'''
        result = guardrails.apply_edit(test_file, new_content)

        assert result.status == EditStatus.SUCCESS
        assert result.success is True

    def test_apply_edit_rejects_invalid_code(self, temp_dir):
        """测试拒绝无效代码"""
        guardrails = EditGuardrails(
            max_retries=1,  # 只尝试一次
        )

        test_file = temp_dir / "test.py"
        invalid_code = '''
def hello(
    return "world"
'''
        result = guardrails.apply_edit(test_file, invalid_code)

        assert result.status == EditStatus.FAILED
        assert len(result.errors) > 0

    def test_check_non_python_file(self, temp_dir):
        """测试非 Python 文件"""
        guardrails = EditGuardrails(max_retries=3)

        content = "some random text"
        errors = guardrails._check_content(content, ".txt")

        # 非 Python 文件不检查
        assert len(errors) == 0


class TestGuardrailsStats:
    """统计追踪器测试"""

    def test_record_success(self):
        """测试记录成功"""
        stats = GuardrailsStats()
        stats.record_success("test.py", first_try=True)

        assert stats.first_success == 1
        assert stats.total == 1

    def test_record_failure(self):
        """测试记录失败"""
        stats = GuardrailsStats()
        stats.record_failure("test.py", attempts=3, errors=["syntax error"])

        assert stats.failed == 1
        assert stats.total == 1

    def test_record_recovery(self):
        """测试记录恢复"""
        stats = GuardrailsStats()
        stats.record_success("test.py", first_try=False)  # 恢复成功

        assert stats.recovered == 1
        assert stats.total == 1

    def test_success_rate_calculation(self):
        """测试成功率计算"""
        stats = GuardrailsStats()
        stats.record_success("a.py", first_try=True)
        stats.record_success("b.py", first_try=True)
        stats.record_failure("c.py", attempts=3, errors=["error"])

        # 成功率 = (first_success + recovered) / total * 100
        assert stats.success_rate == pytest.approx(200/3, rel=0.01)

    def test_empty_stats(self):
        """测试空统计"""
        stats = GuardrailsStats()

        assert stats.total == 0
        assert stats.success_rate == 0.0

    def test_reset_stats(self):
        """测试重置统计"""
        stats = GuardrailsStats()
        stats.record_success("test.py", first_try=True)
        stats.reset()

        assert stats.total == 0

    def test_to_dict(self):
        """测试转字典"""
        stats = GuardrailsStats()
        stats.record_success("test.py", first_try=True)

        data = stats.to_dict()
        assert "total" in data
        assert "success_rate" in data
