"""
编辑防护 + 错误恢复循环 (SWE-agent 风格)

基准文档: MASTER.md v4.6
版本: v4.2

功能:
- 编辑前进行语法和 lint 检查
- 自动修复常见问题
- 最多重试 N 次
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable
from enum import Enum
import subprocess
import ast
import shutil

from .stats_tracker import GuardrailsStats


class EditStatus(Enum):
    """编辑状态"""
    SUCCESS = "success"          # 首次成功
    RECOVERED = "recovered"      # 恢复成功
    FAILED = "failed"           # 最终失败


@dataclass
class EditResult:
    """编辑结果"""
    success: bool
    status: EditStatus
    attempts: int
    errors: List[str] = field(default_factory=list)
    original_content: Optional[str] = None


class EditGuardrails:
    """编辑防护器 - 编辑前检查，失败自动修复"""

    def __init__(
        self,
        max_retries: int = 3,
        enable_ruff: bool = True,
        enable_ast: bool = True,
        backup_on_failure: bool = True,
    ):
        """初始化

        Args:
            max_retries: 最大重试次数
            enable_ruff: 是否启用 ruff 检查
            enable_ast: 是否启用 ast 语法检查
            backup_on_failure: 失败时是否恢复原内容
        """
        self.max_retries = max_retries
        self.enable_ruff = enable_ruff
        self.enable_ast = enable_ast
        self.backup_on_failure = backup_on_failure
        self.stats = GuardrailsStats()

        # 检查 ruff 是否可用
        self._ruff_available = self._check_ruff()

    def _check_ruff(self) -> bool:
        """检查 ruff 是否可用"""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def apply_edit(
        self,
        file_path: Path,
        content: str,
        backup: bool = True,
    ) -> EditResult:
        """应用编辑

        Args:
            file_path: 文件路径
            content: 新内容
            backup: 是否备份原文件

        Returns:
            EditResult: 编辑结果
        """
        file_path = Path(file_path)

        # 读取原内容 (用于回滚)
        original_content = None
        if backup and file_path.exists():
            original_content = file_path.read_text(encoding="utf-8")

        current_content = content

        for attempt in range(self.max_retries):
            # 检查代码
            errors = self._check_content(current_content, file_path.suffix)

            if not errors:
                # 检查通过，写入文件
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(current_content, encoding="utf-8")

                if attempt == 0:
                    self.stats.record_success(str(file_path), first_try=True)
                    return EditResult(
                        success=True,
                        status=EditStatus.SUCCESS,
                        attempts=1,
                        original_content=original_content,
                    )
                else:
                    self.stats.record_success(str(file_path), first_try=False)
                    return EditResult(
                        success=True,
                        status=EditStatus.RECOVERED,
                        attempts=attempt + 1,
                        original_content=original_content,
                    )

            # 尝试自动修复
            if attempt < self.max_retries - 1:
                fixed_content = self._auto_fix(current_content)
                if fixed_content != current_content:
                    current_content = fixed_content
                else:
                    # 无法修复，继续尝试
                    pass

        # 所有重试都失败
        self.stats.record_failure(str(file_path), self.max_retries, errors)

        # 回滚原内容
        if self.backup_on_failure and original_content is not None:
            file_path.write_text(original_content, encoding="utf-8")

        return EditResult(
            success=False,
            status=EditStatus.FAILED,
            attempts=self.max_retries,
            errors=errors,
            original_content=original_content,
        )

    def _check_content(self, content: str, suffix: str) -> List[str]:
        """检查内容

        Args:
            content: 文件内容
            suffix: 文件后缀

        Returns:
            错误列表 (空表示通过)
        """
        errors = []

        # 只检查 Python 文件
        if suffix != ".py":
            return errors

        # 1. AST 语法检查
        if self.enable_ast:
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"SyntaxError: {e.msg} (line {e.lineno})")
                return errors  # 语法错误优先返回

        # 2. Ruff lint 检查
        if self.enable_ruff and self._ruff_available:
            try:
                result = subprocess.run(
                    ["ruff", "check", "--output-format", "concise", "-"],
                    input=content,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0 and result.stdout:
                    # 只取前 5 个错误
                    lint_errors = result.stdout.strip().split("\n")[:5]
                    errors.extend(lint_errors)
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        return errors

    def _auto_fix(self, content: str) -> str:
        """自动修复

        Args:
            content: 原内容

        Returns:
            修复后的内容
        """
        if not self._ruff_available:
            return content

        try:
            # 使用 ruff 自动修复
            result = subprocess.run(
                ["ruff", "check", "--fix", "--unsafe-fixes", "-"],
                input=content,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # ruff --fix 输出修复后的内容到 stdout
            if result.stdout:
                return result.stdout
            return content
        except Exception:
            return content

    def check_file(self, file_path: Path) -> List[str]:
        """检查文件

        Args:
            file_path: 文件路径

        Returns:
            错误列表
        """
        if not file_path.exists():
            return [f"文件不存在: {file_path}"]

        content = file_path.read_text(encoding="utf-8")
        return self._check_content(content, file_path.suffix)

    def validate_before_commit(self, files: List[Path]) -> List[str]:
        """提交前验证

        Args:
            files: 文件列表

        Returns:
            所有错误
        """
        all_errors = []
        for file_path in files:
            if file_path.suffix == ".py":
                errors = self.check_file(file_path)
                if errors:
                    all_errors.extend([f"{file_path}: {e}" for e in errors])
        return all_errors

    def get_stats(self) -> GuardrailsStats:
        """获取统计"""
        return self.stats

    def reset_stats(self):
        """重置统计"""
        self.stats.reset()
