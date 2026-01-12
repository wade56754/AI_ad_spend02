"""
代理适配器

将 wshobson/agents 代理适配到项目需求

版本: v1.0
基准: AI 广告代投系统 SoT 规范
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from .wshobson_agent_loader import Agent


class AgentAdapter:
    """代理适配器 - 将 wshobson/agents 代理适配到项目"""
    
    # 项目技术栈
    PROJECT_TECH_STACK = {
        "backend": {
            "framework": "FastAPI",
            "orm": "SQLAlchemy 2.x",
            "validation": "Pydantic v2",
            "database": "PostgreSQL (Supabase)",
            "auth": "Supabase Auth + JWT",
        },
        "frontend": {
            "framework": "Next.js 16",
            "language": "TypeScript 5.x",
            "ui": "shadcn/ui + Tailwind CSS",
            "state": "TanStack Query v5",
            "form": "react-hook-form + zod",
        },
    }
    
    # SoT 规范约束
    SOT_CONSTRAINTS = {
        "roles": ["admin", "finance", "account_manager", "media_buyer"],
        "business_roles": ["ceo", "project_owner", "finance", "pitcher", "account_manager", "admin"],
        "daily_report_states": [
            "raw_submitted", "trend_pending", "trend_ok", "trend_flagged",
            "trend_resolved", "final_pending", "final_confirmed", "final_locked"
        ],
        "topup_states": [
            "draft", "pending_review", "finance_approve", "paid", "completed",
            "cancelled", "rejected"
        ],
    }
    
    def __init__(self, project_root: Path):
        """
        初始化适配器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self.sot_docs_path = project_root / "docs" / "sot"
    
    def adapt_agent(self, wshobson_agent: Agent, project_requirements: Optional[Dict] = None) -> Agent:
        """
        适配代理
        
        Args:
            wshobson_agent: wshobson/agents 代理
            project_requirements: 项目需求（可选，默认使用内置配置）
        
        Returns:
            适配后的代理
        """
        if project_requirements is None:
            project_requirements = {
                "tech_stack": self.PROJECT_TECH_STACK,
                "sot_constraints": self.SOT_CONSTRAINTS,
            }
        
        # 1. 保留核心能力
        adapted_agent = Agent(
            id=wshobson_agent.id,
            name=wshobson_agent.name,
            source=wshobson_agent.source,
            model_tier=wshobson_agent.model_tier,
            category=wshobson_agent.category,
            description=wshobson_agent.description,
            skills=wshobson_agent.skills.copy(),
            tools=wshobson_agent.tools.copy(),
            capabilities=wshobson_agent.capabilities.copy(),
            metadata=wshobson_agent.metadata.copy(),
        )
        
        # 2. 注入 SoT 规范约束
        self._inject_sot_constraints(adapted_agent, project_requirements)
        
        # 3. 适配技术栈
        self._adapt_tech_stack(adapted_agent, project_requirements)
        
        # 4. 添加项目特定规则
        self._add_project_rules(adapted_agent)
        
        return adapted_agent
    
    def _inject_sot_constraints(self, agent: Agent, requirements: Dict):
        """注入 SoT 规范约束"""
        sot_constraints = requirements.get("sot_constraints", {})
        
        # 在描述中添加 SoT 约束说明
        sot_note = "\n\n**SoT 规范约束**:\n"
        sot_note += "- 角色: " + ", ".join(sot_constraints.get("roles", [])) + "\n"
        sot_note += "- 日报状态: " + ", ".join(sot_constraints.get("daily_report_states", [])[:3]) + "...\n"
        
        agent.description += sot_note
        
        # 在元数据中记录 SoT 约束
        agent.metadata["sot_constraints"] = sot_constraints
    
    def _adapt_tech_stack(self, agent: Agent, requirements: Dict):
        """适配技术栈"""
        tech_stack = requirements.get("tech_stack", {})
        
        # 根据代理类别适配技术栈
        if agent.category == "development":
            if "backend" in agent.id or "backend" in agent.capabilities:
                agent.metadata["tech_stack"] = tech_stack.get("backend", {})
            elif "frontend" in agent.id or "frontend" in agent.capabilities:
                agent.metadata["tech_stack"] = tech_stack.get("frontend", {})
        
        # 在描述中添加技术栈说明
        if "tech_stack" in agent.metadata:
            tech_note = "\n\n**技术栈**:\n"
            for key, value in agent.metadata["tech_stack"].items():
                tech_note += f"- {key}: {value}\n"
            agent.description += tech_note
    
    def _add_project_rules(self, agent: Agent):
        """添加项目特定规则"""
        # 添加项目规则引用
        rules_note = "\n\n**项目规则**:\n"
        rules_note += "- 参考: `docs/sot/MASTER.md`\n"
        rules_note += "- 状态机: `docs/sot/STATE_MACHINE.md`\n"
        rules_note += "- 数据模型: `docs/sot/DATA_SCHEMA.md`\n"
        
        agent.description += rules_note
        
        # 在元数据中记录规则路径
        agent.metadata["project_rules"] = {
            "master": "docs/sot/MASTER.md",
            "state_machine": "docs/sot/STATE_MACHINE.md",
            "data_schema": "docs/sot/DATA_SCHEMA.md",
        }

