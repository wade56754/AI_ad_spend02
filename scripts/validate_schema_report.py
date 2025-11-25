#!/usr/bin/env python3
"""
数据库表结构验证报告生成器
对比 Supabase 数据库实际表结构与 DATA_SCHEMA.md v5.2 的定义

使用方法:
    1. 运行此脚本获取数据库结构
    2. 自动对比并生成报告
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

project_root = Path(__file__).parent.parent


@dataclass
class ColumnDef:
    """列定义"""
    name: str
    data_type: str
    format: str  # PostgreSQL 内部类型
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    character_max_length: Optional[int] = None
    numeric_precision: Optional[Tuple[int, int]] = None  # (precision, scale)


@dataclass
class TableDef:
    """表定义"""
    name: str
    columns: Dict[str, ColumnDef] = field(default_factory=dict)
    primary_key_type: str = ""  # UUID or BIGSERIAL


def parse_data_schema_md(schema_file: Path) -> Dict[str, TableDef]:
    """解析 DATA_SCHEMA.md 文件"""
    if not schema_file.exists():
        raise FileNotFoundError(f"找不到文件: {schema_file}")
    
    content = schema_file.read_text(encoding='utf-8')
    tables: Dict[str, TableDef] = {}
    
    # 提取表清单（第2章）- 获取主键类型
    table_list_pattern = r'\|\s*`(\w+)`\s*\|\s*[^|]+\s*\|\s*(UUID|BIGSERIAL)'
    for match in re.finditer(table_list_pattern, content):
        table_name = match.group(1)
        pk_type = match.group(2)
        tables[table_name] = TableDef(name=table_name, columns={}, primary_key_type=pk_type)
    
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
                tables[table_name] = TableDef(name=table_name, columns={}, primary_key_type='')
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
                    
                    tables[current_table].columns[field_name] = ColumnDef(
                        name=field_name,
                        data_type=data_type,
                        format=format_type,
                        is_nullable=is_nullable,
                        default_value=default_value,
                        is_primary_key=is_primary_key,
                        character_max_length=char_len,
                        numeric_precision=num_prec
                    )
        
        i += 1
    
    return tables


def parse_data_type(type_str: str) -> Tuple[str, str, Optional[int], Optional[Tuple[int, int]]]:
    """解析数据类型字符串，返回 (data_type, format, char_length, numeric_precision)"""
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


def convert_db_result_to_tables(db_result: List[dict]) -> Dict[str, Dict[str, ColumnDef]]:
    """将数据库查询结果转换为表结构字典"""
    tables: Dict[str, Dict[str, ColumnDef]] = {}
    
    for row in db_result:
        table_name = row['table_name']
        if table_name not in tables:
            tables[table_name] = {}
        
        col_name = row['column_name']
        data_type = row['data_type']
        format_type = row.get('format', data_type)
        is_nullable = row['is_nullable'] == 'YES'
        default_value = row.get('column_default')
        is_primary_key = row.get('is_primary_key', False)
        char_max_len = row.get('character_maximum_length')
        num_precision = row.get('numeric_precision')
        num_scale = row.get('numeric_scale')
        
        numeric_prec = None
        if num_precision and num_scale is not None:
            numeric_prec = (num_precision, num_scale)
        
        tables[table_name][col_name] = ColumnDef(
            name=col_name,
            data_type=data_type,
            format=format_type,
            is_nullable=is_nullable,
            default_value=default_value,
            is_primary_key=is_primary_key,
            character_max_length=char_max_len,
            numeric_precision=numeric_prec
        )
    
    return tables


def compare_schemas(db_tables: Dict[str, Dict[str, ColumnDef]], 
                   doc_tables: Dict[str, TableDef]) -> Tuple[List[str], List[str]]:
    """对比数据库和文档定义"""
    errors = []
    warnings = []
    
    # 检查表是否存在
    for table_name, table_def in doc_tables.items():
        if table_name not in db_tables:
            errors.append(f"❌ 表 {table_name} 在文档中定义但数据库中不存在")
            continue
        
        db_columns = db_tables[table_name]
        doc_columns = table_def.columns
        
        # 检查字段
        for col_name, doc_col in doc_columns.items():
            if col_name not in db_columns:
                errors.append(f"❌ 表 {table_name}.{col_name} 在文档中定义但数据库中不存在")
                continue
            
            db_col = db_columns[col_name]
            
            # 检查数据类型（使用 format 字段进行比较）
            if not types_match(db_col.format, doc_col.format, db_col, doc_col):
                errors.append(
                    f"❌ 表 {table_name}.{col_name} 类型不匹配: "
                    f"数据库={db_col.format} ({db_col.data_type}), "
                    f"文档={doc_col.format} ({doc_col.data_type})"
                )
            
            # 检查可空性（主键字段跳过）
            if not doc_col.is_primary_key and db_col.is_nullable != doc_col.is_nullable:
                warnings.append(
                    f"⚠️  表 {table_name}.{col_name} 可空性不一致: "
                    f"数据库={'可空' if db_col.is_nullable else '不可空'}, "
                    f"文档={'可空' if doc_col.is_nullable else '不可空'}"
                )
            
            # 检查字符长度
            if doc_col.character_max_length and db_col.character_max_length:
                if db_col.character_max_length != doc_col.character_max_length:
                    errors.append(
                        f"❌ 表 {table_name}.{col_name} 字符长度不匹配: "
                        f"数据库={db_col.character_max_length}, 文档={doc_col.character_max_length}"
                    )
            
            # 检查数值精度
            if doc_col.numeric_precision and db_col.numeric_precision:
                if db_col.numeric_precision != doc_col.numeric_precision:
                    errors.append(
                        f"❌ 表 {table_name}.{col_name} 数值精度不匹配: "
                        f"数据库={db_col.numeric_precision}, 文档={doc_col.numeric_precision}"
                    )
        
        # 检查数据库中有但文档中没有的字段
        for col_name in db_columns:
            if col_name not in doc_columns:
                errors.append(f"❌ 表 {table_name}.{col_name} 在数据库中存在但文档中未定义（自创字段）")
    
    # 检查数据库中有但文档中没有的表
    for table_name in db_tables:
        if table_name not in doc_tables:
            warnings.append(f"⚠️  表 {table_name} 在数据库中存在但文档中未定义")
    
    return errors, warnings


def types_match(db_format: str, doc_format: str, db_col: ColumnDef, doc_col: ColumnDef) -> bool:
    """检查类型是否匹配"""
    db_format_norm = db_format.lower().strip()
    doc_format_norm = doc_format.lower().strip()
    
    # 处理 bigint/int8 (BIGSERIAL 实际存储为 bigint/int8)
    if db_format_norm in ['bigint', 'int8'] and doc_format_norm in ['bigint', 'int8', 'bigserial']:
        return True
    
    # 处理 numeric 类型
    if 'numeric' in db_format_norm and 'numeric' in doc_format_norm:
        if db_col.numeric_precision and doc_col.numeric_precision:
            return db_col.numeric_precision == doc_col.numeric_precision
        return True  # 如果一方没有精度，认为匹配
    
    # 处理 character varying/varchar
    if db_format_norm in ['varchar', 'character varying'] and doc_format_norm in ['varchar', 'character varying']:
        if db_col.character_max_length and doc_col.character_max_length:
            return db_col.character_max_length == doc_col.character_max_length
        return True  # 如果一方没有长度，认为匹配
    
    # 其他类型直接比较
    return db_format_norm == doc_format_norm


def main():
    """主函数"""
    print("=" * 80)
    print("数据库表结构验证报告")
    print("对比 Supabase 数据库与 DATA_SCHEMA.md v5.2")
    print("=" * 80)
    print()
    
    # 读取配置
    schema_file = project_root / "docs/2.sot/DATA_SCHEMA.md"
    
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
    
    # 注意: 数据库结构数据需要通过 MCP 工具获取
    # 这里提供一个示例数据结构
    print("📋 文档中定义的表:")
    for table_name in sorted(doc_tables.keys()):
        col_count = len(doc_tables[table_name].columns)
        pk_type = doc_tables[table_name].primary_key_type or "未知"
        print(f"   - {table_name:30} ({col_count:2} 个字段, PK: {pk_type})")
    print()
    
    print("=" * 80)
    print("⚠️  注意: 数据库结构数据需要通过 MCP Supabase 工具获取")
    print("   请运行以下命令获取完整的验证报告:")
    print()
    print("   # 在 Cursor 中使用 MCP 工具查询表结构，然后运行此脚本进行对比")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()



