"""分析Excel文件结构"""
import pandas as pd
import os

files = [
    r'C:\Users\user\Downloads\公司业务账单.xlsx',
    r'C:\Users\user\Downloads\收支表.xlsx',
    r'C:\Users\user\Downloads\12月收支表汇总.xlsx',
    r'C:\Users\user\Downloads\ZZ-代理充值汇总表-2025年12月.xlsx'
]

for f in files:
    print(f'\n{"="*60}')
    print(f'文件: {os.path.basename(f)}')
    print(f'{"="*60}')

    try:
        # 获取所有sheet名
        xl = pd.ExcelFile(f)
        print(f'Sheet列表: {xl.sheet_names}')

        for sheet in xl.sheet_names[:3]:  # 只看前3个sheet
            print(f'\n--- Sheet: {sheet} ---')
            df = pd.read_excel(f, sheet_name=sheet, nrows=15)
            print(f'列名: {list(df.columns)}')
            print(f'数据类型:\n{df.dtypes}')
            print(f'\n前5行数据:')
            print(df.head(5).to_string())
            print(f'\n总行数(文件中): {len(pd.read_excel(f, sheet_name=sheet))}')
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
