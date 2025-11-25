"""
数据库测试 Skill - 执行 db_invariants_test_v2.sql
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import re


class DBTestSkill:
    """数据库测试技能"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化数据库测试技能
        
        Args:
            base_path: 项目根路径
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent.parent
        else:
            self.base_path = Path(base_path)
    
    def get_test_script_path(self) -> Path:
        """获取测试脚本路径"""
        return self.base_path / "backend" / "db" / "db_invariants_test_v2.sql"
    
    def get_test_cases_path(self) -> Path:
        """获取测试用例文档路径"""
        return self.base_path / "backend" / "db" / "TEST_CASES_v2.0.md"
    
    def parse_test_cases(self) -> Dict[str, Dict[str, str]]:
        """
        解析测试用例文档，提取用例编号和优先级
        
        Returns:
            测试用例信息字典 {tc_id: {priority: str, module: str}}
        """
        test_cases_path = self.get_test_cases_path()
        if not test_cases_path.exists():
            return {}
        
        content = test_cases_path.read_text(encoding='utf-8')
        test_case_info = {}
        current_priority = None
        
        # 匹配优先级标题
        priority_pattern = r'## (\d+)\. (P\d+) 测试用例'
        for line in content.splitlines():
            priority_match = re.match(priority_pattern, line)
            if priority_match:
                current_priority = priority_match.group(2)
            
            # 匹配测试用例编号
            tc_match = re.search(r'#### (TC-[A-Z]+-\d+):', line)
            if tc_match and current_priority:
                tc_id = tc_match.group(1)
                test_case_info[tc_id] = {
                    'priority': current_priority,
                    'module': tc_id.split('-')[1]
                }
        
        # 集成测试用例
        flow_tc_pattern = r'#### (TC-FLOW-\d+):'
        for line in content.splitlines():
            flow_match = re.search(flow_tc_pattern, line)
            if flow_match:
                tc_id = flow_match.group(1)
                test_case_info[tc_id] = {
                    'priority': '集成',
                    'module': 'FLOW'
                }
        
        return test_case_info
    
    def execute_test(self, project_id: str) -> Dict[str, Any]:
        """
        执行数据库不变量测试
        
        Args:
            project_id: Supabase 项目 ID
            
        Returns:
            测试执行结果
            
        Note:
            此方法需要通过 Supabase MCP 执行测试脚本
        """
        test_script_path = self.get_test_script_path()
        if not test_script_path.exists():
            return {
                "success": False,
                "error": f"Test script not found: {test_script_path}"
            }
        
        # TODO: 通过 Supabase MCP 执行测试脚本
        # 这里需要集成 Supabase MCP 工具
        
        return {
            "success": True,
            "message": "Test execution initiated",
            "script_path": str(test_script_path)
        }
    
    def parse_test_results(self, output: str) -> Dict[str, List[str]]:
        """
        解析测试执行结果
        
        Args:
            output: 测试执行输出
            
        Returns:
            解析结果 {passed: [...], failed: [...]}
        """
        passed = re.findall(r'PASS: (TC-[A-Z]+-\d+)', output)
        failed = re.findall(r'TEST_FAILED \[(TC-[A-Z]+-\d+)\]: (.+)', output)
        
        return {
            "passed": passed,
            "failed": [{"tc_id": tc_id, "reason": reason} for tc_id, reason in failed]
        }

