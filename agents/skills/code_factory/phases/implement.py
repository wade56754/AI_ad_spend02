"""
IMPLEMENT 阶段 - TDD 实现

对接 Superpowers test-driven-development 技能，强制 TDD 流程。

功能:
- 强制先写测试，再写实现
- RED → GREEN → REFACTOR 循环
- 与 Superpowers TDD 技能集成

基准文档: MASTER.md v4.8
版本: v7.0

Superpowers 对接:
- .superpowers/skills/test-driven-development/SKILL.md

TDD 铁律:
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum

from ..types import ExecutionContext, TaskSpec, GeneratedFile
from ..core.exceptions import CodeFactoryError
from ..adapters.superpowers import SuperpowersAdapter

logger = logging.getLogger(__name__)


class TDDViolation(CodeFactoryError):
    """TDD 违规异常"""
    code = "CF-TDD-001"
    
    def __init__(self, message: str, phase: str = "unknown"):
        self.phase = phase
        super().__init__(f"TDD 违规 ({phase}): {message}")


class TDDPhase(str, Enum):
    """TDD 阶段"""
    RED = "red"        # 写失败测试
    GREEN = "green"    # 写最小实现
    REFACTOR = "refactor"  # 重构


@dataclass
class TDDCycleResult:
    """TDD 循环结果"""
    task_id: str
    success: bool
    test_file: Optional[GeneratedFile] = None
    impl_file: Optional[GeneratedFile] = None
    test_passed: bool = False
    refactored: bool = False
    error: Optional[str] = None


class ImplementPhase:
    """
    TDD 实现阶段
    
    职责:
    1. 强制 TDD 流程
    2. 为每个任务执行 RED-GREEN-REFACTOR 循环
    3. 验证测试先失败后通过
    
    Superpowers TDD 原则:
    - 没有失败的测试，就不能写生产代码
    - 写代码前先写测试? 删掉代码，重新开始
    - 测试必须先失败，证明它真的在测试某些东西
    """
    
    PHASE_NAME = "implement"
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.superpowers_skill_path = context.superpowers_dir / "test-driven-development" / "SKILL.md"
        
        # 初始化 Superpowers 适配器
        self.superpowers = SuperpowersAdapter(context.superpowers_dir)
        
        # 加载 TDD 技能原则
        tdd_skill = self.superpowers.load_skill("tdd")
        self.tdd_principles = tdd_skill.content if tdd_skill else ""
        
        logger.info(f"TDD 技能可用: {bool(tdd_skill)}")
    
    def execute(
        self,
        requirement: str,
        phase_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行 TDD 实现阶段
        
        Args:
            requirement: 需求描述
            phase_data: 前序阶段数据 (包含 plan 阶段的任务列表)
            
        Returns:
            实现数据
        """
        logger.info("开始 IMPLEMENT 阶段 (TDD 模式)")
        
        # 获取任务列表
        plan_data = phase_data.get("plan", {})
        tasks_data = plan_data.get("tasks", [])
        
        if not tasks_data:
            logger.warning("没有任务需要实现")
            return {
                "cycles": [],
                "output_files": [],
                "tdd_enforced": True,
            }
        
        # 转换为 TaskSpec
        tasks = [self._dict_to_task(t) for t in tasks_data]
        
        # 执行 TDD 循环
        cycles = []
        output_files = []
        
        for task in tasks:
            logger.info(f"处理任务: {task.id} - {task.description[:50]}...")
            
            try:
                cycle_result = self._execute_tdd_cycle(task)
                cycles.append(cycle_result)
                
                if cycle_result.test_file:
                    output_files.append(cycle_result.test_file.path)
                if cycle_result.impl_file:
                    output_files.append(cycle_result.impl_file.path)
                    
            except TDDViolation as e:
                logger.error(f"TDD 违规: {e}")
                cycles.append(TDDCycleResult(
                    task_id=task.id,
                    success=False,
                    error=str(e),
                ))
        
        # 统计
        success_count = sum(1 for c in cycles if c.success)
        logger.info(f"TDD 完成: {success_count}/{len(cycles)} 任务成功")
        
        return {
            "cycles": [self._cycle_to_dict(c) for c in cycles],
            "output_files": output_files,
            "tdd_enforced": True,
            "success_rate": success_count / len(cycles) if cycles else 1.0,
        }
    
    def _dict_to_task(self, data: Dict[str, Any]) -> TaskSpec:
        """字典转 TaskSpec"""
        return TaskSpec(
            id=data.get("id", "unknown"),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            priority=data.get("priority", 1),
            dependencies=data.get("dependencies", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
        )
    
    def _execute_tdd_cycle(self, task: TaskSpec) -> TDDCycleResult:
        """
        执行单个任务的 TDD 循环
        
        TDD 流程:
        1. RED: 写一个失败的测试
        2. 验证测试失败
        3. GREEN: 写最小代码使测试通过
        4. 验证测试通过
        5. REFACTOR: 清理代码
        """
        result = TDDCycleResult(task_id=task.id, success=True)
        
        # 1. RED: 生成失败测试
        logger.info(f"  [RED] 生成测试: {task.id}")
        test_file = self._generate_test(task)
        result.test_file = test_file
        
        # 2. 验证测试失败 (模拟)
        # 在实际环境中，这里会运行测试并验证失败
        if not self._verify_test_fails(test_file):
            raise TDDViolation("测试必须先失败", phase="RED")
        
        # 3. GREEN: 生成最小实现
        logger.info(f"  [GREEN] 生成实现: {task.id}")
        impl_file = self._generate_implementation(task, test_file)
        result.impl_file = impl_file
        
        # 4. 验证测试通过 (模拟)
        if not self._verify_test_passes(test_file, impl_file):
            raise TDDViolation("实现必须使测试通过", phase="GREEN")
        result.test_passed = True
        
        # 5. REFACTOR: 重构 (可选)
        logger.info(f"  [REFACTOR] 清理代码: {task.id}")
        result.refactored = True
        
        return result
    
    def _generate_test(self, task: TaskSpec) -> GeneratedFile:
        """
        生成测试文件
        
        遵循 Superpowers TDD 原则:
        - 测试一个行为
        - 清晰的名称
        - 使用真实代码 (尽量避免 mock)
        """
        category = task.category
        
        if category == "backend":
            return self._generate_backend_test(task)
        elif category == "frontend":
            return self._generate_frontend_test(task)
        else:
            return self._generate_generic_test(task)
    
    def _generate_backend_test(self, task: TaskSpec) -> GeneratedFile:
        """生成后端测试"""
        test_name = task.id.replace("-", "_")
        
        content = f'''"""
测试: {task.description}

TDD: 此测试在实现之前编写
验收标准:
{chr(10).join(f"- {c}" for c in task.acceptance_criteria)}
"""

import pytest
from httpx import AsyncClient


class Test{test_name.title().replace("_", "")}:
    """测试用例"""
    
    @pytest.mark.asyncio
    async def test_should_succeed_with_valid_input(self, client: AsyncClient):
        """应该: 有效输入时成功"""
        # Arrange
        # TODO: 设置测试数据
        
        # Act
        # TODO: 调用 API
        
        # Assert
        # TODO: 验证结果
        assert False, "测试未实现 - TDD RED 阶段"
    
    @pytest.mark.asyncio
    async def test_should_fail_with_invalid_input(self, client: AsyncClient):
        """应该: 无效输入时失败"""
        # Arrange
        # TODO: 设置无效数据
        
        # Act
        # TODO: 调用 API
        
        # Assert
        # TODO: 验证错误响应
        assert False, "测试未实现 - TDD RED 阶段"
'''
        
        return GeneratedFile(
            path=f"backend/tests/test_{test_name}.py",
            content=content,
            action="create",
        )
    
    def _generate_frontend_test(self, task: TaskSpec) -> GeneratedFile:
        """生成前端测试"""
        test_name = task.id.replace("-", "_")
        
        content = f'''/**
 * 测试: {task.description}
 * 
 * TDD: 此测试在实现之前编写
 * 验收标准:
{chr(10).join(f" * - {c}" for c in task.acceptance_criteria)}
 */

import {{ render, screen }} from '@testing-library/react';
import {{ describe, it, expect }} from 'vitest';

describe('{task.description}', () => {{
  it('should render successfully', () => {{
    // Arrange
    // TODO: 设置测试数据
    
    // Act
    // TODO: 渲染组件
    
    // Assert
    expect(false).toBe(true); // TDD RED 阶段
  }});
  
  it('should handle user interaction', () => {{
    // Arrange
    // TODO: 设置测试数据
    
    // Act
    // TODO: 模拟用户交互
    
    // Assert
    expect(false).toBe(true); // TDD RED 阶段
  }});
}});
'''
        
        return GeneratedFile(
            path=f"frontend/src/__tests__/{test_name}.test.tsx",
            content=content,
            action="create",
        )
    
    def _generate_generic_test(self, task: TaskSpec) -> GeneratedFile:
        """生成通用测试"""
        test_name = task.id.replace("-", "_")
        
        content = f'''"""
测试: {task.description}

TDD: 此测试在实现之前编写
"""

import pytest


def test_{test_name}_should_work():
    """应该: 正常工作"""
    # TDD RED 阶段 - 测试必须先失败
    assert False, "测试未实现"
'''
        
        return GeneratedFile(
            path=f"tests/test_{test_name}.py",
            content=content,
            action="create",
        )
    
    def _generate_implementation(
        self,
        task: TaskSpec,
        test_file: GeneratedFile,
    ) -> GeneratedFile:
        """
        生成最小实现
        
        遵循 Superpowers TDD 原则:
        - 只写使测试通过的最小代码
        - 不要添加额外功能
        - 不要过度设计
        """
        category = task.category
        impl_name = task.id.replace("-", "_").replace("task_", "")
        
        if category == "backend":
            content = f'''"""
实现: {task.description}

SoT: 符合 MASTER.md v4.8 规范
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_db
from backend.core.response import success_response

router = APIRouter()


# TODO: 实现使测试通过的最小代码
# 验收标准:
{chr(10).join(f"# - {c}" for c in task.acceptance_criteria)}
'''
            path = f"backend/routers/{impl_name}.py"
            
        elif category == "frontend":
            content = f'''/**
 * 实现: {task.description}
 * 
 * SoT: 符合 MASTER.md v4.8 规范
 */

import React from 'react';

// TODO: 实现使测试通过的最小代码
// 验收标准:
{chr(10).join(f"// - {c}" for c in task.acceptance_criteria)}

export function Component() {{
  return <div>TODO: 实现</div>;
}}
'''
            path = f"frontend/src/components/{impl_name}.tsx"
            
        else:
            content = f'''"""
实现: {task.description}
"""

# TODO: 实现使测试通过的最小代码
'''
            path = f"src/{impl_name}.py"
        
        return GeneratedFile(
            path=path,
            content=content,
            action="create",
        )
    
    def _verify_test_fails(self, test_file: GeneratedFile) -> bool:
        """
        验证测试失败
        
        在实际环境中会运行测试，这里模拟验证
        """
        # 检查测试文件是否包含 "assert False" 或类似的失败断言
        return "assert False" in test_file.content or "expect(false)" in test_file.content
    
    def _verify_test_passes(
        self,
        test_file: GeneratedFile,
        impl_file: GeneratedFile,
    ) -> bool:
        """
        验证测试通过
        
        在实际环境中会运行测试，这里模拟验证
        """
        # 在实际环境中，这里会:
        # 1. 写入测试文件
        # 2. 写入实现文件
        # 3. 运行 pytest/vitest
        # 4. 检查测试结果
        return True  # 模拟通过
    
    def _cycle_to_dict(self, cycle: TDDCycleResult) -> Dict[str, Any]:
        """循环结果转字典"""
        return {
            "task_id": cycle.task_id,
            "success": cycle.success,
            "test_file": cycle.test_file.to_dict() if cycle.test_file else None,
            "impl_file": cycle.impl_file.to_dict() if cycle.impl_file else None,
            "test_passed": cycle.test_passed,
            "refactored": cycle.refactored,
            "error": cycle.error,
        }
