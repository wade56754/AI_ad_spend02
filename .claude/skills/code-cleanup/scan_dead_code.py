#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dead Code Scanner - Detect unused imports, functions, classes, and variables.
Usage: python scan_dead_code.py <directory> [--format json|text] [--ignore pattern]
"""

import ast
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Iterator, Set, Dict, Tuple

@dataclass
class Issue:
    type: str
    file: str
    line: int
    code: str
    confidence: str
    suggestion: str

class DeadCodeScanner(ast.NodeVisitor):
    """AST visitor to collect definitions and usages."""
    
    def __init__(self):
        self.defined: Dict[str, Tuple[int, str]] = {}  # name -> (line, kind)
        self.used: Set[str] = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self.defined[name] = (node.lineno, 'import')
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name != '*':
                name = alias.asname or alias.name
                self.defined[name] = (node.lineno, 'import')
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        if not node.name.startswith('_'):
            self.defined[node.name] = (node.lineno, 'function')
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node):
        if not node.name.startswith('_'):
            self.defined[node.name] = (node.lineno, 'class')
        self.generic_visit(node)
    
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        # Track attribute access for better accuracy
        self.generic_visit(node)

def scan_python_file(filepath: Path) -> list[Issue]:
    """Scan a single Python file for dead code."""
    issues = []
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content)
        
        scanner = DeadCodeScanner()
        scanner.visit(tree)
        
        lines = content.split('\n')
        
        for name, (line, kind) in scanner.defined.items():
            if name not in scanner.used:
                code = lines[line - 1].strip() if line <= len(lines) else ''
                confidence = 'high' if kind == 'import' else 'medium'
                issues.append(Issue(
                    type=f'unused_{kind}',
                    file=str(filepath),
                    line=line,
                    code=code[:100],
                    confidence=confidence,
                    suggestion=f'Remove unused {kind}: {name}'
                ))
    except SyntaxError as e:
        pass  # Skip files with syntax errors
    except UnicodeDecodeError:
        pass  # Skip binary files
    except Exception as e:
        print(f"Warning: Error scanning {filepath}: {e}", file=sys.stderr)
    
    return issues

def scan_typescript_file(filepath: Path) -> list[Issue]:
    """Scan TypeScript/JavaScript file for unused imports (simplified)."""
    import re
    issues = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Extract named imports: import { x, y } from '...'
        import_pattern = r"import\s*\{([^}]+)\}\s*from\s*['\"]"
        imports = {}
        
        for i, line in enumerate(content.split('\n'), 1):
            match = re.search(import_pattern, line)
            if match:
                for name in match.group(1).split(','):
                    name = name.strip().split(' as ')[-1].strip()
                    if name:
                        imports[name] = (i, line.strip())
        
        # Check usage (simple text search)
        for name, (line, code) in imports.items():
            # Count occurrences (excluding import line itself)
            pattern = rf'\b{re.escape(name)}\b'
            matches = list(re.finditer(pattern, content))
            # If only appears once (in the import), it's unused
            if len(matches) <= 1:
                issues.append(Issue(
                    type='unused_import',
                    file=str(filepath),
                    line=line,
                    code=code[:100],
                    confidence='medium',  # Lower confidence for TS
                    suggestion=f'Possibly unused import: {name}'
                ))
    except Exception as e:
        print(f"Warning: Error scanning {filepath}: {e}", file=sys.stderr)
    
    return issues

def should_ignore(filepath: Path, patterns: list[str]) -> bool:
    """Check if file should be ignored."""
    path_str = str(filepath)
    
    # Always ignore these
    ignore_dirs = ['__pycache__', 'node_modules', '.git', 'venv', '.venv', 'dist', 'build']
    if any(d in path_str for d in ignore_dirs):
        return True
    
    # User patterns
    for pattern in patterns:
        if filepath.match(pattern):
            return True
    
    return False

def scan_directory(target: Path, ignore: list[str]) -> Iterator[Issue]:
    """Scan directory for dead code."""
    # Python files
    for pyfile in target.rglob('*.py'):
        if should_ignore(pyfile, ignore):
            continue
        yield from scan_python_file(pyfile)
    
    # TypeScript/JavaScript files
    for ext in ['*.ts', '*.tsx', '*.js', '*.jsx']:
        for tsfile in target.rglob(ext):
            if should_ignore(tsfile, ignore):
                continue
            yield from scan_typescript_file(tsfile)

def main():
    parser = argparse.ArgumentParser(
        description='Scan for dead code (unused imports, functions, classes)'
    )
    parser.add_argument('target', help='Directory to scan')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json',
                        help='Output format (default: json)')
    parser.add_argument('--ignore', '-i', action='append', default=[],
                        help='Patterns to ignore (can be used multiple times)')
    args = parser.parse_args()
    
    target = Path(args.target)
    if not target.exists():
        print(f'Error: {target} not found', file=sys.stderr)
        sys.exit(1)
    
    # Default ignore patterns
    ignore = args.ignore + ['test_*', '*_test.py', 'conftest.py', '__init__.py']
    
    issues = list(scan_directory(target, ignore))
    
    # Build result
    result = {
        'scan_time': datetime.now().isoformat(),
        'target': str(target.absolute()),
        'issues': [asdict(i) for i in issues],
        'summary': {
            'total': len(issues),
            'high': len([i for i in issues if i.confidence == 'high']),
            'medium': len([i for i in issues if i.confidence == 'medium']),
            'low': len([i for i in issues if i.confidence == 'low']),
        }
    }
    
    if args.format == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"=== Dead Code Scan: {target} ===")
        print(f"Found {len(issues)} issues\n")
        
        for conf in ['high', 'medium', 'low']:
            conf_issues = [i for i in issues if i.confidence == conf]
            if conf_issues:
                print(f"[{conf.upper()}] ({len(conf_issues)} issues)")
                for i in conf_issues:
                    print(f"  {i.file}:{i.line} - {i.type}")
                    print(f"    {i.code[:60]}...")
                print()

if __name__ == '__main__':
    main()
