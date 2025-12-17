"""
数据导出工具函数
Version: 1.0
Author: Claude协作开发
"""

import io
import json
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union


def _convert_value(value: Any) -> Any:
    """转换值为可序列化格式"""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, 'model_dump'):  # Pydantic model
        return value.model_dump()
    if hasattr(value, '__dict__'):  # ORM model
        return {k: _convert_value(v) for k, v in value.__dict__.items() if not k.startswith('_')}
    return value


def export_to_excel(
    data: Union[List[Dict[str, Any]], List[Any]],
    sheet_name: str = "Sheet1",
    headers: Optional[List[str]] = None
) -> bytes:
    """
    导出数据到 Excel 格式

    Args:
        data: 数据列表（字典列表或对象列表）
        sheet_name: 工作表名称
        headers: 自定义表头（可选）

    Returns:
        Excel 文件的字节内容
    """
    try:
        import openpyxl
        from openpyxl import Workbook
    except ImportError:
        # 如果没有 openpyxl，返回 CSV 格式
        return export_to_csv(data, headers)

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # 转换数据
    converted_data = []
    for item in data:
        if hasattr(item, 'model_dump'):
            converted_data.append(item.model_dump())
        elif hasattr(item, '__dict__'):
            converted_data.append({k: _convert_value(v) for k, v in item.__dict__.items() if not k.startswith('_')})
        elif isinstance(item, dict):
            converted_data.append({k: _convert_value(v) for k, v in item.items()})
        else:
            converted_data.append({"value": _convert_value(item)})

    if not converted_data:
        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    # 写入表头
    if headers:
        ws.append(headers)
    else:
        ws.append(list(converted_data[0].keys()))

    # 写入数据
    for row in converted_data:
        if headers:
            ws.append([_convert_value(row.get(h, '')) for h in headers])
        else:
            ws.append([_convert_value(v) for v in row.values()])

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_to_csv(
    data: Union[List[Dict[str, Any]], List[Any]],
    headers: Optional[List[str]] = None
) -> bytes:
    """
    导出数据到 CSV 格式

    Args:
        data: 数据列表
        headers: 自定义表头

    Returns:
        CSV 文件的字节内容
    """
    import csv

    output = io.StringIO()

    # 转换数据
    converted_data = []
    for item in data:
        if hasattr(item, 'model_dump'):
            converted_data.append(item.model_dump())
        elif hasattr(item, '__dict__'):
            converted_data.append({k: _convert_value(v) for k, v in item.__dict__.items() if not k.startswith('_')})
        elif isinstance(item, dict):
            converted_data.append({k: _convert_value(v) for k, v in item.items()})
        else:
            converted_data.append({"value": _convert_value(item)})

    if not converted_data:
        return output.getvalue().encode('utf-8-sig')

    # 确定表头
    fieldnames = headers if headers else list(converted_data[0].keys())

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for row in converted_data:
        writer.writerow({k: _convert_value(row.get(k, '')) for k in fieldnames})

    return output.getvalue().encode('utf-8-sig')


def export_to_pdf(
    data: Union[List[Dict[str, Any]], List[Any]],
    title: str = "数据报表",
    headers: Optional[List[str]] = None
) -> bytes:
    """
    导出数据到 PDF 格式

    注意：需要安装 reportlab 库
    如果没有安装，返回 JSON 格式作为替代

    Args:
        data: 数据列表
        title: 报表标题
        headers: 自定义表头

    Returns:
        PDF 文件的字节内容
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        # 如果没有 reportlab，返回 JSON 格式
        return export_to_json(data)

    output = io.BytesIO()

    # 转换数据
    converted_data = []
    for item in data:
        if hasattr(item, 'model_dump'):
            converted_data.append(item.model_dump())
        elif hasattr(item, '__dict__'):
            converted_data.append({k: _convert_value(v) for k, v in item.__dict__.items() if not k.startswith('_')})
        elif isinstance(item, dict):
            converted_data.append({k: _convert_value(v) for k, v in item.items()})
        else:
            converted_data.append({"value": _convert_value(item)})

    doc = SimpleDocTemplate(output, pagesize=landscape(A4))
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))

    if converted_data:
        # 确定表头
        table_headers = headers if headers else list(converted_data[0].keys())

        # 构建表格数据
        table_data = [table_headers]
        for row in converted_data:
            table_data.append([str(_convert_value(row.get(h, ''))) for h in table_headers])

        # 创建表格
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

    doc.build(elements)
    return output.getvalue()


def export_to_json(
    data: Union[List[Dict[str, Any]], List[Any]],
    indent: int = 2
) -> bytes:
    """
    导出数据到 JSON 格式

    Args:
        data: 数据列表
        indent: 缩进空格数

    Returns:
        JSON 文件的字节内容
    """
    # 转换数据
    converted_data = []
    for item in data:
        if hasattr(item, 'model_dump'):
            converted_data.append(item.model_dump())
        elif hasattr(item, '__dict__'):
            converted_data.append({k: _convert_value(v) for k, v in item.__dict__.items() if not k.startswith('_')})
        elif isinstance(item, dict):
            converted_data.append({k: _convert_value(v) for k, v in item.items()})
        else:
            converted_data.append({"value": _convert_value(item)})

    return json.dumps(
        converted_data,
        ensure_ascii=False,
        indent=indent,
        default=str
    ).encode('utf-8')
