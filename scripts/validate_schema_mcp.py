#!/usr/bin/env python3
"""
数据库表结构验证脚本（使用 MCP Supabase）
对比 Supabase 数据库实际表结构与 DATA_SCHEMA.md v5.2 的定义

使用方法:
    python scripts/validate_schema_mcp.py
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ColumnDef:
    """列定义"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_unique: bool = False


@dataclass
class TableDef:
    """表定义"""
    name: str
    columns: Dict[str, ColumnDef] = field(default_factory=dict)
    primary_key_type: str = ""  # UUID or BIGSERIAL


class SchemaValidator:
    """Schema 验证器"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def parse_data_schema_md(self, schema_file: Path) -> Dict[str, TableDef]:
        """解析 DATA_SCHEMA.md 文件"""
        if not schema_file.exists():
            raise FileNotFoundError(f"找不到文件: {schema_file}")
        
        content = schema_file.read_text(encoding='utf-8')
        tables: Dict[str, TableDef] = {}
        
        # 提取表清单（第2章）
        table_list_pattern = r'\|\s*`(\w+)`\s*\|\s*[^|]+\s*\|\s*(UUID|BIGSERIAL)'
        for match in re.finditer(table_list_pattern, content):
            table_name = match.group(1)
            pk_type = match.group(2)
            tables[table_name] = TableDef(name=table_name, columns={}, primary_key_type=pk_type)
        
        # 解析详细表结构（第3章）
        # 匹配表定义部分，例如: #### 3.1.1 `users`（implemented）
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
            
            # 检测表结束（下一个表或章节）
            if in_table_section and (line.startswith('####') or line.startswith('###') or line.startswith('##')):
                in_table_section = False
                current_table = None
                i += 1
                continue
            
            # 解析字段定义（Markdown 表格格式）
            if in_table_section and current_table and '|' in line:
                # 跳过表头分隔行
                if re.match(r'^\|\s*---', line):
                    i += 1
                    continue
                
                # 解析表格行: | `field_name` | TYPE | 约束 | 说明 |
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    field_name = parts[0].strip('`').strip()
                    if field_name and field_name not in ['字段', '---']:
                        data_type_str = parts[1] if len(parts) > 1 else ''
                        constraints_str = parts[2] if len(parts) > 2 else ''
                        
                        # 解析数据类型
                        data_type = self._parse_data_type(data_type_str)
                        is_nullable = 'NOT NULL' not in constraints_str.upper() and 'PK' not in constraints_str.upper()
                        is_primary_key = 'PK' in constraints_str.upper()
                        is_unique = 'UNIQUE' in constraints_str.upper()
                        
                        # 提取默认值
                        default_match = re.search(r'DEFAULT\s+([^,\s]+)', constraints_str, re.IGNORECASE)
                        default_value = default_match.group(1) if default_match else None
                        
                        tables[current_table].columns[field_name] = ColumnDef(
                            name=field_name,
                            data_type=data_type,
                            is_nullable=is_nullable,
                            default_value=default_value,
                            is_primary_key=is_primary_key,
                            is_unique=is_unique
                        )
            
            i += 1
        
        return tables
    
    def _parse_data_type(self, type_str: str) -> str:
        """解析数据类型字符串"""
        type_str = type_str.upper().strip()
        
        # 标准化类型名称
        if 'BIGSERIAL' in type_str:
            return 'bigint'  # PostgreSQL 中 BIGSERIAL 实际存储为 bigint
        elif 'UUID' in type_str:
            return 'uuid'
        elif 'VARCHAR' in type_str:
            match = re.search(r'\((\d+)\)', type_str)
            if match:
                return f'character varying({match.group(1)})'
            return 'character varying'
        elif 'TEXT' in type_str:
            return 'text'
        elif 'DECIMAL' in type_str or 'NUMERIC' in type_str:
            match = re.search(r'\((\d+),(\d+)\)', type_str)
            if match:
                return f'numeric({match.group(1)},{match.group(2)})'
            return 'numeric'
        elif 'BOOLEAN' in type_str:
            return 'boolean'
        elif 'TIMESTAMPTZ' in type_str:
            return 'timestamp with time zone'
        elif 'DATE' in type_str:
            return 'date'
        elif 'INTEGER' in type_str or 'INT' in type_str:
            return 'integer'
        elif 'JSONB' in type_str:
            return 'jsonb'
        elif 'INET' in type_str:
            return 'inet'
        
        return type_str.lower()
    
    def convert_mcp_table_to_columns(self, mcp_table: dict) -> Dict[str, ColumnDef]:
        """将 MCP 返回的表结构转换为 ColumnDef 字典"""
        columns = {}
        
        for col in mcp_table.get('columns', []):
            col_name = col.get('name', '')
            data_type = col.get('data_type', '')
            format_type = col.get('format', '')
            options = col.get('options', [])
            default_value = col.get('default_value')
            
            # 判断是否可空
            is_nullable = 'nullable' in options
            
            # 判断是否主键
            is_primary_key = col_name in [pk for pk in mcp_table.get('primary_keys', [])]
            
            # 判断是否唯一（需要检查 unique 约束）
            is_unique = 'unique' in options or col_name in [pk for pk in mcp_table.get('primary_keys', [])]
            
            # 使用 format 字段作为标准化的数据类型
            db_type = format_type if format_type else data_type
            
            columns[col_name] = ColumnDef(
                name=col_name,
                data_type=db_type,
                is_nullable=is_nullable,
                default_value=default_value,
                is_primary_key=is_primary_key,
                is_unique=is_unique
            )
        
        return columns
    
    def compare_schemas(self, db_tables: Dict[str, Dict[str, ColumnDef]], 
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
                
                # 检查数据类型
                if not self._types_match(db_col.data_type, doc_col.data_type):
                    errors.append(
                        f"❌ 表 {table_name}.{col_name} 类型不匹配: "
                        f"数据库={db_col.data_type}, 文档={doc_col.data_type}"
                    )
                
                # 检查可空性（主键字段跳过，因为主键自动不可空）
                if not doc_col.is_primary_key and db_col.is_nullable != doc_col.is_nullable:
                    warnings.append(
                        f"⚠️  表 {table_name}.{col_name} 可空性不一致: "
                        f"数据库={'可空' if db_col.is_nullable else '不可空'}, "
                        f"文档={'可空' if doc_col.is_nullable else '不可空'}"
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
    
    def _types_match(self, db_type: str, doc_type: str) -> bool:
        """检查类型是否匹配"""
        # 标准化类型名称进行比较
        db_type_norm = db_type.lower().strip()
        doc_type_norm = doc_type.lower().strip()
        
        # 处理 numeric 类型（可能有精度）
        if 'numeric' in db_type_norm and 'numeric' in doc_type_norm:
            # 提取精度进行比较
            db_match = re.search(r'numeric(?:\((\d+),(\d+)\))?', db_type_norm)
            doc_match = re.search(r'numeric(?:\((\d+),(\d+)\))?', doc_type_norm)
            if db_match and doc_match:
                db_precision = (db_match.group(1), db_match.group(2)) if db_match.group(1) else None
                doc_precision = (doc_match.group(1), doc_match.group(2)) if doc_match.group(1) else None
                if db_precision and doc_precision:
                    return db_precision == doc_precision
                # 如果一方没有精度，认为匹配（因为文档可能不写精度）
                return True
        
        # 处理 character varying 类型
        if 'character varying' in db_type_norm or 'varchar' in db_type_norm:
            if 'character varying' in doc_type_norm or 'varchar' in doc_type_norm:
                # 比较长度（如果有）
                db_len_match = re.search(r'\((\d+)\)', db_type_norm)
                doc_len_match = re.search(r'\((\d+)\)', doc_type_norm)
                if db_len_match and doc_len_match:
                    return db_len_match.group(1) == doc_len_match.group(1)
                # 如果一方没有长度，认为匹配
                return True
        
        # 处理 bigint (BIGSERIAL 实际存储为 bigint)
        if db_type_norm == 'bigint' and ('bigserial' in doc_type_norm or 'bigint' in doc_type_norm):
            return True
        
        # 处理 int8 (PostgreSQL 内部类型)
        if db_type_norm == 'int8' and ('bigserial' in doc_type_norm or 'bigint' in doc_type_norm):
            return True
        
        # 其他类型直接比较
        return db_type_norm == doc_type_norm or db_type_norm in doc_type_norm or doc_type_norm in db_type_norm


def main():
    """主函数 - 需要通过 MCP 工具调用"""
    print("=" * 80)
    print("数据库表结构验证工具")
    print("对比 Supabase 数据库与 DATA_SCHEMA.md v5.2")
    print("=" * 80)
    print()
    
    # 读取配置
    schema_file = project_root / "docs/sot/DATA_SCHEMA.md"
    project_id = "jzmcoivxhiyidizncyaq"
    
    if not schema_file.exists():
        print(f"❌ 错误: 找不到 DATA_SCHEMA.md 文件: {schema_file}")
        sys.exit(1)
    
    print(f"📄 读取文档: {schema_file}")
    
    # 解析文档
    validator = SchemaValidator(project_id)
    try:
        doc_tables = validator.parse_data_schema_md(schema_file)
        print(f"✅ 成功解析文档，找到 {len(doc_tables)} 个表定义")
        print()
    except Exception as e:
        print(f"❌ 解析文档失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("📋 文档中定义的表:")
    for table_name in sorted(doc_tables.keys()):
        col_count = len(doc_tables[table_name].columns)
        pk_type = doc_tables[table_name].primary_key_type or "未知"
        print(f"   - {table_name:30} ({col_count:2} 个字段, PK: {pk_type})")
    print()
    
    print("=" * 80)
    print("⚠️  注意: 此脚本需要通过 MCP Supabase 工具获取数据库结构")
    print("   请在 Cursor 中使用 MCP 工具查询表结构，然后手动对比")
    print()
    print("   使用以下 SQL 查询表结构:")
    print()
    print("   SELECT column_name, data_type, format, is_nullable, column_default")
    print("   FROM information_schema.columns")
    print("   WHERE table_schema = 'public' AND table_name = 'daily_reports'")
    print("   ORDER BY ordinal_position;")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()



