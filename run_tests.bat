@echo off
cd /d D:\git\1108\AI_ad_spend02
.venv\Scripts\python.exe -m pytest agent_platform\tests\test_mcp_server.py agent_platform\tests\test_mcp_server_agents.py agent_platform\tests\test_skills_registry.py -v --tb=line > test_output.txt 2>&1
echo Tests completed >> test_output.txt
