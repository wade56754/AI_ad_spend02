#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速更新到GitHub
"""

import subprocess
import os
import sys
from datetime import datetime

def run_cmd(cmd):
    """运行命令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', cwd=os.getcwd())
    return result.returncode == 0

def main():
    """主函数"""
    print("AI广告代投系统 - 快速更新到GitHub")
    print("="*50)

    # 1. 添加所有文件
    print("添加文件到Git...")
    if not run_cmd("git add ."):
        print("添加文件失败")
        return 1

    # 2. 提交
    print("提交到本地Git...")
    commit_msg = f"""feat: 更新AI广告代投系统测试框架

时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

主要更新:
- 完善测试框架
- 优化API接口
- 增强业务逻辑
- 改进文档配置

Generated with Claude Code
"""

    # 使用文件方式避免编码问题
    with open("commit_msg.txt", "w", encoding="utf-8") as f:
        f.write(commit_msg)

    if not run_cmd("git commit -F commit_msg.txt"):
        print("提交失败")
        return 1

    # 清理临时文件
    try:
        os.remove("commit_msg.txt")
    except:
        pass

    # 3. 推送到GitHub
    print("推送到GitHub...")
    if not run_cmd("git push origin master"):
        print("推送失败 - 请检查:")
        print("1. 网络连接")
        print("2. GitHub权限")
        print("3. 分支配置")
        return 1

    print("✅ GitHub更新成功！")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)