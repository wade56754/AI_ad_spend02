#!/bin/bash
# 监工系统一键验证脚本
# Usage: bash .claude/test_supervisor.sh

set -e
cd "$(dirname "$0")/.."

echo "=============================================="
echo "  监工系统验证 (Supervisor System Test)"
echo "=============================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC}"; }
fail() { echo -e "${RED}FAIL${NC}"; exit 1; }

# Step 1: 配置模块
echo -e "\n[Step 1] 配置模块验证"
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from lib.config import get_sot_versions, get_valid_roles
v = get_sot_versions()
r = get_valid_roles()
assert len(v) == 8, f'SoT versions: {len(v)} != 8'
assert len(r) == 7, f'Roles: {len(r)} != 7'
print(f'  SoT: {len(v)} versions, Roles: {len(r)}')
" && pass || fail

# Step 2: 进度追踪
echo -e "\n[Step 2] 进度追踪验证"
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from lib.progress_tracker import ProgressTracker
t = ProgressTracker()
t.load_tasks()
assert len(t.modules) == 11, 'Modules != 11'
assert len(t.tasks) >= 20, 'Tasks < 20'
print(f'  Modules: {len(t.modules)}, Tasks: {len(t.tasks)}')
" && pass || fail

# Step 3: 合规检查 - 违规代码拒绝
echo -e "\n[Step 3] 合规检查验证"
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from lib.compliance_checker import is_compliant
# 正常代码应通过
assert is_compliant('def hello(): pass') == True, 'Normal code rejected'
# 违规代码应拒绝
assert is_compliant('account.balance -= 100') == False, 'Bad code passed'
assert is_compliant('role == \"operator\"') == False, 'Old role passed'
print('  Normal: pass, Balance: reject, OldRole: reject')
" && pass || fail

# Step 4: 风险检测
echo -e "\n[Step 4] 风险检测验证"
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from lib.risk_detector import RiskDetector
d = RiskDetector()
r = d.detect_all()
print(f'  Detected {len(r.risks)} risks')
" && pass || fail

# Step 5: 报告生成
echo -e "\n[Step 5] 报告生成验证"
python3 -c "
import sys; sys.path.insert(0, '.claude/hooks')
from lib.report_generator import ReportGenerator
g = ReportGenerator()
c = g.generate_daily()
assert '# 项目进度日报' in c, 'Missing header'
assert '## 📊 进度概览' in c, 'Missing progress'
print(f'  Daily report: {len(c)} chars')
" && pass || fail

# Step 6: PreToolUse Hook (模拟)
echo -e "\n[Step 6] PreToolUse Hook 验证"
python3 -c "
import sys, json; sys.path.insert(0, '.claude/hooks')
from lib.compliance_checker import is_compliant

# 模拟 hook 输入
good = {'tool_name': 'Write', 'tool_input': {'content': 'def x(): pass'}}
bad = {'tool_name': 'Write', 'tool_input': {'content': 'account.balance -= 1'}}

assert is_compliant(good['tool_input']['content']) == True
assert is_compliant(bad['tool_input']['content']) == False
print('  Good code: approve, Bad code: reject')
" && pass || fail

echo -e "\n=============================================="
echo -e "  ${GREEN}All tests passed!${NC}"
echo "=============================================="
