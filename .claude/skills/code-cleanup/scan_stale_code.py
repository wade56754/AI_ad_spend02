#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stale Code Scanner - Detect commented code, old TODOs, and debug statements.
Usage: python scan_stale_code.py <directory> [--todo-days 90] [--no-debug]
"""

import re
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Iterator, Optional

@dataclass
class Issue:
    type: str
    file: str
    line: int
    code: str
    confidence: str
    suggestion: str

# Patterns that indicate commented-out code (not regular comments)
CODE_PATTERNS = [
    r'^\s*(def|class|import|from|return|if|for|while|try|except)\s+',
    r'^\s*\w+\s*=\s*',           # assignment
    r'^\s*\w+\.\w+\s*\(',        # method call
    r'^\s*\w+\s*\([^)]*\)\s*$',  # function call
    r'^\s*(const|let|var|function|async|await|export|import)\s+',
]

# Debug statement patterns
DEBUG_PATTERNS = [
    (r'\bprint\s*\([^)]*\)', 'print()'),
    (r'\bconsole\.(log|debug|info|warn|error)\s*\(', 'console.log()'),
    (r'\bdebugger\b', 'debugger'),
    (r'\bpdb\.set_trace\s*\(', 'pdb.set_trace()'),
    (r'\bbreakpoint\s*\(\s*\)', 'breakpoint()'),
    (r'\bimport\s+pdb\b', 'import pdb'),
    (r'\bfrom\s+pdb\s+import\b', 'from pdb import'),
]

def looks_like_code(text: str) -> bool:
    """Check if text looks like commented-out code."""
    text = text.strip()
    if len(text) < 5:
        return False
    
    for pattern in CODE_PATTERNS:
        if re.match(pattern, text):
            return True
    return False

def parse_todo_date(text: str) -> Optional[datetime]:
    """Try to extract date from TODO comment."""
    date_patterns = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2024-01-15 or 2024/01/15
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 01-15-2024 or 01/15/2024
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1).replace('/', '-')
            try:
                # Try YYYY-MM-DD first
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    # Try MM-DD-YYYY
                    return datetime.strptime(date_str, '%m-%d-%Y')
                except ValueError:
                    pass
    return None

def scan_file(filepath: Path, todo_days: int, check_debug: bool) -> list[Issue]:
    """Scan a single file for stale code."""
    issues = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
        lines = content.split('\n')
        now = datetime.now()
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for commented-out code
            comment_prefixes = [('#', 1), ('//', 2)]
            for prefix, skip_len in comment_prefixes:
                if stripped.startswith(prefix):
                    comment_content = stripped[skip_len:].strip()
                    if looks_like_code(comment_content):
                        issues.append(Issue(
                            type='commented_code',
                            file=str(filepath),
                            line=i,
                            code=stripped[:80],
                            confidence='medium',
                            suggestion='Remove commented-out code or restore it'
                        ))
                    break
            
            # Check for stale TODOs
            todo_match = re.search(r'\b(TODO|FIXME|HACK|XXX)\b[:\s]*(.+)?', line, re.IGNORECASE)
            if todo_match:
                todo_type = todo_match.group(1).upper()
                todo_text = todo_match.group(2) or ''
                
                todo_date = parse_todo_date(todo_text)
                if todo_date:
                    days_old = (now - todo_date).days
                    if days_old > todo_days:
                        issues.append(Issue(
                            type='stale_todo',
                            file=str(filepath),
                            line=i,
                            code=stripped[:80],
                            confidence='high',
                            suggestion=f'{todo_type} is {days_old} days old - resolve or remove'
                        ))
                else:
                    # TODO without date
                    issues.append(Issue(
                        type='undated_todo',
                        file=str(filepath),
                        line=i,
                        code=stripped[:80],
                        confidence='low',
                        suggestion=f'{todo_type} has no date - consider adding one'
                    ))
            
            # Check for debug statements
            if check_debug:
                for pattern, name in DEBUG_PATTERNS:
                    if re.search(pattern, line):
                        issues.append(Issue(
                            type='debug_code',
                            file=str(filepath),
                            line=i,
                            code=stripped[:80],
                            confidence='high',
                            suggestion=f'Remove debug statement: {name}'
                        ))
                        break  # Only report once per line
    
    except UnicodeDecodeError:
        pass
    except Exception as e:
        print(f"Warning: Error scanning {filepath}: {e}", file=sys.stderr)
    
    return issues

def should_ignore(filepath: Path) -> bool:
    """Check if file should be ignored."""
    path_str = str(filepath)
    ignore_dirs = ['__pycache__', 'node_modules', '.git', 'venv', '.venv', 'dist', 'build']
    return any(d in path_str for d in ignore_dirs)

def scan_directory(target: Path, todo_days: int, check_debug: bool) -> Iterator[Issue]:
    """Scan directory for stale code."""
    extensions = ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx']
    
    for ext in extensions:
        for filepath in target.rglob(ext):
            if should_ignore(filepath):
                continue
            yield from scan_file(filepath, todo_days, check_debug)

def main():
    parser = argparse.ArgumentParser(
        description='Scan for stale code (commented code, old TODOs, debug statements)'
    )
    parser.add_argument('target', help='Directory to scan')
    parser.add_argument('--todo-days', type=int, default=90,
                        help='TODOs older than this are flagged (default: 90)')
    parser.add_argument('--no-debug', action='store_true',
                        help='Skip debug statement detection')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json',
                        help='Output format (default: json)')
    args = parser.parse_args()
    
    target = Path(args.target)
    if not target.exists():
        print(f'Error: {target} not found', file=sys.stderr)
        sys.exit(1)
    
    issues = list(scan_directory(target, args.todo_days, not args.no_debug))
    
    result = {
        'scan_time': datetime.now().isoformat(),
        'target': str(target.absolute()),
        'config': {
            'todo_days': args.todo_days,
            'check_debug': not args.no_debug
        },
        'issues': [asdict(i) for i in issues],
        'summary': {
            'total': len(issues),
            'high': len([i for i in issues if i.confidence == 'high']),
            'medium': len([i for i in issues if i.confidence == 'medium']),
            'low': len([i for i in issues if i.confidence == 'low']),
            'by_type': {}
        }
    }
    
    # Count by type
    for issue in issues:
        result['summary']['by_type'][issue.type] = \
            result['summary']['by_type'].get(issue.type, 0) + 1
    
    if args.format == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"=== Stale Code Scan: {target} ===")
        print(f"Found {len(issues)} issues\n")
        
        for issue_type in ['debug_code', 'stale_todo', 'commented_code', 'undated_todo']:
            type_issues = [i for i in issues if i.type == issue_type]
            if type_issues:
                print(f"[{issue_type}] ({len(type_issues)} issues)")
                for i in type_issues[:5]:  # Show first 5
                    print(f"  {i.file}:{i.line}")
                    print(f"    {i.code[:60]}")
                if len(type_issues) > 5:
                    print(f"  ... and {len(type_issues) - 5} more")
                print()

if __name__ == '__main__':
    main()
