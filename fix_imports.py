#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入路径自动修复脚本
将所有短路径导入统一改为以 backend 为根的绝对导入
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


class ImportFixer:
    """导入路径修复器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixed_files = 0
        self.total_replacements = 0

        # 定义需要替换的导入模式
        # 格式：(正则模式, 替换函数)
        self.patterns = [
            # from core.xxx import yyy
            (r'^(\s*)from core\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.core.{m.group(2)} import {m.group(3)}'),

            # import core.xxx
            (r'^(\s*)import core\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.core.{m.group(2)}'),

            # from models.xxx import yyy
            (r'^(\s*)from models\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.models.{m.group(2)} import {m.group(3)}'),

            # from models import xxx
            (r'^(\s*)from models import (.+)$',
             lambda m: f'{m.group(1)}from backend.models import {m.group(2)}'),

            # import models.xxx
            (r'^(\s*)import models\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.models.{m.group(2)}'),

            # from routers.xxx import yyy
            (r'^(\s*)from routers\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.routers.{m.group(2)} import {m.group(3)}'),

            # import routers.xxx
            (r'^(\s*)import routers\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.routers.{m.group(2)}'),

            # from services.xxx import yyy
            (r'^(\s*)from services\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.services.{m.group(2)} import {m.group(3)}'),

            # import services.xxx
            (r'^(\s*)import services\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.services.{m.group(2)}'),

            # from schemas.xxx import yyy
            (r'^(\s*)from schemas\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.schemas.{m.group(2)} import {m.group(3)}'),

            # import schemas.xxx
            (r'^(\s*)import schemas\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.schemas.{m.group(2)}'),

            # from exceptions.xxx import yyy
            (r'^(\s*)from exceptions\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.exceptions.{m.group(2)} import {m.group(3)}'),

            # import exceptions.xxx
            (r'^(\s*)import exceptions\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.exceptions.{m.group(2)}'),

            # from deps.xxx import yyy
            (r'^(\s*)from deps\.(\S+) import (.+)$',
             lambda m: f'{m.group(1)}from backend.deps.{m.group(2)} import {m.group(3)}'),

            # import deps.xxx
            (r'^(\s*)import deps\.(\S+)$',
             lambda m: f'{m.group(1)}import backend.deps.{m.group(2)}'),
        ]

        # 编译正则表达式
        self.compiled_patterns = [
            (re.compile(pattern, re.MULTILINE), replacer)
            for pattern, replacer in self.patterns
        ]

    def fix_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        修复单个文件的导入路径

        Returns:
            (是否修改, 替换次数)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"  [ERROR] 无法读取文件 {file_path}: {e}")
            return False, 0

        original_content = content
        replacements = 0

        # 逐行处理，避免误替换字符串或注释中的内容
        lines = content.split('\n')
        new_lines = []

        for line in lines:
            # 跳过注释行（但保留它们）
            if line.strip().startswith('#'):
                new_lines.append(line)
                continue

            # 跳过字符串（简单检测，不在引号内）
            if '"""' in line or "'''" in line or ('"' in line and 'import' in line and line.index('"') < line.index('import')):
                new_lines.append(line)
                continue

            # 尝试所有模式
            modified = False
            for pattern, replacer in self.compiled_patterns:
                match = pattern.match(line)
                if match:
                    new_line = replacer(match)
                    if new_line != line:
                        new_lines.append(new_line)
                        replacements += 1
                        modified = True
                        break

            if not modified:
                new_lines.append(line)

        new_content = '\n'.join(new_lines)

        # 如果有修改，写回文件
        if new_content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, replacements
            except Exception as e:
                print(f"  [ERROR] 无法写入文件 {file_path}: {e}")
                return False, 0

        return False, 0

    def fix_directory(self, directory: str) -> None:
        """修复指定目录下的所有 Python 文件"""
        dir_path = self.project_root / directory

        if not dir_path.exists():
            print(f"[WARN] 目录不存在: {dir_path}")
            return

        print(f"\n{'='*80}")
        print(f"正在修复目录: {directory}")
        print(f"{'='*80}")

        # 收集所有 Python 文件
        py_files = list(dir_path.rglob('*.py'))
        print(f"找到 {len(py_files)} 个 Python 文件")

        # 修复每个文件
        for py_file in py_files:
            relative_path = py_file.relative_to(self.project_root)
            modified, count = self.fix_file(py_file)

            if modified:
                self.fixed_files += 1
                self.total_replacements += count
                print(f"  [OK] {relative_path} - {count} replacements")
            # else:
            #     print(f"  [  ] {relative_path} - no changes needed")

    def run(self) -> None:
        """执行修复"""
        print("="*80)
        print("开始修复导入路径".center(80))
        print("="*80)

        # 修复 backend 目录
        self.fix_directory('backend')

        # 修复 tests 目录
        self.fix_directory('tests')

        # 打印总结
        print(f"\n{'='*80}")
        print("修复完成".center(80))
        print(f"{'='*80}")
        print(f"修改的文件数: {self.fixed_files}")
        print(f"总替换次数: {self.total_replacements}")
        print(f"{'='*80}\n")


if __name__ == '__main__':
    import sys

    # 获取项目根目录
    project_root = Path(__file__).parent

    # 创建修复器并运行
    fixer = ImportFixer(str(project_root))
    fixer.run()

    # 如果没有修改，退出码为 0；如果有修改，退出码为修改的文件数
    sys.exit(0)
