#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2A 自动执行脚本（非交互模式）
"""

import os
import sys
import subprocess

# 修改 execute_phase2a.py 为自动模式
script_path = os.path.join(os.path.dirname(__file__), 'execute_phase2a.py')

# 使用 subprocess 传递 "yes" 作为输入
process = subprocess.Popen(
    [sys.executable, script_path],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# 发送 "yes" 作为确认
output, _ = process.communicate(input='yes\n')

print(output)
sys.exit(process.returncode)
