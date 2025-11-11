#!/usr/bin/env python3
"""
AI财务系统安全检查脚本
检查敏感信息泄露和配置安全性
"""

import os
import re
import sys
import secrets
from pathlib import Path
from typing import List, Tuple, Dict


class SecurityChecker:
    """安全检查器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[Dict] = []

        # 敏感信息模式
        self.sensitive_patterns = {
            'jwt_secret': r'(?i)jwt[_-]?secret\s*=\s*["\']?([^"\'\s]{20,})["\']?',
            'database_password': r'postgresql://[^:]+:([^@\s]+)@',
            'api_key': r'(?i)api[_-]?key\s*=\s*["\']?([^"\'\s]{16,})["\']?',
            'supabase_key': r'supabase[_-]?key\s*=\s*["\']?([^"\'\s]{20,})["\']?',
            'encryption_key': r'(?i)encryption[_-]?key\s*=\s*["\']?([^"\'\s]{16,})["\']?',
            'password': r'(?i)password\s*=\s*["\']?([^"\'\s]{6,})["\']?',
        }

        # 弱密码模式
        self.weak_password_patterns = [
            r'(?i)(password|123456|admin|root|test|dev)',
            r'(?i)(qwerty|abc123|password123)',
            r'(?i)(pass|pwd).*\d{1,3}$',
        ]

    def check_sensitive_info_leakage(self) -> List[Dict]:
        """检查敏感信息泄露"""
        print("[*] 检查敏感信息泄露...")

        # 检查.env文件
        env_file = self.project_root / '.env'
        if env_file.exists():
            issues = self._check_file_for_secrets(env_file)
            self.issues.extend(issues)

        # 检查配置文件
        config_files = [
            'config.py', 'settings.py', 'config.yaml', 'config.yml',
            'docker-compose.yml', 'docker-compose.yaml'
        ]

        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                issues = self._check_file_for_secrets(file_path)
                self.issues.extend(issues)

        return self.issues

    def _check_file_for_secrets(self, file_path: Path) -> List[Dict]:
        """检查文件中的敏感信息"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    for pattern_name, pattern in self.sensitive_patterns.items():
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            secret_value = match.group(1) if match.groups() else match.group(0)

                            # 检查是否是明显的示例数据
                            if self._is_example_data(secret_value):
                                continue

                            issues.append({
                                'type': 'sensitive_info',
                                'file': str(file_path),
                                'line': line_num,
                                'pattern': pattern_name,
                                'value': secret_value[:10] + '...' if len(secret_value) > 10 else secret_value,
                                'severity': 'high',
                                'description': f'发现敏感信息: {pattern_name}'
                            })

                    # 检查弱密码
                    for weak_pattern in self.weak_password_patterns:
                        if re.search(weak_pattern, line) and '=' in line:
                            issues.append({
                                'type': 'weak_password',
                                'file': str(file_path),
                                'line': line_num,
                                'pattern': 'weak_password',
                                'severity': 'medium',
                                'description': '发现可能的弱密码'
                            })

        except Exception as e:
            issues.append({
                'type': 'file_error',
                'file': str(file_path),
                'severity': 'low',
                'description': f'无法读取文件: {e}'
            })

        return issues

    def _is_example_data(self, value: str) -> bool:
        """判断是否是示例数据"""
        example_indicators = [
            'example', 'test', 'dev', 'demo', 'sample',
            'your_', 'replace_', 'xxx', 'yyy',
            'localhost', '127.0.0.1'
        ]

        value_lower = value.lower()
        return any(indicator in value_lower for indicator in example_indicators)

    def check_gitignore_security(self) -> List[Dict]:
        """检查.gitignore文件安全性"""
        print("🔍 检查.gitignore安全性...")

        gitignore_file = self.project_root / '.gitignore'
        issues = []

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

                # 检查是否忽略了敏感文件
                required_ignores = [
                    '.env', '*.env', 'config.env', 'secrets.yml',
                    '*.key', '*.pem', '*.crt',
                    'node_modules/', '__pycache__/', '.pytest_cache/',
                    '*.log', 'logs/', '.DS_Store'
                ]

                for required_ignore in required_ignores:
                    if required_ignore not in content:
                        issues.append({
                            'type': 'missing_gitignore_rule',
                            'severity': 'medium',
                            'description': f'.gitignore中缺少: {required_ignore}'
                        })

        except Exception as e:
            issues.append({
                'type': 'gitignore_error',
                'severity': 'low',
                'description': f'无法读取.gitignore文件: {e}'
            })

        return issues

    def check_configuration_security(self) -> List[Dict]:
        """检查配置安全性"""
        print("🔍 检查配置安全性...")

        issues = []

        # 检查.env.example是否存在
        env_example = self.project_root / '.env.example'
        if not env_example.exists():
            issues.append({
                'type': 'missing_env_example',
                'severity': 'medium',
                'description': '缺少.env.example模板文件'
            })

        # 检查环境变量配置
        env_file = self.project_root / '.env'
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # 检查是否是开发环境配置
                    if 'ENV_NAME=production' in content:
                        # 生产环境安全检查
                        if 'DEBUG=true' in content:
                            issues.append({
                                'type': 'production_debug',
                                'severity': 'high',
                                'description': '生产环境开启了调试模式'
                            })

                        if 'localhost' in content or '127.0.0.1' in content:
                            issues.append({
                                'type': 'production_localhost',
                                'severity': 'medium',
                                'description': '生产环境包含localhost配置'
                            })

                    # 检查JWT密钥长度
                    jwt_match = re.search(r'JWT_SECRET=([^\s]+)', content)
                    if jwt_match:
                        jwt_secret = jwt_match.group(1)
                        if len(jwt_secret) < 64:
                            issues.append({
                                'type': 'weak_jwt_secret',
                                'severity': 'high',
                                'description': f'JWT密钥长度不足: {len(jwt_secret)}字符'
                            })

            except Exception as e:
                issues.append({
                    'type': 'env_check_error',
                    'severity': 'low',
                    'description': f'无法检查.env文件: {e}'
                })

        return issues

    def check_file_permissions(self) -> List[Dict]:
        """检查文件权限"""
        print("🔍 检查文件权限...")

        issues = []

        # 检查敏感文件的权限
        sensitive_files = ['.env', '.env.example', 'config.py']

        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                # 在Windows上，我们主要检查文件是否可被其他用户读取
                try:
                    stat_info = file_path.stat()
                    mode = oct(stat_info.st_mode)[-3:]

                    # 如果其他用户可读，则存在安全风险
                    if mode[2] in ['4', '5', '6', '7']:  # 其他用户有读权限
                        issues.append({
                            'type': 'file_permission',
                            'file': str(file_path),
                            'severity': 'medium',
                            'description': f'文件权限过于开放: {mode}',
                            'current_permission': mode
                        })
                except Exception:
                    # Windows系统可能不支持权限检查
                    pass

        return issues

    def generate_secure_secrets(self) -> Dict[str, str]:
        """生成安全的密钥"""
        print("🔐 生成安全的密钥...")

        return {
            'jwt_secret': secrets.token_urlsafe(64),
            'encryption_key': secrets.token_urlsafe(32),
            'database_password': self._generate_strong_password(),
            'api_key': secrets.token_urlsafe(32),
        }

    def _generate_strong_password(self, length: int = 16) -> str:
        """生成强密码"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def run_full_security_check(self) -> Dict:
        """运行完整的安全检查"""
        print("开始AI财务系统安全检查...")
        print("=" * 50)

        all_issues = []

        # 执行各项检查
        all_issues.extend(self.check_sensitive_info_leakage())
        all_issues.extend(self.check_gitignore_security())
        all_issues.extend(self.check_configuration_security())
        all_issues.extend(self.check_file_permissions())

        # 按严重程度分类
        high_issues = [issue for issue in all_issues if issue['severity'] == 'high']
        medium_issues = [issue for issue in all_issues if issue['severity'] == 'medium']
        low_issues = [issue for issue in all_issues if issue['severity'] == 'low']

        # 生成报告
        report = {
            'total_issues': len(all_issues),
            'high_issues': len(high_issues),
            'medium_issues': len(medium_issues),
            'low_issues': len(low_issues),
            'issues': {
                'high': high_issues,
                'medium': medium_issues,
                'low': low_issues
            },
            'secure_secrets': self.generate_secure_secrets()
        }

        return report

    def print_report(self, report: Dict):
        """打印安全检查报告"""
        print("\n" + "=" * 50)
        print("📊 AI财务系统安全检查报告")
        print("=" * 50)

        print(f"\n📈 总体统计:")
        print(f"  总问题数: {report['total_issues']}")
        print(f"  🔴 高危: {report['high_issues']}")
        print(f"  🟡 中危: {report['medium_issues']}")
        print(f"  🟢 低危: {report['low_issues']}")

        # 打印高危问题
        if report['issues']['high']:
            print(f"\n🔴 高危问题 ({len(report['issues']['high'])}个):")
            for i, issue in enumerate(report['issues']['high'], 1):
                print(f"  {i}. {issue['description']}")
                if 'file' in issue:
                    print(f"     文件: {issue['file']}")
                    if 'line' in issue:
                        print(f"     行号: {issue['line']}")

        # 打印中危问题
        if report['issues']['medium']:
            print(f"\n🟡 中危问题 ({len(report['issues']['medium'])}个):")
            for i, issue in enumerate(report['issues']['medium'], 1):
                print(f"  {i}. {issue['description']}")
                if 'file' in issue:
                    print(f"     文件: {issue['file']}")

        # 打印低危问题
        if report['issues']['low']:
            print(f"\n🟢 低危问题 ({len(report['issues']['low'])}个):")
            for i, issue in enumerate(report['issues']['low'], 1):
                print(f"  {i}. {issue['description']}")
                if 'file' in issue:
                    print(f"     文件: {issue['file']}")

        # 安全建议
        print(f"\n💡 安全建议:")
        if report['high_issues'] > 0:
            print("  🔴 立即修复所有高危问题")
        if report['medium_issues'] > 0:
            print("  🟡 尽快修复中危问题")
        if report['low_issues'] > 0:
            print("  🟢 建议修复低危问题")

        print("  📋 定期运行安全检查")
        print("  🔐 使用强密码和随机密钥")
        print("  🛡️ 启用HTTPS和数据库SSL连接")

        # 生成安全密钥建议
        print(f"\n🔐 建议的安全密钥:")
        secrets = report['secure_secrets']
        print(f"  JWT_SECRET: {secrets['jwt_secret']}")
        print(f"  ENCRYPTION_KEY: {secrets['encryption_key']}")
        print(f"  数据库密码: {secrets['database_password']}")
        print(f"  API密钥: {secrets['api_key']}")

        print("\n" + "=" * 50)


def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 创建安全检查器
    checker = SecurityChecker(project_root)

    # 运行安全检查
    report = checker.run_full_security_check()

    # 打印报告
    checker.print_report(report)

    # 根据检查结果设置退出码
    if report['high_issues'] > 0:
        print("\n❌ 发现高危安全问题，请立即修复！")
        sys.exit(1)
    elif report['medium_issues'] > 0:
        print("\n⚠️ 发现中危安全问题，建议尽快修复！")
        sys.exit(2)
    elif report['low_issues'] > 0:
        print("\n✅ 安全检查通过，发现少量低危问题")
        sys.exit(0)
    else:
        print("\n🎉 安全检查完全通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()