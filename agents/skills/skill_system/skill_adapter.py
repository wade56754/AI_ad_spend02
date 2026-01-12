"""
技能适配器

将 wshobson/agents 技能适配到项目需求

版本: v1.0
基准: AI 广告代投系统 SoT 规范
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .base import Skill, SkillMetadata


class SkillAdapter:
    """技能适配器"""
    
    # 项目技术栈
    PROJECT_TECH_STACK = {
        "backend": {
            "framework": "FastAPI",
            "orm": "SQLAlchemy 2.x",
            "validation": "Pydantic v2",
            "database": "PostgreSQL (Supabase)",
        },
        "frontend": {
            "framework": "Next.js 16",
            "language": "TypeScript 5.x",
            "ui": "shadcn/ui + Tailwind CSS",
        },
    }
    
    def __init__(self, project_root: Path):
        """
        初始化适配器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
    
    def adapt_skill(self, wshobson_skill: Skill, project_context: Optional[Dict] = None) -> Skill:
        """
        适配技能到项目
        
        Args:
            wshobson_skill: wshobson/agents 技能
            project_context: 项目上下文（SoT、技术栈、规范）
        
        Returns:
            适配后的技能（包装类，包含修改后的指令）
        """
        if project_context is None:
            project_context = {
                "tech_stack": self.PROJECT_TECH_STACK,
                "sot_references": [
                    "MASTER.md",
                    "STATE_MACHINE.md",
                    "DATA_SCHEMA.md",
                ],
            }
        
        # P0-1 fix: 获取原始指令并适配
        original_instructions = wshobson_skill.instructions
        
        # 2. 注入 SoT 约束
        adapted_instructions = self._inject_sot_constraints(
            original_instructions,
            project_context
        )
        
        # 3. 适配技术栈示例
        adapted_instructions = self._adapt_tech_examples(
            adapted_instructions,
            project_context
        )
        
        # 4. 添加项目特定规则
        adapted_instructions = self._add_project_rules(
            adapted_instructions,
            project_context
        )
        
        # P0-1 fix: 创建适配后的技能包装类
        return AdaptedSkill(wshobson_skill, adapted_instructions)
    
    def _inject_sot_constraints(self, instructions: str, context: Dict) -> str:
        """注入 SoT 约束"""
        sot_section = "\n\n## SoT 规范约束\n\n"
        sot_section += "本项目遵循以下 SoT 规范：\n"
        sot_section += "- MASTER.md - 系统宪法\n"
        sot_section += "- STATE_MACHINE.md - 状态机定义\n"
        sot_section += "- DATA_SCHEMA.md - 数据模型\n"
        sot_section += "- API_SOT.md - API 契约\n"
        sot_section += "- ERROR_CODES_SOT.md - 错误码\n\n"
        sot_section += "**重要**: 所有代码必须符合 SoT 规范，禁止使用未定义的状态、角色、字段。\n"
        
        return instructions + sot_section
    
    def _adapt_tech_examples(self, instructions: str, context: Dict) -> str:
        """适配技术栈示例"""
        tech_stack = context.get("tech_stack", {})
        
        # 替换通用示例为项目特定示例
        replacements = {
            "Flask": "FastAPI",
            "Django": "FastAPI",
            "SQLAlchemy 1.x": "SQLAlchemy 2.x",
            "Pydantic v1": "Pydantic v2",
            "React": "Next.js 16 + React",
            "TypeScript": "TypeScript 5.x (strict mode)",
        }
        
        adapted = instructions
        for old, new in replacements.items():
            adapted = adapted.replace(old, new)
        
        return adapted
    
    def _add_project_rules(self, instructions: str, context: Dict) -> str:
        """添加项目特定规则"""
        rules_section = "\n\n## 项目特定规则\n\n"
        rules_section += "1. **技术栈约束**:\n"
        rules_section += "   - 后端: FastAPI + SQLAlchemy 2.x + Pydantic v2\n"
        rules_section += "   - 前端: Next.js 16 + TypeScript 5.x + shadcn/ui\n"
        rules_section += "\n2. **代码风格**:\n"
        rules_section += "   - Python: PEP8, 类型提示\n"
        rules_section += "   - TypeScript: strict mode, 无 any 类型\n"
        rules_section += "\n3. **API 响应格式**:\n"
        rules_section += "   - 使用 Envelope 格式: `success_response(data={...})`\n"
        rules_section += "   - 错误使用 `BusinessError` 和标准错误码\n"
        
        return instructions + rules_section


class AdaptedSkill(Skill):
    """
    适配后的技能包装类
    
    P0-1 fix: 包装原始技能，但使用适配后的指令
    """
    
    def __init__(self, original_skill: Skill, adapted_instructions: str):
        """
        初始化适配后的技能
        
        Args:
            original_skill: 原始技能
            adapted_instructions: 适配后的指令
        """
        # 使用原始技能的路径和元数据
        super().__init__(original_skill.skill_path)
        self._original_skill = original_skill
        self._adapted_instructions = adapted_instructions
        # 直接使用原始技能的元数据和资源
        self._metadata = original_skill._metadata
        self._resources = original_skill._resources
        self._loaded_layers = original_skill._loaded_layers.copy()
    
    @property
    def instructions(self) -> str:
        """返回适配后的指令"""
        return self._adapted_instructions

