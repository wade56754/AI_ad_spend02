"""分析Excel文件结构 - 保存到文件"""
import pandas as pd
import os
import sys

# 强制UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

files = [
    r'C:\Users\user\Downloads\公司业务账单.xlsx',
    r'C:\Users\user\Downloads\收支表.xlsx',
    r'C:\Users\user\Downloads\12月收支表汇总.xlsx',
    r'C:\Users\user\Downloads\ZZ-代理充值汇总表-2025年12月.xlsx'
]

output = []

for f in files:
    output.append(f'\n{"="*60}')
    output.append(f'文件: {os.path.basename(f)}')
    output.append(f'{"="*60}')

    try:
        xl = pd.ExcelFile(f)
        output.append(f'Sheet列表: {xl.sheet_names}')

        for sheet in xl.sheet_names[:2]:  # 只看前2个sheet
            output.append(f'\n--- Sheet: {sheet} ---')
            df = pd.read_excel(f, sheet_name=sheet)
            output.append(f'列名: {list(df.columns)}')
            output.append(f'总行数: {len(df)}')

            # 找到真正的表头行
            for i, row in df.head(10).iterrows():
                non_null = row.dropna()
                if len(non_null) >= 3:
                    output.append(f'第{i}行数据: {dict(non_null)}')

    except Exception as e:
        output.append(f'错误: {e}')

# 保存到文件
with open('excel_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("分析完成，结果保存在 excel_analysis.txt")
