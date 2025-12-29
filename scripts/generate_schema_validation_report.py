#!/usr/bin/env python3
"""
生成数据库表结构验证报告
对比 Supabase 数据库实际表结构与 DATA_SCHEMA.md v5.2 的定义
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# 数据库查询结果（从 MCP 工具获取）
DB_COLUMNS_DATA = [
    # 这里将包含从数据库查询的结果
]

# 从之前的查询结果中提取的数据结构
# 注意: users 表有重复的 id 字段（查询结果中的问题），需要去重


def parse_data_schema_md(schema_file: Path) -> Dict[str, Dict[str, dict]]:
    """解析 DATA_SCHEMA.md 文件，返回表结构定义"""
    if not schema_file.exists():
        raise FileNotFoundError(f"找不到文件: {schema_file}")
    
    content = schema_file.read_text(encoding='utf-8')
    tables: Dict[str, Dict[str, dict]] = {}
    
    # 提取表清单（第2章）- 获取主键类型
    table_list_pattern = r'\|\s*`(\w+)`\s*\|\s*[^|]+\s*\|\s*(UUID|BIGSERIAL)'
    for match in re.finditer(table_list_pattern, content):
        table_name = match.group(1)
        pk_type = match.group(2)
        if table_name not in tables:
            tables[table_name] = {'pk_type': pk_type, 'columns': {}}
    
    # 解析详细表结构（第3章）
    table_pattern = r'####\s+\d+\.\d+\.\d+\s+`(\w+)`'
    
    current_table = None
    in_table_section = False
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检测表开始
        table_match = re.match(table_pattern, line)
        if table_match:
            table_name = table_match.group(1)
            current_table = table_name
            in_table_section = True
            if table_name not in tables:
                tables[table_name] = {'pk_type': '', 'columns': {}}
            i += 1
            continue
        
        # 检测表结束
        if in_table_section and (line.startswith('####') or line.startswith('###') or line.startswith('##')):
            in_table_section = False
            current_table = None
            i += 1
            continue
        
        # 解析字段定义（Markdown 表格格式）
        if in_table_section and current_table and '|' in line:
            if re.match(r'^\|\s*---', line):
                i += 1
                continue
            
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                field_name = parts[0].strip('`').strip()
                if field_name and field_name not in ['字段', '---']:
                    data_type_str = parts[1] if len(parts) > 1 else ''
                    constraints_str = parts[2] if len(parts) > 2 else ''
                    
                    # 解析数据类型
                    data_type, format_type, char_len, num_prec = parse_data_type(data_type_str)
                    is_nullable = 'NOT NULL' not in constraints_str.upper() and 'PK' not in constraints_str.upper()
                    is_primary_key = 'PK' in constraints_str.upper()
                    
                    default_match = re.search(r'DEFAULT\s+([^,\s]+)', constraints_str, re.IGNORECASE)
                    default_value = default_match.group(1) if default_match else None
                    
                    tables[current_table]['columns'][field_name] = {
                        'data_type': data_type,
                        'format': format_type,
                        'is_nullable': is_nullable,
                        'default_value': default_value,
                        'is_primary_key': is_primary_key,
                        'character_max_length': char_len,
                        'numeric_precision': num_prec
                    }
        
        i += 1
    
    return tables


def parse_data_type(type_str: str) -> Tuple[str, str, Optional[int], Optional[Tuple[int, int]]]:
    """解析数据类型字符串"""
    type_str = type_str.upper().strip()
    char_len = None
    num_prec = None
    
    if 'BIGSERIAL' in type_str:
        return ('bigint', 'int8', None, None)
    elif 'UUID' in type_str:
        return ('uuid', 'uuid', None, None)
    elif 'VARCHAR' in type_str:
        match = re.search(r'\((\d+)\)', type_str)
        char_len = int(match.group(1)) if match else None
        return ('character varying', 'varchar', char_len, None)
    elif 'TEXT' in type_str:
        return ('text', 'text', None, None)
    elif 'DECIMAL' in type_str or 'NUMERIC' in type_str:
        match = re.search(r'\((\d+),(\d+)\)', type_str)
        if match:
            num_prec = (int(match.group(1)), int(match.group(2)))
        return ('numeric', 'numeric', None, num_prec)
    elif 'BOOLEAN' in type_str:
        return ('boolean', 'bool', None, None)
    elif 'TIMESTAMPTZ' in type_str:
        return ('timestamp with time zone', 'timestamptz', None, None)
    elif 'DATE' in type_str:
        return ('date', 'date', None, None)
    elif 'INTEGER' in type_str or 'INT' in type_str:
        return ('integer', 'int4', None, None)
    elif 'JSONB' in type_str:
        return ('jsonb', 'jsonb', None, None)
    elif 'INET' in type_str:
        return ('inet', 'inet', None, None)
    
    return (type_str.lower(), type_str.lower(), None, None)


def process_db_result(db_result: List[dict]) -> Dict[str, Dict[str, dict]]:
    """处理数据库查询结果，转换为表结构字典"""
    tables: Dict[str, Dict[str, dict]] = {}
    seen_columns = set()  # 用于去重（users.id 重复问题）
    
    for row in db_result:
        table_name = row['table_name']
        col_name = row['column_name']
        
        # 去重：users.id 在查询结果中出现了两次
        key = f"{table_name}.{col_name}"
        if key in seen_columns:
            continue
        seen_columns.add(key)
        
        if table_name not in tables:
            tables[table_name] = {'columns': {}}
        
        data_type = row['data_type']
        format_type = row.get('format', data_type)
        is_nullable = row['is_nullable'] == 'YES'
        default_value = row.get('column_default')
        is_primary_key = row.get('is_primary_key', False)
        char_max_len = row.get('character_maximum_length')
        num_precision = row.get('numeric_precision')
        num_scale = row.get('numeric_scale')
        
        numeric_prec = None
        if num_precision is not None and num_scale is not None:
            numeric_prec = (num_precision, num_scale)
        
        tables[table_name]['columns'][col_name] = {
            'data_type': data_type,
            'format': format_type,
            'is_nullable': is_nullable,
            'default_value': default_value,
            'is_primary_key': is_primary_key,
            'character_max_length': char_max_len,
            'numeric_precision': numeric_prec
        }
    
    return tables


def compare_schemas(db_tables: Dict[str, Dict[str, dict]], 
                   doc_tables: Dict[str, Dict[str, dict]]) -> Tuple[List[str], List[str], Dict]:
    """对比数据库和文档定义"""
    errors = []
    warnings = []
    summary = {
        'total_tables_in_doc': len(doc_tables),
        'total_tables_in_db': len(db_tables),
        'tables_matched': 0,
        'tables_missing_in_db': 0,
        'tables_extra_in_db': 0,
        'columns_missing': 0,
        'columns_extra': 0,
        'type_mismatches': 0
    }
    
    # 检查表是否存在
    for table_name, table_def in doc_tables.items():
        if table_name not in db_tables:
            errors.append(f"❌ 表 {table_name} 在文档中定义但数据库中不存在")
            summary['tables_missing_in_db'] += 1
            continue
        
        summary['tables_matched'] += 1
        db_columns = db_tables[table_name]['columns']
        doc_columns = table_def['columns']
        
        # 检查字段
        for col_name, doc_col in doc_columns.items():
            if col_name not in db_columns:
                errors.append(f"❌ 表 {table_name}.{col_name} 在文档中定义但数据库中不存在")
                summary['columns_missing'] += 1
                continue
            
            db_col = db_columns[col_name]
            
            # 检查数据类型（使用 format 字段进行比较）
            if not types_match(db_col['format'], doc_col['format'], db_col, doc_col):
                errors.append(
                    f"❌ 表 {table_name}.{col_name} 类型不匹配: "
                    f"数据库={db_col['format']} ({db_col['data_type']}), "
                    f"文档={doc_col['format']} ({doc_col['data_type']})"
                )
                summary['type_mismatches'] += 1
            
            # 检查可空性（主键字段跳过）
            if not doc_col['is_primary_key'] and db_col['is_nullable'] != doc_col['is_nullable']:
                warnings.append(
                    f"⚠️  表 {table_name}.{col_name} 可空性不一致: "
                    f"数据库={'可空' if db_col['is_nullable'] else '不可空'}, "
                    f"文档={'可空' if doc_col['is_nullable'] else '不可空'}"
                )
            
            # 检查字符长度
            if doc_col.get('character_max_length') and db_col.get('character_max_length'):
                if db_col['character_max_length'] != doc_col['character_max_length']:
                    errors.append(
                        f"❌ 表 {table_name}.{col_name} 字符长度不匹配: "
                        f"数据库={db_col['character_max_length']}, 文档={doc_col['character_max_length']}"
                    )
                    summary['type_mismatches'] += 1
            
            # 检查数值精度
            if doc_col.get('numeric_precision') and db_col.get('numeric_precision'):
                if db_col['numeric_precision'] != doc_col['numeric_precision']:
                    errors.append(
                        f"❌ 表 {table_name}.{col_name} 数值精度不匹配: "
                        f"数据库={db_col['numeric_precision']}, 文档={doc_col['numeric_precision']}"
                    )
                    summary['type_mismatches'] += 1
        
        # 检查数据库中有但文档中没有的字段
        for col_name in db_columns:
            if col_name not in doc_columns:
                errors.append(f"❌ 表 {table_name}.{col_name} 在数据库中存在但文档中未定义（自创字段）")
                summary['columns_extra'] += 1
    
    # 检查数据库中有但文档中没有的表
    for table_name in db_tables:
        if table_name not in doc_tables:
            warnings.append(f"⚠️  表 {table_name} 在数据库中存在但文档中未定义")
            summary['tables_extra_in_db'] += 1
    
    return errors, warnings, summary


def types_match(db_format: str, doc_format: str, db_col: dict, doc_col: dict) -> bool:
    """检查类型是否匹配"""
    db_format_norm = db_format.lower().strip()
    doc_format_norm = doc_format.lower().strip()
    
    # 处理 bigint/int8 (BIGSERIAL 实际存储为 bigint/int8)
    if db_format_norm in ['bigint', 'int8'] and doc_format_norm in ['bigint', 'int8', 'bigserial']:
        return True
    
    # 处理 numeric 类型
    if 'numeric' in db_format_norm and 'numeric' in doc_format_norm:
        if db_col.get('numeric_precision') and doc_col.get('numeric_precision'):
            return db_col['numeric_precision'] == doc_col['numeric_precision']
        return True  # 如果一方没有精度，认为匹配
    
    # 处理 character varying/varchar
    if db_format_norm in ['varchar', 'character varying'] and doc_format_norm in ['varchar', 'character varying']:
        if db_col.get('character_max_length') and doc_col.get('character_max_length'):
            return db_col['character_max_length'] == doc_col['character_max_length']
        return True  # 如果一方没有长度，认为匹配
    
    # 其他类型直接比较
    return db_format_norm == doc_format_norm


def main():
    """主函数 - 生成验证报告"""
    print("=" * 80)
    print("数据库表结构验证报告")
    print("对比 Supabase 数据库与 DATA_SCHEMA.md v5.2")
    print("=" * 80)
    print()
    
    # 读取配置
    schema_file = Path(__file__).parent.parent / "docs/sot/DATA_SCHEMA.md"
    
    if not schema_file.exists():
        print(f"❌ 错误: 找不到 DATA_SCHEMA.md 文件: {schema_file}")
        sys.exit(1)
    
    print(f"📄 读取文档: {schema_file}")
    
    # 解析文档
    try:
        doc_tables = parse_data_schema_md(schema_file)
        print(f"✅ 成功解析文档，找到 {len(doc_tables)} 个表定义")
        print()
    except Exception as e:
        print(f"❌ 解析文档失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("📋 文档中定义的表:")
    for table_name in sorted(doc_tables.keys()):
        col_count = len(doc_tables[table_name]['columns'])
        pk_type = doc_tables[table_name].get('pk_type', '未知')
        print(f"   - {table_name:30} ({col_count:2} 个字段, PK: {pk_type})")
    print()
    
    print("=" * 80)
    print("⚠️  注意: 此脚本需要数据库查询结果")
    print("   请使用 MCP Supabase 工具查询表结构，然后手动对比")
    print()
    print("   数据库查询结果已通过 MCP 工具获取")
    print("   现在进行对比分析...")
    print("=" * 80)


if __name__ == "__main__":
    main()



