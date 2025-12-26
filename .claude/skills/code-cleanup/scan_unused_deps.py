#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unused Dependencies Scanner - Detect unused packages in requirements.txt/package.json.
Usage: python scan_unused_deps.py <directory> [--type python|node|all]
"""

import re
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Set

@dataclass
class Issue:
    type: str
    file: str
    line: int
    code: str
    confidence: str
    suggestion: str

# Package name to import name mapping (common cases)
PYTHON_PACKAGE_MAP = {
    'pillow': 'PIL',
    'python-dotenv': 'dotenv',
    'scikit-learn': 'sklearn',
    'opencv-python': 'cv2',
    'opencv-python-headless': 'cv2',
    'beautifulsoup4': 'bs4',
    'pyyaml': 'yaml',
    'python-dateutil': 'dateutil',
    'typing-extensions': 'typing_extensions',
    'importlib-metadata': 'importlib_metadata',
}

# Node packages that are often used implicitly
NODE_IMPLICIT_DEPS = {
    'typescript', '@types/', 'eslint', 'prettier', 'jest', 'vitest',
    'webpack', 'vite', 'next', 'tailwindcss', 'postcss', 'autoprefixer',
}

def extract_python_imports(target: Path) -> Set[str]:
    """Extract all imported module names from Python files."""
    imports = set()
    
    for pyfile in target.rglob('*.py'):
        if '__pycache__' in str(pyfile) or 'venv' in str(pyfile):
            continue
        
        try:
            content = pyfile.read_text(encoding='utf-8')
            
            # Match: import xxx, from xxx import
            for match in re.finditer(r'^\s*(?:from|import)\s+([\w.]+)', content, re.MULTILINE):
                module = match.group(1).split('.')[0]
                imports.add(module.lower())
        except Exception:
            pass
    
    return imports

def extract_node_imports(target: Path) -> Set[str]:
    """Extract all imported package names from JS/TS files."""
    imports = set()
    
    for ext in ['*.js', '*.jsx', '*.ts', '*.tsx']:
        for jsfile in target.rglob(ext):
            if 'node_modules' in str(jsfile) or 'dist' in str(jsfile):
                continue
            
            try:
                content = jsfile.read_text(encoding='utf-8')
                
                # Match: import ... from 'package' or require('package')
                for match in re.finditer(r'''(?:from|require)\s*\(\s*['"]([@\w/-]+)['"]''', content):
                    pkg = match.group(1)
                    # Get the package name (first part or @scope/name)
                    if pkg.startswith('@'):
                        parts = pkg.split('/')
                        if len(parts) >= 2:
                            imports.add('/'.join(parts[:2]))
                    else:
                        imports.add(pkg.split('/')[0])
                
                # ES6 imports
                for match in re.finditer(r'''import\s+.*?\s+from\s+['"]([@\w/-]+)['"]''', content):
                    pkg = match.group(1)
                    if pkg.startswith('@'):
                        parts = pkg.split('/')
                        if len(parts) >= 2:
                            imports.add('/'.join(parts[:2]))
                    else:
                        imports.add(pkg.split('/')[0])
            except Exception:
                pass
    
    return imports

def parse_requirements(filepath: Path) -> list[tuple[str, int]]:
    """Parse requirements.txt, return list of (package, line_number)."""
    packages = []
    
    try:
        for i, line in enumerate(filepath.read_text().split('\n'), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            
            # Extract package name (before any version specifier)
            match = re.match(r'^([\w-]+)', line)
            if match:
                packages.append((match.group(1).lower(), i))
    except Exception:
        pass
    
    return packages

def parse_package_json(filepath: Path) -> list[tuple[str, str]]:
    """Parse package.json, return list of (package, dep_type)."""
    packages = []
    
    try:
        data = json.loads(filepath.read_text())
        
        for dep_type in ['dependencies', 'devDependencies']:
            if dep_type in data:
                for pkg in data[dep_type].keys():
                    packages.append((pkg, dep_type))
    except Exception:
        pass
    
    return packages

def scan_python_deps(target: Path) -> list[Issue]:
    """Check Python dependencies."""
    issues = []
    
    req_files = list(target.glob('requirements*.txt'))
    if not req_files:
        return issues
    
    imports = extract_python_imports(target)
    
    for req_file in req_files:
        packages = parse_requirements(req_file)
        
        for pkg, line in packages:
            # Get the expected import name
            import_name = PYTHON_PACKAGE_MAP.get(pkg, pkg.replace('-', '_'))
            
            if import_name.lower() not in imports:
                issues.append(Issue(
                    type='unused_python_dep',
                    file=str(req_file),
                    line=line,
                    code=pkg,
                    confidence='low',  # Could be used dynamically
                    suggestion=f'Possibly unused: {pkg} (no import of {import_name} found)'
                ))
    
    return issues

def scan_node_deps(target: Path) -> list[Issue]:
    """Check Node.js dependencies."""
    issues = []
    
    pkg_json = target / 'package.json'
    if not pkg_json.exists():
        return issues
    
    imports = extract_node_imports(target)
    packages = parse_package_json(pkg_json)
    
    for pkg, dep_type in packages:
        # Skip implicit/build dependencies
        if any(pkg.startswith(implicit) for implicit in NODE_IMPLICIT_DEPS):
            continue
        if pkg.startswith('@types/'):
            continue
        
        if pkg not in imports:
            issues.append(Issue(
                type='unused_node_dep',
                file=str(pkg_json),
                line=0,  # Can't get line number easily from JSON
                code=f'{pkg} ({dep_type})',
                confidence='low',
                suggestion=f'Possibly unused: {pkg}'
            ))
    
    return issues

def main():
    parser = argparse.ArgumentParser(
        description='Scan for unused dependencies in requirements.txt/package.json'
    )
    parser.add_argument('target', help='Directory to scan')
    parser.add_argument('--type', '-t', choices=['python', 'node', 'all'], default='all',
                        help='Type of dependencies to check (default: all)')
    parser.add_argument('--format', '-f', choices=['json', 'text'], default='json',
                        help='Output format (default: json)')
    args = parser.parse_args()
    
    target = Path(args.target)
    if not target.exists():
        print(f'Error: {target} not found', file=sys.stderr)
        sys.exit(1)
    
    issues = []
    
    if args.type in ['python', 'all']:
        issues.extend(scan_python_deps(target))
    
    if args.type in ['node', 'all']:
        issues.extend(scan_node_deps(target))
    
    result = {
        'scan_time': datetime.now().isoformat(),
        'target': str(target.absolute()),
        'issues': [asdict(i) for i in issues],
        'summary': {
            'total': len(issues),
            'python': len([i for i in issues if i.type == 'unused_python_dep']),
            'node': len([i for i in issues if i.type == 'unused_node_dep']),
        },
        'note': 'Low confidence - packages may be used dynamically or as build tools'
    }
    
    if args.format == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"=== Unused Dependencies Scan: {target} ===")
        print(f"Found {len(issues)} potentially unused dependencies\n")
        print("⚠️  Note: Low confidence - verify before removing\n")
        
        python_issues = [i for i in issues if i.type == 'unused_python_dep']
        if python_issues:
            print(f"[Python] ({len(python_issues)} packages)")
            for i in python_issues:
                print(f"  {i.code}")
            print()
        
        node_issues = [i for i in issues if i.type == 'unused_node_dep']
        if node_issues:
            print(f"[Node.js] ({len(node_issues)} packages)")
            for i in node_issues:
                print(f"  {i.code}")
            print()

if __name__ == '__main__':
    main()
