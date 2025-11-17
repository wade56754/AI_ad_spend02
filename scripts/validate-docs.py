#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档规则一致性验证脚本

用途：自动检查文档是否符合项目规范
版本：v1.0
更新日期：2025-11-16
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Windows控制台UTF-8支持
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_error(msg: str):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_success(msg: str):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}[WARN] {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

# 检查1: Next.js版本统一性
def check_nextjs_version(docs_dir: Path) -> List[Tuple[str, int, str]]:
    """检查Next.js版本是否统一为16.0.2"""
    issues = []
    wrong_version_pattern = re.compile(r'Next\.js\s+(?!16\.0\.2)(\d+\.\d+\.\d+|\d+\.x)', re.IGNORECASE)

    for md_file in docs_dir.rglob('*.md'):
        if 'archive' in str(md_file):  # 跳过归档文件
            continue

        content = md_file.read_text(encoding='utf-8')
        for line_num, line in enumerate(content.splitlines(), 1):
            match = wrong_version_pattern.search(line)
            if match:
                issues.append((str(md_file.relative_to(docs_dir.parent)), line_num, match.group(1)))

    return issues

# 检查2: 错误码规范
def check_error_codes(docs_dir: Path) -> List[Tuple[str, int, str]]:
    """检查错误码是否符合SYS_*/BIZ_*/SEC_*规范"""
    issues = []
    # 匹配错误码但不符合规范的模式
    invalid_error_code = re.compile(r'"code":\s*"(?!SYS_|BIZ_|SEC_|SUCCESS)([A-Z_]+)"')

    for md_file in docs_dir.rglob('*.md'):
        if 'archive' in str(md_file):
            continue

        content = md_file.read_text(encoding='utf-8')
        for line_num, line in enumerate(content.splitlines(), 1):
            match = invalid_error_code.search(line)
            if match:
                issues.append((str(md_file.relative_to(docs_dir.parent)), line_num, match.group(1)))

    return issues

# 检查3: AppShell使用（应废弃）
def check_appshell_usage(docs_dir: Path) -> List[Tuple[str, int]]:
    """检查是否还在使用已废弃的AppShell"""
    issues = []
    appshell_pattern = re.compile(r'import.*AppShell|<AppShell|from.*AppShell', re.IGNORECASE)

    for md_file in docs_dir.rglob('*.md'):
        if 'archive' in str(md_file) or 'COMPONENT_MIGRATION' in str(md_file):
            continue  # 跳过归档和迁移指南

        content = md_file.read_text(encoding='utf-8')
        for line_num, line in enumerate(content.splitlines(), 1):
            # 排除废弃说明
            if '已废弃' in line or 'deprecated' in line.lower() or '⚠️' in line:
                continue
            if appshell_pattern.search(line):
                issues.append((str(md_file.relative_to(docs_dir.parent)), line_num))

    return issues

# 检查4: API响应格式
def check_api_response_format(docs_dir: Path) -> List[Tuple[str, int, str]]:
    """检查API响应是否使用ISO 8601格式（包含毫秒）"""
    issues = []
    # 检查时间戳格式是否包含毫秒 (.000Z 或 .sssZ)
    timestamp_pattern = re.compile(r'"timestamp":\s*"[^"]+(?<!\.000Z|\.sssZ)"')

    for md_file in docs_dir.rglob('*.md'):
        if 'archive' in str(md_file):
            continue

        content = md_file.read_text(encoding='utf-8')
        for line_num, line in enumerate(content.splitlines(), 1):
            if '"timestamp":' in line:
                match = timestamp_pattern.search(line)
                if match:
                    issues.append((str(md_file.relative_to(docs_dir.parent)), line_num, 'timestamp格式缺少毫秒部分'))

    return issues

# 检查5: 断链检测
def check_broken_links(docs_dir: Path) -> List[Tuple[str, int, str]]:
    """检查文档中的断链"""
    issues = []
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+\.md)\)')

    for md_file in docs_dir.rglob('*.md'):
        if 'archive' in str(md_file):
            continue

        content = md_file.read_text(encoding='utf-8')
        for line_num, line in enumerate(content.splitlines(), 1):
            for match in link_pattern.finditer(line):
                link_text = match.group(1)
                link_path = match.group(2)

                # 解析相对路径
                if link_path.startswith('http'):
                    continue  # 跳过外部链接

                target_path = (md_file.parent / link_path).resolve()
                if not target_path.exists():
                    issues.append((str(md_file.relative_to(docs_dir.parent)), line_num, f'断链: {link_path}'))

    return issues

def main():
    """主函数"""
    print_info("开始文档规则一致性验证...\n")

    # 项目根目录
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / 'docs'

    if not docs_dir.exists():
        print_error(f"文档目录不存在: {docs_dir}")
        sys.exit(1)

    total_issues = 0

    # 检查1: Next.js版本
    print_info("检查1: Next.js版本统一性...")
    nextjs_issues = check_nextjs_version(docs_dir)
    if nextjs_issues:
        print_error(f"发现 {len(nextjs_issues)} 处Next.js版本不一致:")
        for file, line, version in nextjs_issues[:10]:  # 最多显示10个
            print(f"  {file}:{line} - 发现版本 {version} (应为 16.0.2)")
        if len(nextjs_issues) > 10:
            print(f"  ... 还有 {len(nextjs_issues) - 10} 处问题")
        total_issues += len(nextjs_issues)
    else:
        print_success("Next.js版本检查通过")
    print()

    # 检查2: 错误码规范
    print_info("检查2: 错误码命名规范...")
    error_code_issues = check_error_codes(docs_dir)
    if error_code_issues:
        print_error(f"发现 {len(error_code_issues)} 处错误码不符合规范:")
        for file, line, code in error_code_issues[:10]:
            print(f"  {file}:{line} - 错误码 {code} (应使用 SYS_*/BIZ_*/SEC_* 前缀)")
        if len(error_code_issues) > 10:
            print(f"  ... 还有 {len(error_code_issues) - 10} 处问题")
        total_issues += len(error_code_issues)
    else:
        print_success("错误码规范检查通过")
    print()

    # 检查3: AppShell使用
    print_info("检查3: AppShell废弃检查...")
    appshell_issues = check_appshell_usage(docs_dir)
    if appshell_issues:
        print_warning(f"发现 {len(appshell_issues)} 处仍在使用AppShell:")
        for file, line in appshell_issues[:10]:
            print(f"  {file}:{line} - 应迁移到AppLayout")
        if len(appshell_issues) > 10:
            print(f"  ... 还有 {len(appshell_issues) - 10} 处问题")
        total_issues += len(appshell_issues)
    else:
        print_success("AppShell废弃检查通过")
    print()

    # 检查4: API响应格式
    print_info("检查4: API响应timestamp格式...")
    timestamp_issues = check_api_response_format(docs_dir)
    if timestamp_issues:
        print_warning(f"发现 {len(timestamp_issues)} 处timestamp格式需要改进:")
        for file, line, msg in timestamp_issues[:10]:
            print(f"  {file}:{line} - {msg}")
        if len(timestamp_issues) > 10:
            print(f"  ... 还有 {len(timestamp_issues) - 10} 处问题")
        total_issues += len(timestamp_issues)
    else:
        print_success("API响应格式检查通过")
    print()

    # 检查5: 断链检测
    print_info("检查5: 文档链接有效性...")
    link_issues = check_broken_links(docs_dir)
    if link_issues:
        print_error(f"发现 {len(link_issues)} 处断链:")
        for file, line, msg in link_issues[:10]:
            print(f"  {file}:{line} - {msg}")
        if len(link_issues) > 10:
            print(f"  ... 还有 {len(link_issues) - 10} 处问题")
        total_issues += len(link_issues)
    else:
        print_success("文档链接检查通过")
    print()

    # 总结
    print("=" * 60)
    if total_issues == 0:
        print_success("所有检查通过！文档规则一致性验证成功 🎉")
        sys.exit(0)
    else:
        print_error(f"发现 {total_issues} 处需要修复的问题")
        print_info("请参考上述输出修复问题后重新运行验证")
        sys.exit(1)

if __name__ == '__main__':
    main()
