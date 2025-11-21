#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模型验证脚本

验证内容：
1. ORM 与数据库 Schema 一致性检查
2. relationship/back_populates 成对性检查
3. 字段类型与 DATA_SCHEMA.md 一致性检查
4. 主键/外键类型一致性检查
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
from collections import defaultdict

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import inspect
from sqlalchemy.orm import RelationshipProperty
from backend.models import Base


class ModelValidator:
    """模型验证器"""
    
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.relationships: Dict[str, List[str]] = defaultdict(list)
        
    def validate_all(self) -> bool:
        """执行所有验证"""
        print("=" * 80)
        print("数据库模型验证报告")
        print("=" * 80)
        
        self._check_table_names()
        self._check_primary_keys()
        self._check_foreign_keys()
        self._check_relationships()
        self._check_field_types()
        
        return self._print_report()
    
    def _check_table_names(self):
        """检查表名是否与模型类名一致"""
        print("\n[1] 检查表名与模型类名一致性...")

        inspector = inspect(Base.metadata)
        tables = Base.metadata.tables.keys()

        for table_name in sorted(tables):
            # 查找对应的模型类
            model_class = None
            for mapper in Base.registry.mappers:
                if mapper.class_.__tablename__ == table_name:
                    model_class = mapper.class_
                    break

            if model_class:
                # 验证类名与表名的对应关系
                expected_plural = self._table_to_class_name(table_name)
                expected_singular = self._table_to_class_name_singular(table_name)
                actual_name = model_class.__name__

                # 允许两种情况：1) 完全匹配复数形式  2) 单数形式（常见的 ORM 约定）
                if actual_name == expected_plural or actual_name == expected_singular:
                    print(f"  [OK] {table_name} -> {actual_name}")
                else:
                    # 真正不匹配的情况（既不是复数也不是单数）
                    self.issues.append({
                        'type': 'table_name_mismatch',
                        'table': table_name,
                        'expected_class': f"{expected_singular}/{expected_plural}",
                        'actual_class': actual_name,
                        'severity': 'warning'
                    })
                    print(f"  [WARN] {table_name}: 模型类名 {actual_name} 与表名不一致（预期: {expected_singular} 或 {expected_plural}）")
            else:
                self.issues.append({
                    'type': 'no_model_class',
                    'table': table_name,
                    'severity': 'error'
                })
                print(f"  [ERROR] {table_name}: 找不到对应的模型类")
    
    def _check_primary_keys(self):
        """检查主键类型是否符合 DATA_SCHEMA"""
        print("\n[2] 检查主键类型...")
        
        # 根据 DATA_SCHEMA.md 定义的主键规则
        uuid_tables = {'users', 'channels', 'channel_contacts', 
                       'channel_reviews', 'channel_account_requests', 'channel_performance',
                       'ad_spend_daily'}
        bigserial_tables = {'projects', 'project_members', 'project_expenses',
                           'ad_accounts', 'account_status_history', 'account_alerts',
                           'daily_reports', 'topup_requests', 'topup_transactions',
                           'ledger_entries', 'reconciliation_batches', 'reconciliation_details',
                           'audit_logs', 'user_sessions'}
        
        for table_name, table in Base.metadata.tables.items():
            pk_col = None
            for col in table.columns:
                if col.primary_key:
                    pk_col = col
                    break
            
            if pk_col is not None:
                col_type = str(pk_col.type)
                is_uuid = 'UUID' in col_type or 'uuid' in col_type.lower()
                is_bigint = 'BIGINT' in col_type or 'BigInteger' in col_type
                
                if table_name in uuid_tables:
                    if not is_uuid:
                        self.issues.append({
                            'type': 'pk_type_mismatch',
                            'table': table_name,
                            'expected': 'UUID',
                            'actual': col_type,
                            'severity': 'error'
                        })
                        print(f"  [ERROR] {table_name}: 主键类型应为 UUID，实际为 {col_type}")
                    else:
                        print(f"  [OK] {table_name}: 主键类型为 UUID")
                
                elif table_name in bigserial_tables:
                    if not is_bigint:
                        self.issues.append({
                            'type': 'pk_type_mismatch',
                            'table': table_name,
                            'expected': 'BIGSERIAL/BIGINT',
                            'actual': col_type,
                            'severity': 'error'
                        })
                        print(f"  [ERROR] {table_name}: 主键类型应为 BIGSERIAL，实际为 {col_type}")
                    else:
                        print(f"  [OK] {table_name}: 主键类型为 BIGINT")
    
    def _check_foreign_keys(self):
        """检查外键类型是否与引用表的主键类型一致"""
        print("\n[3] 检查外键类型一致性...")
        
        for table_name, table in Base.metadata.tables.items():
            for fk in table.foreign_keys:
                ref_table = fk.column.table.name
                ref_col = fk.column.name
                
                # 获取外键列类型
                fk_col = None
                for col in table.columns:
                    if col.name == fk.parent.name:
                        fk_col = col
                        break
                
                if fk_col is not None:
                    fk_type = str(fk_col.type)
                    ref_type = str(fk.column.type)
                    
                    # 简化类型比较（忽略长度等细节）
                    fk_simple = self._simplify_type(fk_type)
                    ref_simple = self._simplify_type(ref_type)
                    
                    if fk_simple != ref_simple:
                        self.issues.append({
                            'type': 'fk_type_mismatch',
                            'table': table_name,
                            'fk_column': fk.parent.name,
                            'ref_table': ref_table,
                            'ref_column': ref_col,
                            'fk_type': fk_type,
                            'ref_type': ref_type,
                            'severity': 'error'
                        })
                        print(f"  [ERROR] {table_name}.{fk.parent.name} -> {ref_table}.{ref_col}: "
                              f"类型不匹配 ({fk_type} vs {ref_type})")
                    else:
                        print(f"  [OK] {table_name}.{fk.parent.name} -> {ref_table}.{ref_col}")
    
    def _check_relationships(self):
        """检查 relationship 的 back_populates 是否成对"""
        print("\n[4] 检查 relationship/back_populates 成对性...")
        
        relationships_map: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)
        
        for mapper in Base.registry.mappers:
            model_name = mapper.class_.__name__
            for prop in mapper.attrs:
                if isinstance(prop, RelationshipProperty):
                    rel_name = prop.key
                    back_populates = prop.back_populates
                    
                    if back_populates:
                        # 获取目标模型类
                        target_model = prop.entity.class_
                        target_name = target_model.__name__
                        
                        # 记录关系
                        key = (model_name, target_name)
                        relationships_map[key].append((rel_name, back_populates))
        
        # 检查成对性
        for (model_a, model_b), rels in relationships_map.items():
            # 查找反向关系
            reverse_key = (model_b, model_a)
            reverse_rels = relationships_map.get(reverse_key, [])
            
            for rel_a, back_a in rels:
                found = False
                for rel_b, back_b in reverse_rels:
                    if rel_b == back_a and back_b == rel_a:
                        found = True
                        break
                
                if not found and reverse_key in relationships_map:
                    self.issues.append({
                        'type': 'relationship_not_paired',
                        'model_a': model_a,
                        'rel_a': rel_a,
                        'back_populates': back_a,
                        'model_b': model_b,
                        'severity': 'warning'
                    })
                    print(f"  [WARN] {model_a}.{rel_a} -> back_populates='{back_a}' "
                          f"但 {model_b} 中可能缺少对应的 relationship")
                elif found:
                    print(f"  [OK] {model_a}.{rel_name} <-> {model_b}.{back_a}")
    
    def _check_field_types(self):
        """检查字段类型是否符合 DATA_SCHEMA（金额字段 DECIMAL(15,2) 等）"""
        print("\n[5] 检查字段类型...")

        # 检查金额字段和时间字段
        for table_name, table in Base.metadata.tables.items():
            for col in table.columns:
                col_type = str(col.type)
                col_name_lower = col.name.lower()

                # 优先检查日期/时间字段（避免 spend_date 被误判为金额字段）
                is_datetime_field = any(keyword in col_name_lower for keyword in ['_at', '_date', '_time']) and col.name != 'id'

                if is_datetime_field:
                    # 检查时间字段类型
                    if 'DATE' in col_type and 'TIME' not in col_type:
                        # 纯 DATE 类型，正常
                        print(f"  [OK] {table_name}.{col.name}: DATE")
                    elif 'TIMESTAMPTZ' in col_type or 'DateTime(timezone=True)' in col_type or 'TIMESTAMP WITH TIME ZONE' in col_type:
                        # 带时区的时间戳，正常
                        print(f"  [OK] {table_name}.{col.name}: TIMESTAMPTZ")
                    elif 'DateTime' in col_type or 'TIMESTAMP' in col_type:
                        # 不带时区的时间戳，给个提示但不算错误
                        self.issues.append({
                            'type': 'timestamp_timezone_missing',
                            'table': table_name,
                            'column': col.name,
                            'type': col_type,
                            'expected': 'TIMESTAMPTZ',
                            'severity': 'info'
                        })
                        print(f"  [INFO] {table_name}.{col.name}: 时间字段建议使用 TIMESTAMPTZ，当前为 {col_type}")
                    continue

                # 检查金额字段（排除已被识别为日期的字段）
                is_amount_field = any(keyword in col_name_lower for keyword in ['amount', 'budget', 'spend', 'cost', 'price', 'fee'])

                if is_amount_field:
                    # NUMERIC 和 DECIMAL 在 PostgreSQL 中是等价的
                    is_decimal_type = 'Numeric' in col_type or 'NUMERIC' in col_type or 'DECIMAL' in col_type or 'Decimal' in col_type

                    if is_decimal_type:
                        # 检查精度（15,2）
                        has_correct_precision = '(15,2)' in col_type or '(15, 2)' in col_type

                        if has_correct_precision:
                            print(f"  [OK] {table_name}.{col.name}: NUMERIC/DECIMAL(15,2)")
                        else:
                            # 精度不匹配，只给个提示
                            self.issues.append({
                                'type': 'amount_precision_mismatch',
                                'table': table_name,
                                'column': col.name,
                                'type': col_type,
                                'expected': 'DECIMAL(15,2)',
                                'severity': 'info'
                            })
                            print(f"  [INFO] {table_name}.{col.name}: 金额字段建议使用 DECIMAL(15,2)，当前为 {col_type}")
                    else:
                        # 金额字段不是 DECIMAL/NUMERIC 类型，这是真正的错误
                        self.issues.append({
                            'type': 'amount_type_mismatch',
                            'table': table_name,
                            'column': col.name,
                            'type': col_type,
                            'expected': 'DECIMAL',
                            'severity': 'error'
                        })
                        print(f"  [ERROR] {table_name}.{col.name}: 金额字段应为 DECIMAL/NUMERIC，实际为 {col_type}")
    
    def _print_report(self) -> bool:
        """打印验证报告"""
        print("\n" + "=" * 80)
        print("验证结果汇总")
        print("=" * 80)

        errors = [i for i in self.issues if i['severity'] == 'error']
        warnings = [i for i in self.issues if i['severity'] == 'warning']
        infos = [i for i in self.issues if i['severity'] == 'info']

        # 只统计真正需要处理的问题（error 和 warning）
        print(f"\n需要处理的问题数: {len(errors) + len(warnings)}")
        print(f"  [ERROR] 错误: {len(errors)}")
        print(f"  [WARN] 警告: {len(warnings)}")

        if infos:
            print(f"\n提示信息: {len(infos)} 条（不影响功能，仅供参考）")

        if errors:
            print("\n错误列表（需要修复）:")
            for issue in errors:
                table = issue.get('table', 'N/A')
                column = issue.get('column', '')
                location = f"{table}.{column}" if column else table
                print(f"  - {issue['type']}: {location}")

        if warnings:
            print("\n警告列表（建议优化）:")
            for issue in warnings:
                table = issue.get('table', 'N/A')
                column = issue.get('column', '')
                location = f"{table}.{column}" if column else table
                print(f"  - {issue['type']}: {location}")

        if infos:
            print("\n提示列表（可选优化）:")
            for issue in infos:
                table = issue.get('table', 'N/A')
                column = issue.get('column', '')
                location = f"{table}.{column}" if column else table
                print(f"  - {issue['type']}: {location}")

        print("\n" + "=" * 80)

        return len(errors) == 0
    
    def _table_to_class_name(self, table_name: str) -> str:
        """将表名转换为类名（PascalCase 复数形式）"""
        parts = table_name.split('_')
        return ''.join(word.capitalize() for word in parts)

    def _table_to_class_name_singular(self, table_name: str) -> str:
        """将表名转换为单数形式的类名（常见的 ORM 约定）"""
        parts = table_name.split('_')

        # 处理最后一个词的单数转换
        if parts:
            last_word = parts[-1]

            # 常见的复数 -> 单数规则（按优先级顺序检查）
            if last_word.endswith('ies'):
                # entries -> entry, categories -> category
                parts[-1] = last_word[:-3] + 'y'
            elif last_word.endswith('ches'):
                # batches -> batch
                parts[-1] = last_word[:-2]
            elif last_word.endswith('sses'):
                # statuses -> status, addresses -> address
                parts[-1] = last_word[:-2]
            elif last_word.endswith('xes'):
                # indexes -> index
                parts[-1] = last_word[:-2]
            elif last_word.endswith('s') and not last_word.endswith('ss'):
                # accounts -> account, logs -> log
                # 但 'ss' 结尾的不变（如 'address' 不应该变成 'addres'）
                parts[-1] = last_word[:-1]

        return ''.join(word.capitalize() for word in parts)

    def _simplify_type(self, type_str: str) -> str:
        """简化类型字符串以便比较"""
        type_str = type_str.upper()
        if 'UUID' in type_str:
            return 'UUID'
        elif 'BIGINT' in type_str:
            return 'BIGINT'
        elif 'INT' in type_str:
            return 'INT'
        elif 'DECIMAL' in type_str or 'NUMERIC' in type_str:
            return 'DECIMAL'
        elif 'VARCHAR' in type_str or 'STRING' in type_str:
            return 'STRING'
        return type_str


if __name__ == '__main__':
    validator = ModelValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)

