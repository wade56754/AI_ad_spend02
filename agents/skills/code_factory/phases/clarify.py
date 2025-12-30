"""
CLARIFY 阶段 - 需求澄清

在代码生成前澄清需求，减少歧义和误解。

功能:
- 分析需求描述，识别模糊点
- 生成澄清问题
- 支持交互式问答
- 输出结构化的澄清结果

基准文档: MASTER.md v4.6
版本: v5.0
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
import re

from .base import PhaseBase, PhaseResult
from .context import PipelineContext


class ClarityLevel(str, Enum):
    """清晰度级别"""
    CLEAR = "clear"           # 清晰，无需澄清
    NEEDS_CLARIFICATION = "needs_clarification"  # 需要澄清
    AMBIGUOUS = "ambiguous"   # 模糊，必须澄清


class QuestionCategory(str, Enum):
    """问题分类"""
    SCOPE = "scope"           # 范围问题
    DATA = "data"             # 数据问题
    API = "api"               # 接口问题
    AUTH = "auth"             # 权限问题
    BUSINESS = "business"     # 业务规则问题
    ACCEPTANCE = "acceptance" # 验收标准问题


@dataclass
class ClarifyQuestion:
    """澄清问题"""
    id: str
    category: QuestionCategory
    question: str
    importance: str  # "required" | "optional"
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "question": self.question,
            "importance": self.importance,
            "options": self.options,
            "answer": self.answer,
        }


@dataclass
class ClarifiedRequirement:
    """澄清后的需求"""
    summary: str
    user_role: Optional[str] = None
    business_flow: Optional[str] = None
    
    scope_included: List[str] = field(default_factory=list)
    scope_excluded: List[str] = field(default_factory=list)
    
    tables: List[str] = field(default_factory=list)
    new_fields: List[str] = field(default_factory=list)
    
    api_endpoints: List[Dict[str, str]] = field(default_factory=list)
    
    business_rules: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    
    acceptance_criteria: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "user_role": self.user_role,
            "business_flow": self.business_flow,
            "scope": {
                "included": self.scope_included,
                "excluded": self.scope_excluded,
            },
            "data": {
                "tables": self.tables,
                "new_fields": self.new_fields,
            },
            "api": {
                "endpoints": self.api_endpoints,
            },
            "constraints": {
                "business_rules": self.business_rules,
                "permissions": self.permissions,
            },
            "acceptance_criteria": self.acceptance_criteria,
        }
    
    def to_prompt_context(self) -> str:
        """生成提示词上下文"""
        lines = [
            "## 澄清后的需求",
            "",
            f"**摘要**: {self.summary}",
        ]
        
        if self.user_role:
            lines.append(f"**目标用户**: {self.user_role}")
        
        if self.business_flow:
            lines.append(f"**业务流程**: {self.business_flow}")
        
        if self.scope_included:
            lines.append("\n### 功能范围")
            lines.append("包含:")
            for item in self.scope_included:
                lines.append(f"  - {item}")
        
        if self.scope_excluded:
            lines.append("不包含:")
            for item in self.scope_excluded:
                lines.append(f"  - {item}")
        
        if self.tables:
            lines.append(f"\n### 涉及数据表: {', '.join(self.tables)}")
        
        if self.api_endpoints:
            lines.append("\n### API 端点:")
            for ep in self.api_endpoints:
                lines.append(f"  - {ep.get('method', 'GET')} {ep.get('path', '')}: {ep.get('description', '')}")
        
        if self.business_rules:
            lines.append("\n### 业务规则:")
            for rule in self.business_rules:
                lines.append(f"  - {rule}")
        
        if self.acceptance_criteria:
            lines.append("\n### 验收标准:")
            for i, criteria in enumerate(self.acceptance_criteria, 1):
                lines.append(f"  {i}. {criteria}")
        
        return "\n".join(lines)


@dataclass
class ClarifyResult:
    """澄清阶段结果"""
    clarity_level: ClarityLevel
    questions: List[ClarifyQuestion]
    clarified_requirement: Optional[ClarifiedRequirement] = None
    original_requirement: str = ""
    
    @property
    def needs_interaction(self) -> bool:
        """是否需要用户交互"""
        return self.clarity_level == ClarityLevel.NEEDS_CLARIFICATION and any(
            q.importance == "required" and q.answer is None 
            for q in self.questions
        )
    
    @property
    def unanswered_questions(self) -> List[ClarifyQuestion]:
        """获取未回答的问题"""
        return [q for q in self.questions if q.answer is None]
    
    @property
    def required_unanswered(self) -> List[ClarifyQuestion]:
        """获取必须回答的未回答问题"""
        return [q for q in self.questions if q.importance == "required" and q.answer is None]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "clarity_level": self.clarity_level.value,
            "questions": [q.to_dict() for q in self.questions],
            "clarified_requirement": self.clarified_requirement.to_dict() if self.clarified_requirement else None,
            "original_requirement": self.original_requirement,
            "needs_interaction": self.needs_interaction,
        }


class ClarifyPhase(PhaseBase):
    """
    CLARIFY 阶段 - 需求澄清
    
    工作流程:
    1. 分析需求描述
    2. 识别模糊点
    3. 生成澄清问题
    4. (可选) 等待用户回答
    5. 输出结构化需求
    
    使用方式:
    ```python
    phase = ClarifyPhase()
    
    # 分析需求
    result = phase.analyze(requirement)
    
    # 如果需要澄清
    if result.needs_interaction:
        for q in result.required_unanswered:
            answer = input(q.question)
            q.answer = answer
        
        # 重新生成澄清结果
        result = phase.finalize(result)
    ```
    """
    
    # 模糊关键词
    AMBIGUOUS_KEYWORDS = [
        "等", "之类", "类似", "一些", "某些", "适当", "合理",
        "etc", "similar", "some", "various", "appropriate",
    ]
    
    # 需要澄清的模式
    NEED_CLARIFICATION_PATTERNS = [
        r"(什么|哪些|如何|怎么)",  # 疑问词
        r"(可能|也许|大概)",       # 不确定词
        r"(以及|还有|包括)",       # 不完整列举
    ]
    
    # 角色关键词映射
    ROLE_KEYWORDS = {
        "投手": "pitcher",
        "财务": "finance",
        "项目负责人": "project_owner",
        "管理员": "admin",
        "户管": "account_manager",
        "老板": "ceo",
    }
    
    # 模块关键词映射
    MODULE_KEYWORDS = {
        "日报": ("daily_reports", "pitcher"),
        "充值": ("topup_requests", "finance"),
        "账户": ("ad_accounts", "account_manager"),
        "项目": ("projects", "project_owner"),
        "用户": ("users", "admin"),
    }
    
    def __init__(
        self,
        interaction_callback: Optional[Callable[[List[ClarifyQuestion]], List[ClarifyQuestion]]] = None,
    ):
        """初始化
        
        Args:
            interaction_callback: 交互回调函数，用于获取用户回答
        """
        super().__init__(phase_id=0, phase_name="CLARIFY")
        self.interaction_callback = interaction_callback
    
    def execute(self, context: PipelineContext) -> PhaseResult:
        """执行澄清阶段"""
        requirement = context.requirement
        
        # 1. 分析需求
        clarify_result = self.analyze(requirement)
        
        # 2. 如果需要交互且有回调
        if clarify_result.needs_interaction and self.interaction_callback:
            answered_questions = self.interaction_callback(clarify_result.questions)
            for i, q in enumerate(clarify_result.questions):
                if i < len(answered_questions):
                    q.answer = answered_questions[i].answer
            
            # 重新生成澄清结果
            clarify_result = self.finalize(clarify_result)
        
        # 3. 返回结果
        if clarify_result.clarity_level == ClarityLevel.AMBIGUOUS:
            return self._failure(
                errors=["需求过于模糊，必须先澄清"],
                clarify_result=clarify_result.to_dict(),
            )
        
        return self._success(
            clarify_result=clarify_result.to_dict(),
            clarified_requirement=clarify_result.clarified_requirement.to_dict() 
                if clarify_result.clarified_requirement else None,
        )
    
    def analyze(self, requirement: str) -> ClarifyResult:
        """分析需求，生成澄清问题
        
        Args:
            requirement: 需求描述
            
        Returns:
            ClarifyResult
        """
        questions = []
        clarity_level = ClarityLevel.CLEAR
        
        # 1. 检测模糊关键词
        for keyword in self.AMBIGUOUS_KEYWORDS:
            if keyword in requirement.lower():
                clarity_level = ClarityLevel.NEEDS_CLARIFICATION
                break
        
        # 2. 检测需要澄清的模式
        for pattern in self.NEED_CLARIFICATION_PATTERNS:
            if re.search(pattern, requirement):
                clarity_level = ClarityLevel.NEEDS_CLARIFICATION
                break
        
        # 3. 生成问题
        questions.extend(self._generate_scope_questions(requirement))
        questions.extend(self._generate_data_questions(requirement))
        questions.extend(self._generate_api_questions(requirement))
        questions.extend(self._generate_auth_questions(requirement))
        questions.extend(self._generate_acceptance_questions(requirement))
        
        # 4. 如果有必须回答的问题，升级清晰度级别
        if any(q.importance == "required" for q in questions):
            clarity_level = ClarityLevel.NEEDS_CLARIFICATION
        
        # 5. 尝试自动提取信息
        clarified = self._auto_extract(requirement)
        
        return ClarifyResult(
            clarity_level=clarity_level,
            questions=questions,
            clarified_requirement=clarified,
            original_requirement=requirement,
        )
    
    def finalize(self, result: ClarifyResult) -> ClarifyResult:
        """根据回答完善澄清结果
        
        Args:
            result: 带有回答的澄清结果
            
        Returns:
            更新后的 ClarifyResult
        """
        if not result.clarified_requirement:
            result.clarified_requirement = ClarifiedRequirement(
                summary=result.original_requirement
            )
        
        clarified = result.clarified_requirement
        
        # 根据回答更新澄清结果
        for q in result.questions:
            if q.answer:
                if q.category == QuestionCategory.SCOPE:
                    if "包含" in q.question:
                        clarified.scope_included.append(q.answer)
                    elif "不包含" in q.question:
                        clarified.scope_excluded.append(q.answer)
                
                elif q.category == QuestionCategory.DATA:
                    if "表" in q.question:
                        clarified.tables.extend(q.answer.split(","))
                    elif "字段" in q.question:
                        clarified.new_fields.extend(q.answer.split(","))
                
                elif q.category == QuestionCategory.AUTH:
                    clarified.permissions.append(q.answer)
                
                elif q.category == QuestionCategory.ACCEPTANCE:
                    clarified.acceptance_criteria.append(q.answer)
        
        # 更新清晰度级别
        if not result.required_unanswered:
            result.clarity_level = ClarityLevel.CLEAR
        
        return result
    
    def _generate_scope_questions(self, requirement: str) -> List[ClarifyQuestion]:
        """生成范围相关问题"""
        questions = []
        
        # 如果需求较短或模糊
        if len(requirement) < 50:
            questions.append(ClarifyQuestion(
                id="scope-1",
                category=QuestionCategory.SCOPE,
                question="这个功能的具体范围是什么？请列出包含的功能点。",
                importance="required",
            ))
        
        return questions
    
    def _generate_data_questions(self, requirement: str) -> List[ClarifyQuestion]:
        """生成数据相关问题"""
        questions = []
        
        # 检测是否涉及数据操作
        data_keywords = ["导入", "导出", "保存", "删除", "修改", "查询", "列表"]
        if any(kw in requirement for kw in data_keywords):
            # 尝试自动识别相关表
            detected_tables = []
            for keyword, (table, _) in self.MODULE_KEYWORDS.items():
                if keyword in requirement:
                    detected_tables.append(table)
            
            if not detected_tables:
                questions.append(ClarifyQuestion(
                    id="data-1",
                    category=QuestionCategory.DATA,
                    question="这个功能涉及哪些数据表？",
                    importance="optional",
                    options=["daily_reports", "ad_accounts", "projects", "topup_requests"],
                ))
        
        return questions
    
    def _generate_api_questions(self, requirement: str) -> List[ClarifyQuestion]:
        """生成 API 相关问题"""
        questions = []
        
        # 如果是后端相关需求
        backend_keywords = ["API", "接口", "后端", "服务"]
        if any(kw in requirement for kw in backend_keywords):
            questions.append(ClarifyQuestion(
                id="api-1",
                category=QuestionCategory.API,
                question="需要哪些 API 端点？请描述 HTTP 方法和路径。",
                importance="optional",
            ))
        
        return questions
    
    def _generate_auth_questions(self, requirement: str) -> List[ClarifyQuestion]:
        """生成权限相关问题"""
        questions = []
        
        # 尝试自动识别角色
        detected_role = None
        for keyword, role in self.ROLE_KEYWORDS.items():
            if keyword in requirement:
                detected_role = role
                break
        
        if not detected_role:
            questions.append(ClarifyQuestion(
                id="auth-1",
                category=QuestionCategory.AUTH,
                question="这个功能的目标用户是谁？",
                importance="optional",
                options=["pitcher", "finance", "project_owner", "account_manager", "admin"],
            ))
        
        return questions
    
    def _generate_acceptance_questions(self, requirement: str) -> List[ClarifyQuestion]:
        """生成验收相关问题"""
        questions = []
        
        # 总是询问验收标准
        questions.append(ClarifyQuestion(
            id="acceptance-1",
            category=QuestionCategory.ACCEPTANCE,
            question="如何判断这个功能已经完成？请列出验收标准。",
            importance="optional",
        ))
        
        return questions
    
    def _auto_extract(self, requirement: str) -> ClarifiedRequirement:
        """自动提取需求信息
        
        Args:
            requirement: 需求描述
            
        Returns:
            ClarifiedRequirement
        """
        clarified = ClarifiedRequirement(summary=requirement)
        
        # 1. 识别角色
        for keyword, role in self.ROLE_KEYWORDS.items():
            if keyword in requirement:
                clarified.user_role = role
                clarified.permissions.append(role)
                break
        
        # 2. 识别模块和表
        for keyword, (table, default_role) in self.MODULE_KEYWORDS.items():
            if keyword in requirement:
                clarified.tables.append(table)
                if not clarified.user_role:
                    clarified.user_role = default_role
                    clarified.permissions.append(default_role)
        
        # 3. 识别操作类型
        if "导出" in requirement or "export" in requirement.lower():
            clarified.scope_included.append("数据导出")
            clarified.api_endpoints.append({
                "method": "GET",
                "path": f"/api/v1/{clarified.tables[0] if clarified.tables else 'data'}/export",
                "description": "导出数据",
            })
        
        if "导入" in requirement or "import" in requirement.lower():
            clarified.scope_included.append("数据导入")
            clarified.api_endpoints.append({
                "method": "POST",
                "path": f"/api/v1/{clarified.tables[0] if clarified.tables else 'data'}/import",
                "description": "导入数据",
            })
        
        if "列表" in requirement or "list" in requirement.lower():
            clarified.scope_included.append("数据列表")
        
        if "详情" in requirement or "detail" in requirement.lower():
            clarified.scope_included.append("数据详情")
        
        # 4. 提取通用验收标准
        if clarified.scope_included:
            for scope in clarified.scope_included:
                clarified.acceptance_criteria.append(f"{scope}功能可用")
        
        return clarified


# ============================================================
# 便捷函数
# ============================================================

def clarify_requirement(
    requirement: str,
    interaction_callback: Optional[Callable] = None,
) -> ClarifyResult:
    """快速澄清需求
    
    Args:
        requirement: 需求描述
        interaction_callback: 交互回调
        
    Returns:
        ClarifyResult
    """
    phase = ClarifyPhase(interaction_callback=interaction_callback)
    return phase.analyze(requirement)


def auto_clarify(requirement: str) -> ClarifiedRequirement:
    """自动澄清需求 (无交互)
    
    Args:
        requirement: 需求描述
        
    Returns:
        ClarifiedRequirement
    """
    phase = ClarifyPhase()
    result = phase.analyze(requirement)
    return result.clarified_requirement or ClarifiedRequirement(summary=requirement)

