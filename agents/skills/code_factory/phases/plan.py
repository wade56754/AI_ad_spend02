"""
PLAN 阶段 - 计划生成

对接 Superpowers writing-plans 技能，生成详细的实现计划。

功能:
- 将需求分解为小任务 (每个 2-5 分钟)
- 每个任务包含精确的文件路径和完整代码
- 包含验证步骤

基准文档: MASTER.md v4.8
版本: v7.0

Superpowers 对接:
- .superpowers/skills/writing-plans/SKILL.md
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..types import ExecutionContext, TaskSpec, ImplementationPlan

logger = logging.getLogger(__name__)


@dataclass
class PlanResult:
    """计划阶段结果"""
    plan: ImplementationPlan
    superpowers_skill_used: bool = False
    

class PlanPhase:
    """
    计划生成阶段
    
    职责:
    1. 分析澄清后的需求
    2. 生成实现计划
    3. 分解为可执行任务
    
    Superpowers 集成:
    - 使用 writing-plans 技能的原则
    - YAGNI: 只实现需要的功能
    - 任务粒度: 2-5 分钟
    """
    
    PHASE_NAME = "plan"
    
    def __init__(self, context: ExecutionContext):
        self.context = context
        self.superpowers_skill_path = context.superpowers_dir / "writing-plans" / "SKILL.md"
    
    def execute(
        self,
        requirement: str,
        phase_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        执行计划生成阶段
        
        Args:
            requirement: 需求描述
            phase_data: 前序阶段数据 (包含 clarify 阶段的输出)
            
        Returns:
            计划数据
        """
        logger.info("开始 PLAN 阶段")
        
        # 获取澄清结果
        clarify_data = phase_data.get("clarify", {})
        
        # 分析需求类型
        req_analysis = self._analyze_requirement(requirement, clarify_data)
        
        # 生成任务列表
        tasks = self._generate_tasks(requirement, req_analysis)
        
        # 构建实现计划
        plan = ImplementationPlan(
            tasks=tasks,
            estimated_time=self._estimate_time(tasks),
            approach=req_analysis.get("approach", ""),
            risks=req_analysis.get("risks", []),
        )
        
        logger.info(f"生成 {len(tasks)} 个任务")
        
        return {
            "plan": plan.to_dict(),
            "tasks": [t.to_dict() for t in tasks],
            "superpowers_skill_used": self._check_superpowers_available(),
        }
    
    def _analyze_requirement(
        self,
        requirement: str,
        clarify_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        分析需求
        
        Returns:
            分析结果，包含:
            - scope: 范围 (backend/frontend/fullstack)
            - complexity: 复杂度 (low/medium/high)
            - approach: 实现方法
            - risks: 风险点
        """
        req_lower = requirement.lower()
        
        # 判断范围
        scope = "fullstack"
        if "后端" in requirement or "api" in req_lower or "backend" in req_lower:
            scope = "backend"
        elif "前端" in requirement or "ui" in req_lower or "frontend" in req_lower:
            scope = "frontend"
        
        # 判断复杂度
        complexity = "medium"
        complexity_keywords = {
            "high": ["重构", "架构", "迁移", "系统", "完整", "全部"],
            "low": ["修复", "调整", "简单", "小", "单个"],
        }
        for level, keywords in complexity_keywords.items():
            if any(kw in requirement for kw in keywords):
                complexity = level
                break
        
        # 确定方法
        approach = self._determine_approach(scope, complexity)
        
        # 识别风险
        risks = self._identify_risks(requirement, clarify_data)
        
        return {
            "scope": scope,
            "complexity": complexity,
            "approach": approach,
            "risks": risks,
        }
    
    def _determine_approach(self, scope: str, complexity: str) -> str:
        """确定实现方法"""
        approaches = {
            ("backend", "low"): "直接修改相关文件，确保测试通过",
            ("backend", "medium"): "先定义 Schema，实现 Service，再创建 Router",
            ("backend", "high"): "分阶段实现：数据模型 → 业务逻辑 → API 层 → 测试",
            ("frontend", "low"): "修改组件，确保类型正确",
            ("frontend", "medium"): "Types → API → Hooks → Components",
            ("frontend", "high"): "架构设计 → 组件拆分 → 状态管理 → 测试",
            ("fullstack", "low"): "后端 API → 前端调用",
            ("fullstack", "medium"): "后端完整实现 → 前端 Types → 前端组件",
            ("fullstack", "high"): "分层实现：DB → Service → API → Frontend",
        }
        return approaches.get((scope, complexity), "按需实现")
    
    def _identify_risks(
        self,
        requirement: str,
        clarify_data: Dict[str, Any],
    ) -> List[str]:
        """识别风险点"""
        risks = []
        
        # 基于关键词识别风险
        risk_keywords = {
            "删除": "数据丢失风险，需要备份",
            "迁移": "兼容性风险，需要迁移脚本",
            "权限": "安全风险，需要权限验证",
            "支付": "资金风险，需要事务保护",
            "批量": "性能风险，需要分批处理",
        }
        
        for keyword, risk in risk_keywords.items():
            if keyword in requirement:
                risks.append(risk)
        
        return risks
    
    def _generate_tasks(
        self,
        requirement: str,
        analysis: Dict[str, Any],
    ) -> List[TaskSpec]:
        """
        生成任务列表
        
        遵循 Superpowers writing-plans 原则:
        - 每个任务 2-5 分钟
        - 包含精确的文件路径
        - 包含验证步骤
        """
        tasks = []
        scope = analysis.get("scope", "fullstack")
        task_id = 1
        
        # 后端任务
        if scope in ("backend", "fullstack"):
            # Schema 任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description=f"定义 Pydantic Schema (基于需求: {requirement[:50]}...)",
                category="backend",
                priority=1,
                acceptance_criteria=[
                    "Schema 继承 BaseModel",
                    "使用 ConfigDict(from_attributes=True)",
                    "字段类型符合 DATA_SCHEMA.md",
                ],
            ))
            task_id += 1
            
            # Service 任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description="实现业务逻辑 Service",
                category="backend",
                priority=2,
                dependencies=[f"task-{task_id-1:03d}"],
                acceptance_criteria=[
                    "使用 SQLAlchemy 2.x select() 语法",
                    "包含错误处理",
                    "符合 BUSINESS_RULES.md",
                ],
            ))
            task_id += 1
            
            # Router 任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description="创建 FastAPI Router",
                category="backend",
                priority=3,
                dependencies=[f"task-{task_id-1:03d}"],
                acceptance_criteria=[
                    "使用 Envelope 响应格式",
                    "使用标准错误码",
                    "符合 API_SOT.md",
                ],
            ))
            task_id += 1
            
            # 测试任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description="编写后端单元测试",
                category="backend",
                priority=4,
                dependencies=[f"task-{task_id-1:03d}"],
                acceptance_criteria=[
                    "测试覆盖主要路径",
                    "使用 pytest fixtures",
                    "测试错误处理",
                ],
            ))
            task_id += 1
        
        # 前端任务
        if scope in ("frontend", "fullstack"):
            # Types 任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description="定义 TypeScript 类型",
                category="frontend",
                priority=1 if scope == "frontend" else 5,
                acceptance_criteria=[
                    "类型与后端 Schema 对齐",
                    "使用 strict 模式",
                    "无 any 类型",
                ],
            ))
            task_id += 1
            
            # API 任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description="实现前端 API 调用",
                category="frontend",
                priority=2 if scope == "frontend" else 6,
                dependencies=[f"task-{task_id-1:03d}"],
                acceptance_criteria=[
                    "使用 apiFetch",
                    "处理加载和错误状态",
                ],
            ))
            task_id += 1
            
            # Component 任务
            tasks.append(TaskSpec(
                id=f"task-{task_id:03d}",
                description="实现 React 组件",
                category="frontend",
                priority=3 if scope == "frontend" else 7,
                dependencies=[f"task-{task_id-1:03d}"],
                acceptance_criteria=[
                    "使用 shadcn/ui 组件",
                    "响应式设计",
                    "包含加载状态",
                ],
            ))
            task_id += 1
        
        return tasks
    
    def _estimate_time(self, tasks: List[TaskSpec]) -> str:
        """估算总时间"""
        # 假设每个任务平均 3 分钟
        total_minutes = len(tasks) * 3
        if total_minutes < 60:
            return f"{total_minutes} 分钟"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours} 小时 {minutes} 分钟"
    
    def _check_superpowers_available(self) -> bool:
        """检查 Superpowers 技能是否可用"""
        return self.superpowers_skill_path.exists()
