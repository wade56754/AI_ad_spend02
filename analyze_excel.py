import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read the main sheet
df = pd.read_excel(r'C:\Users\user\Downloads\投手日报（回复）.xlsx', sheet_name='第 1 张表单回复')

print('=== 数据概览 ===')
print(f'总记录数: {len(df)}')
print(f'日期范围: {df["日期"].min()} ~ {df["日期"].max()}')

print('\n=== 投手列表 ===')
investors = df['投手'].unique().tolist()
print(f'共 {len(investors)} 人: {investors}')

print('\n=== 地区列表 ===')
regions = df['地区'].unique().tolist()
print(f'共 {len(regions)} 个: {regions}')

print('\n=== 平台列表 ===')
platforms = df['平台'].dropna().unique().tolist()
print(f'共 {len(platforms)} 个: {platforms}')

print('\n=== 团队列表 ===')
teams = df['所属团队（team）'].unique().tolist()
print(f'共 {len(teams)} 个: {teams}')

print('\n=== 数据统计 ===')
total_spend = df['广告消耗（AD Spend） 美元(USD) '].sum()
total_result = df['成效（result）'].sum()
total_people = df['进粉数（people）'].sum()
print(f'总广告消耗: ${total_spend:,.2f}')
print(f'总成效: {total_result:,.0f}')
print(f'总进粉数: {total_people:,.0f}')

print('\n=== 字段数据类型与空值统计 ===')
for col in df.columns:
    non_null = df[col].notna().sum()
    null_count = df[col].isna().sum()
    print(f'{col}: {df[col].dtype} (非空: {non_null}, 空值: {null_count})')

print('\n=== 投手信息表 ===')
df_info = pd.read_excel(r'C:\Users\user\Downloads\投手日报（回复）.xlsx', sheet_name='投手信息')
print(df_info.to_string())
