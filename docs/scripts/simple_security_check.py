#!/usr/bin/env python3
"""
AI财务系统简化安全检查脚本
检查敏感信息泄露和配置安全性
"""

import os
import re
import sys
import secrets
from pathlib import Path
from typing import List, Dict


def check_sensitive_files(project_root: str) -> List[Dict]:
    """检查敏感文件"""
    issues = []
    root = Path(project_root)

    # 检查是否存在敏感文件
    sensitive_files = [
        '.env', '.env.backup', '.env.production',
        'secrets.yml', 'secrets.yaml',
        'private.key', 'certificate.pem'
    ]

    for file_name in sensitive_files:
        file_path = root / file_name
        if file_path.exists():
            # 检查文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查是否包含真实密钥
                if len(content) > 100 and 'example' not in content.lower():
                    issues.append({
                        'type': 'sensitive_file_exists',
                        'file': file_name,
                        'severity': 'high',
                        'description': f'发现敏感文件: {file_name}'
                    })
            except:
                pass

    return issues


def check_gitignore(project_root: str) -> List[Dict]:
    """检查.gitignore配置"""
    issues = []
    root = Path(project_root)

    gitignore_file = root / '.gitignore'
    if not gitignore_file.exists():
        issues.append({
            'type': 'missing_gitignore',
            'severity': 'high',
            'description': '缺少.gitignore文件'
        })
        return issues

    try:
        with open(gitignore_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查必要的忽略规则
        required_patterns = ['.env', '*.key', '*.pem', 'secrets.yml']

        for pattern in required_patterns:
            if pattern not in content:
                issues.append({
                    'type': 'missing_gitignore_pattern',
                    'severity': 'medium',
                    'description': f'.gitignore缺少规则: {pattern}'
                })

    except Exception as e:
        issues.append({
            'type': 'gitignore_read_error',
            'severity': 'low',
            'description': f'无法读取.gitignore: {e}'
        })

    return issues


def check_env_configuration(project_root: str) -> List[Dict]:
    """检查环境变量配置"""
    issues = []
    root = Path(project_root)

    # 检查.env.example是否存在
    env_example = root / '.env.example'
    if not env_example.exists():
        issues.append({
            'type': 'missing_env_example',
            'severity': 'medium',
            'description': '缺少.env.example模板文件'
        })

    # 检查当前.env文件
    env_file = root / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查生产环境配置
            if 'ENV_NAME=production' in content:
                if 'DEBUG=true' in content:
                    issues.append({
                        'type': 'production_debug_enabled',
                        'severity': 'high',
                        'description': '生产环境开启了调试模式'
                    })

            # 检查JWT密钥长度
            jwt_match = re.search(r'JWT_SECRET=([^\s\n]+)', content)
            if jwt_match:
                jwt_secret = jwt_match.group(1)
                if len(jwt_secret) < 64:
                    issues.append({
                        'type': 'weak_jwt_secret',
                        'severity': 'high',
                        'description': f'JWT密钥长度不足: {len(jwt_secret)}字符'
                    })

            # 检查是否包含明显的示例数据
            if 'example.com' in content or 'your_' in content:
                issues.append({
                    'type': 'example_data_in_env',
                    'severity': 'medium',
                    'description': '.env文件包含示例数据'
                })

        except Exception as e:
            issues.append({
                'type': 'env_read_error',
                'severity': 'low',
                'description': f'无法读取.env文件: {e}'
            })

    return issues


def generate_secure_secrets() -> Dict[str, str]:
    """生成安全密钥"""
    return {
        'jwt_secret': secrets.token_urlsafe(64),
        'encryption_key': secrets.token_urlsafe(32),
        'database_password': secrets.token_urlsafe(16) + 'A1!',
        'api_key': secrets.token_urlsafe(32),
    }


def run_security_check(project_root: str) -> Dict:
    """运行安全检查"""
    print("=" * 60)
    print("AI财务系统安全检查报告")
    print("=" * 60)

    all_issues = []

    # 执行各项检查
    all_issues.extend(check_sensitive_files(project_root))
    all_issues.extend(check_gitignore(project_root))
    all_issues.extend(check_env_configuration(project_root))

    # 分类问题
    high_issues = [i for i in all_issues if i['severity'] == 'high']
    medium_issues = [i for i in all_issues if i['severity'] == 'medium']
    low_issues = [i for i in all_issues if i['severity'] == 'low']

    # 打印统计
    print(f"\n检查结果统计:")
    print(f"  总问题数: {len(all_issues)}")
    print(f"  高危问题: {len(high_issues)}")
    print(f"  中危问题: {len(medium_issues)}")
    print(f"  低危问题: {len(low_issues)}")

    # 打印高危问题
    if high_issues:
        print(f"\n[高危问题] ({len(high_issues)}个):")
        for i, issue in enumerate(high_issues, 1):
            print(f"  {i}. {issue['description']}")
            if 'file' in issue:
                print(f"     文件: {issue['file']}")

    # 打印中危问题
    if medium_issues:
        print(f"\n[中危问题] ({len(medium_issues)}个):")
        for i, issue in enumerate(medium_issues, 1):
            print(f"  {i}. {issue['description']}")
            if 'file' in issue:
                print(f"     文件: {issue['file']}")

    # 打印低危问题
    if low_issues:
        print(f"\n[低危问题] ({len(low_issues)}个):")
        for i, issue in enumerate(low_issues, 1):
            print(f"  {i}. {issue['description']}")

    # 安全建议
    print(f"\n[安全建议]:")
    if high_issues:
        print("  1. 立即修复所有高危问题")
    if medium_issues:
        print("  2. 尽快修复中危问题")
    print("  3. 定期运行安全检查")
    print("  4. 使用强密码和随机密钥")
    print("  5. 确保敏感文件不被提交到版本控制")

    # 生成安全密钥
    print(f"\n[建议的安全密钥]:")
    secrets_dict = generate_secure_secrets()
    print(f"  JWT_SECRET={secrets_dict['jwt_secret']}")
    print(f"  ENCRYPTION_KEY={secrets_dict['encryption_key']}")
    print(f"  DATABASE_PASSWORD={secrets_dict['database_password']}")
    print(f"  API_KEY={secrets_dict['api_key']}")

    print("\n" + "=" * 60)

    return {
        'total_issues': len(all_issues),
        'high_issues': len(high_issues),
        'medium_issues': len(medium_issues),
        'low_issues': len(low_issues),
        'secrets': secrets_dict
    }


def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 运行安全检查
    report = run_security_check(project_root)

    # 设置退出码
    if report['high_issues'] > 0:
        print("\n[结果] 发现高危安全问题，请立即修复！")
        sys.exit(1)
    elif report['medium_issues'] > 0:
        print("\n[结果] 发现中危安全问题，建议尽快修复！")
        sys.exit(2)
    else:
        print("\n[结果] 安全检查通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()