"""
auto_fix_loop.py - 自动修复循环机制

对齐 AI_CODE_FACTORY_DEV_GUIDE_v2.0 Section 7.5:
- 最多 2 轮自动修复
- 第 3 次失败 → 生成 FAILURE_REPORT
- 支持 pytest 执行和结果分析

自动修复流程:
┌─────────────────────────────────────────────────────────────┐
│                    自动修复 Loop                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Round 1: 分析失败 → 生成补丁 → 重跑测试                     │
│           (修明显 bug / 漏测)                                │
│                    │                                         │
│                    ▼ 还失败?                                 │
│  Round 2: 分析失败 → 生成补丁 → 重跑测试                     │
│           (补细节或小逻辑错误)                               │
│                    │                                         │
│                    ▼ 还失败?                                 │
│  停止! 生成 FAILURE_REPORT_xxx.md                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import subprocess
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class FixRoundStatus(str, Enum):
    """修复轮次状态"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """测试执行结果"""
    passed: bool
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    error_tests: int = 0
    failures: List[str] = field(default_factory=list)  # 失败用例名称
    errors: List[str] = field(default_factory=list)  # 错误信息
    output: str = ""  # pytest 原始输出
    duration_seconds: float = 0.0


@dataclass
class FixRound:
    """单轮修复记录"""
    round_num: int
    status: FixRoundStatus
    gen_result: Optional[Dict[str, Any]] = None
    test_result: Optional[TestResult] = None
    changes_made: Dict[str, str] = field(default_factory=dict)
    fix_actions: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


@dataclass
class AutoFixResult:
    """自动修复流程结果"""
    success: bool
    rounds_executed: int
    max_rounds: int
    final_test_passed: bool
    rounds: List[FixRound] = field(default_factory=list)
    files_generated: Dict[str, str] = field(default_factory=dict)
    failure_report_path: Optional[str] = None
    summary: str = ""


class AutoFixLoop:
    """
    自动修复循环执行器

    遵循 AI_CODE_FACTORY_DEV_GUIDE_v2.0 规范:
    - 最多 2 轮自动修复 (MAX_ROUNDS = 2)
    - 每轮: 分析失败 → 生成补丁 → 重跑测试
    - 第 3 次失败 → 停止并生成 FAILURE_REPORT

    使用示例:
        loop = AutoFixLoop(base_path, code_agent, test_files)
        result = loop.execute(task, target_files)

        if not result.success:
            # 自动生成了 FAILURE_REPORT
            print(f"Failure report: {result.failure_report_path}")
    """

    # 最大修复轮次 (对齐开发指南: 最多 2 轮)
    MAX_ROUNDS = 2

    def __init__(
        self,
        base_path: Path,
        code_agent: Any,  # BEAgent or FEAgent
        test_files: List[str],
        reports_dir: Optional[Path] = None,
    ):
        """
        初始化自动修复循环

        Args:
            base_path: 项目根路径
            code_agent: 代码生成 Agent (BEAgent 或 FEAgent)
            test_files: 测试文件路径列表
            reports_dir: 报告输出目录 (默认: docs/reports/)
        """
        self.base_path = base_path
        self.code_agent = code_agent
        self.test_files = test_files
        self.reports_dir = reports_dir or (base_path / "docs" / "reports")
        self.rounds: List[FixRound] = []

    def execute(
        self,
        task: str,
        target_files: List[str],
        initial_context: Optional[str] = None,
    ) -> AutoFixResult:
        """
        执行自动修复循环

        Args:
            task: 任务描述
            target_files: 目标文件列表
            initial_context: 初始上下文 (可选)

        Returns:
            AutoFixResult 包含执行结果和可能的失败报告
        """
        logger.info(f"[AutoFix] Starting auto-fix loop: max_rounds={self.MAX_ROUNDS}")

        all_changes: Dict[str, str] = {}
        fix_context: List[str] = []
        if initial_context:
            fix_context.append(initial_context)

        final_test_passed = False
        last_test_result: Optional[TestResult] = None

        for round_num in range(1, self.MAX_ROUNDS + 2):  # +1 for initial, +1 for final attempt
            if round_num > self.MAX_ROUNDS + 1:
                break  # 超过最大轮次

            round_record = FixRound(
                round_num=round_num,
                status=FixRoundStatus.PENDING,
                started_at=datetime.now(),
            )

            logger.info(f"[AutoFix] Round {round_num}/{self.MAX_ROUNDS + 1}")

            # Step 1: 生成/修复代码
            gen_task = self._build_task_with_context(task, fix_context)
            gen_request = {
                "task": gen_task,
                "target_files": target_files,
            }

            logger.info(f"[AutoFix] Round {round_num}: Generating code")
            gen_result = self.code_agent.handle_request(gen_request)
            round_record.gen_result = gen_result

            if not gen_result.get("success", False):
                logger.warning(f"[AutoFix] Round {round_num}: Code generation failed")
                round_record.status = FixRoundStatus.FAILED
                round_record.ended_at = datetime.now()
                self.rounds.append(round_record)

                fix_context.append(
                    f"Round {round_num} generation failed: {gen_result.get('error')}"
                )
                continue

            # 收集生成的代码
            changes = gen_result.get("data", {}).get("changes", {})
            all_changes.update(changes)
            round_record.changes_made = changes

            # Step 2: 运行测试
            logger.info(f"[AutoFix] Round {round_num}: Running tests")
            test_result = self._run_pytest()
            round_record.test_result = test_result
            last_test_result = test_result

            if test_result.passed:
                logger.info(f"[AutoFix] Round {round_num}: Tests PASSED!")
                round_record.status = FixRoundStatus.SUCCESS
                round_record.ended_at = datetime.now()
                self.rounds.append(round_record)
                final_test_passed = True
                break
            else:
                logger.warning(
                    f"[AutoFix] Round {round_num}: Tests FAILED "
                    f"({test_result.failed_tests} failures, {test_result.error_tests} errors)"
                )
                round_record.status = FixRoundStatus.FAILED
                round_record.ended_at = datetime.now()
                self.rounds.append(round_record)

                # 添加失败信息到修复上下文
                fix_hints = self._analyze_failures(test_result)
                fix_context.extend(fix_hints)
                round_record.fix_actions = fix_hints

        # 生成结果
        result = AutoFixResult(
            success=final_test_passed,
            rounds_executed=len(self.rounds),
            max_rounds=self.MAX_ROUNDS,
            final_test_passed=final_test_passed,
            rounds=self.rounds,
            files_generated=all_changes,
        )

        # 如果失败，生成 FAILURE_REPORT
        if not final_test_passed:
            report_path = self._generate_failure_report(
                task=task,
                target_files=target_files,
                test_result=last_test_result,
            )
            result.failure_report_path = str(report_path)
            result.summary = f"Auto-fix exhausted {len(self.rounds)} rounds without passing tests"
            logger.warning(f"[AutoFix] Failed - report generated: {report_path}")
        else:
            result.summary = f"Auto-fix succeeded in {len(self.rounds)} round(s)"
            logger.info(f"[AutoFix] Success - {result.summary}")

        return result

    def _build_task_with_context(self, task: str, fix_context: List[str]) -> str:
        """构建带修复上下文的任务描述"""
        if not fix_context:
            return task

        # 只保留最近 3 条修复提示
        recent_hints = fix_context[-3:]
        hints_block = "\n".join(f"- {hint}" for hint in recent_hints)

        return f"""{task}

[Auto-Fix Context]
Previous issues to address:
{hints_block}

Please fix these issues while maintaining SoT compliance."""

    def _run_pytest(self) -> TestResult:
        """
        执行 pytest 测试

        Returns:
            TestResult 包含测试执行结果
        """
        if not self.test_files:
            logger.warning("[AutoFix] No test files specified, skipping pytest")
            return TestResult(passed=True)

        # 构建 pytest 命令
        cmd = [
            "python", "-m", "pytest",
            "-v",
            "--tb=short",
            "-q",
        ]
        cmd.extend(str(self.base_path / f) for f in self.test_files)

        logger.debug(f"[AutoFix] Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.base_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
            )

            # 解析输出
            output = result.stdout + result.stderr
            test_result = self._parse_pytest_output(output, result.returncode)
            test_result.output = output

            return test_result

        except subprocess.TimeoutExpired:
            logger.error("[AutoFix] pytest timeout (300s)")
            return TestResult(
                passed=False,
                errors=["pytest execution timed out after 300 seconds"],
            )
        except FileNotFoundError:
            logger.error("[AutoFix] pytest not found")
            return TestResult(
                passed=False,
                errors=["pytest command not found - ensure pytest is installed"],
            )
        except Exception as e:
            logger.error(f"[AutoFix] pytest execution error: {e}")
            return TestResult(
                passed=False,
                errors=[str(e)],
            )

    def _parse_pytest_output(self, output: str, return_code: int) -> TestResult:
        """解析 pytest 输出"""
        result = TestResult(passed=(return_code == 0))

        # 解析汇总行 (例如: "5 passed, 2 failed, 1 error in 1.23s")
        import re

        # 尝试匹配测试结果摘要
        summary_pattern = r"(\d+)\s+(passed|failed|error|skipped)"
        for match in re.finditer(summary_pattern, output, re.IGNORECASE):
            count = int(match.group(1))
            status = match.group(2).lower()
            if status == "passed":
                result.passed_tests = count
            elif status == "failed":
                result.failed_tests = count
            elif status == "error":
                result.error_tests = count

        result.total_tests = result.passed_tests + result.failed_tests + result.error_tests

        # 提取失败用例名称
        failure_pattern = r"FAILED\s+(.+?)::"
        result.failures = re.findall(failure_pattern, output)

        # 提取错误信息
        error_pattern = r"E\s+(.+)"
        error_lines = re.findall(error_pattern, output)
        result.errors = error_lines[:10]  # 只保留前 10 条

        return result

    def _analyze_failures(self, test_result: TestResult) -> List[str]:
        """分析测试失败原因，生成修复提示"""
        hints = []

        if test_result.failures:
            hints.append(f"Failed tests: {', '.join(test_result.failures[:5])}")

        if test_result.errors:
            # 提取关键错误信息
            for error in test_result.errors[:3]:
                if "AssertionError" in error:
                    hints.append(f"Assertion failed: {error}")
                elif "TypeError" in error:
                    hints.append(f"Type error: {error}")
                elif "AttributeError" in error:
                    hints.append(f"Attribute error: {error}")
                elif "ImportError" in error or "ModuleNotFoundError" in error:
                    hints.append(f"Import error: {error}")
                else:
                    hints.append(f"Error: {error[:100]}")

        if not hints:
            hints.append("Tests failed - review test output for details")

        return hints

    def _generate_failure_report(
        self,
        task: str,
        target_files: List[str],
        test_result: Optional[TestResult],
    ) -> Path:
        """
        生成失败报告

        对齐 AI_CODE_FACTORY_DEV_GUIDE_v2.0 Section 12.1
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        module_name = target_files[0].split("/")[0] if target_files else "unknown"
        report_name = f"FAILURE_REPORT_{module_name}_{timestamp}.md"
        report_path = self.reports_dir / report_name

        # 确保报告目录存在
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 构建报告内容
        rounds_summary = []
        for r in self.rounds:
            status_emoji = "✅" if r.status == FixRoundStatus.SUCCESS else "❌"
            rounds_summary.append(
                f"- Round {r.round_num}: {status_emoji} {r.status.value}"
            )

        failures_list = []
        errors_list = []
        if test_result:
            failures_list = test_result.failures[:10]
            errors_list = test_result.errors[:10]

        content = f"""# FAILURE_REPORT - {module_name}

> **生成时间**: {datetime.now().isoformat()}
> **最大修复轮次**: {self.MAX_ROUNDS}
> **执行轮次**: {len(self.rounds)}
> **最终状态**: ❌ 失败

---

## 1. 当前代码状态

### 1.1 任务描述
```
{task}
```

### 1.2 目标文件
{chr(10).join(f"- `{f}`" for f in target_files)}

### 1.3 已生成文件
{chr(10).join(f"- `{f}`" for f in (self.rounds[-1].changes_made.keys() if self.rounds else []))}

---

## 2. 修复轮次记录

{chr(10).join(rounds_summary)}

---

## 3. 失败日志摘要

### 3.1 失败用例
{chr(10).join(f"- {f}" for f in failures_list) if failures_list else "无具体用例信息"}

### 3.2 错误信息
{chr(10).join(f"- {e}" for e in errors_list) if errors_list else "无具体错误信息"}

### 3.3 测试输出 (最后 50 行)
```
{test_result.output[-2000:] if test_result and test_result.output else "无输出"}
```

---

## 4. 推测根因

根据失败模式分析，可能的原因包括：

1. **SoT 不一致**: 代码可能未完全对齐 SoT 文档
2. **状态机违规**: 状态转换可能不符合 STATE_MACHINE.md 定义
3. **类型错误**: Pydantic 模型可能与 DATA_SCHEMA.md 不一致
4. **业务逻辑**: 可能缺少 BUSINESS_RULES.md 中定义的校验

---

## 5. 建议人工介入点

### 5.1 需要检查的文件
{chr(10).join(f"- `{f}`" for f in target_files[:5])}

### 5.2 需要检查的测试
{chr(10).join(f"- `{f}`" for f in self.test_files[:5])}

### 5.3 建议修复方向
1. 对比 SoT 文档检查状态枚举定义
2. 检查错误码是否在 ERROR_CODES_SOT.md 中定义
3. 验证字段类型是否与 DATA_SCHEMA.md 一致
4. 检查是否遗漏关键业务规则

---

## 6. 后续操作

选择以下方式继续：

- **A) 手动修复** → 修复后运行 `/agent test`
- **B) 调整需求** → 简化任务后运行 `/agent be`
- **C) 升级 SoT** → 人工修改 SoT 后重试

---

**自动生成**: AI 代码工厂 Auto-Fix Loop
**基准**: AI_CODE_FACTORY_DEV_GUIDE_v2.0
"""

        report_path.write_text(content, encoding="utf-8")
        logger.info(f"[AutoFix] Generated failure report: {report_path}")

        return report_path


# === 便捷函数 ===

def run_auto_fix(
    base_path: Path,
    code_agent: Any,
    task: str,
    target_files: List[str],
    test_files: List[str],
) -> AutoFixResult:
    """
    便捷函数: 执行自动修复循环

    Args:
        base_path: 项目根路径
        code_agent: 代码生成 Agent
        task: 任务描述
        target_files: 目标文件列表
        test_files: 测试文件列表

    Returns:
        AutoFixResult
    """
    loop = AutoFixLoop(
        base_path=base_path,
        code_agent=code_agent,
        test_files=test_files,
    )
    return loop.execute(task, target_files)


__all__ = [
    "AutoFixLoop",
    "AutoFixResult",
    "FixRound",
    "FixRoundStatus",
    "TestResult",
    "run_auto_fix",
]
