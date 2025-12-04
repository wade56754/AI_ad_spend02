@echo off
cd /d D:\git\1108\AI_ad_spend02
D:\git\1108\AI_ad_spend02\.venv\Scripts\python.exe -m pytest agent_platform\tests\test_mcp_server.py agent_platform\tests\test_mcp_server_agents.py agent_platform\tests\test_skills_registry.py -v --tb=line > test_results.log 2>&1
echo Test execution completed
