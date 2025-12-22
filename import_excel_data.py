"""
Excel数据导入脚本
将4个Excel文件中的数据整理并导入数据库

文件来源：
1. 公司业务账单.xlsx - 每月收支财务报表
2. 收支表.xlsx - 项目明细、成本、利润
3. 12月收支表汇总.xlsx - 应收未收、渠道收支
4. ZZ-代理充值汇总表-2025年12月.xlsx - 代理充值明细
"""

import pandas as pd
import os
import sys
import json
from decimal import Decimal
from datetime import datetime, date
from uuid import uuid4
import re

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Excel文件路径
FILES = {
    'company_bills': r'C:\Users\user\Downloads\公司业务账单.xlsx',
    'income_expense': r'C:\Users\user\Downloads\收支表.xlsx',
    'summary': r'C:\Users\user\Downloads\12月收支表汇总.xlsx',
    'topup': r'C:\Users\user\Downloads\ZZ-代理充值汇总表-2025年12月.xlsx'
}


class ExcelDataProcessor:
    """Excel数据处理器"""

    def __init__(self):
        self.teams_data = []
        self.buyers_data = []
        self.suppliers_data = []
        self.accounts_data = []
        self.topups_data = []
        self.daily_reports_data = []
        self.financial_events_data = []

    def process_all_files(self):
        """处理所有Excel文件"""
        print("开始处理Excel文件...\n")

        # 1. 处理收支表 - 获取团队和项目数据
        self.process_income_expense()

        # 2. 处理代理充值汇总表 - 获取渠道商和充值记录
        self.process_topup_summary()

        # 3. 处理公司业务账单 - 获取财务明细
        self.process_company_bills()

        # 4. 处理收支汇总表 - 获取渠道收支数据
        self.process_monthly_summary()

        return self.get_summary()

    def process_income_expense(self):
        """处理收支表.xlsx - 提取项目明细、成本、团队数据"""
        print("=" * 60)
        print("处理收支表.xlsx...")
        print("=" * 60)

        try:
            # 读取明细表
            df_detail = pd.read_excel(FILES['income_expense'], sheet_name='明细表')
            print(f"明细表行数: {len(df_detail)}")

            # 提取团队信息
            teams = df_detail['团队'].dropna().unique()
            for team_code in teams:
                if team_code and str(team_code).strip():
                    team_code = str(team_code).strip()
                    self.teams_data.append({
                        'code': team_code,
                        'name': f'{team_code}团队',
                        'status': 'active'
                    })
            print(f"发现团队: {[t['code'] for t in self.teams_data]}")

            # 提取项目/代投人信息作为参考
            projects = df_detail['项目/代投人名称'].dropna().unique()
            print(f"发现项目/代投人数量: {len(projects)}")

            # 提取地区信息
            regions = df_detail['地区'].dropna().unique()
            print(f"发现地区: {list(regions)}")

            # 处理明细数据 - 转换为日报格式
            for _, row in df_detail.iterrows():
                if pd.isna(row.get('月份')) or pd.isna(row.get('团队')):
                    continue

                # 解析月份 (如 "11月" -> 2025-11)
                month_str = str(row['月份']).replace('月', '')
                try:
                    month = int(month_str)
                    year = 2025
                    report_date = date(year, month, 15)  # 默认月中
                except:
                    continue

                report_data = {
                    'report_date': report_date,
                    'team_code': str(row['团队']).strip(),
                    'business_type': str(row.get('业务类型', '')),
                    'region': str(row.get('地区', '')),
                    'project_name': str(row.get('项目/代投人名称', '')),
                    'follows_count': int(row.get('有效数(粉/人)', 0) or 0),
                    'raw_spend': Decimal(str(row.get('总支出/消耗', 0) or 0)),
                    'revenue': Decimal(str(row.get('实际收款', 0) or 0)),
                    'profit': Decimal(str(row.get('项目毛利', 0) or 0)),
                    'prepaid_balance': str(row.get('剩余预付款', '')),
                    'notes': str(row.get('备注', ''))
                }
                self.daily_reports_data.append(report_data)

            print(f"提取日报数据: {len(self.daily_reports_data)} 条")

            # 读取成本表
            df_cost = pd.read_excel(FILES['income_expense'], sheet_name='成本表')
            print(f"\n成本表行数: {len(df_cost)}")

            for _, row in df_cost.iterrows():
                if pd.isna(row.get('月份')):
                    continue

                month_str = str(row['月份']).replace('月', '')
                try:
                    month = int(month_str)
                    year = 2025
                    event_date = date(year, month, 28)
                except:
                    continue

                # 工资成本
                salary = Decimal(str(row.get('员工工资成本', 0) or 0))
                if salary > 0:
                    self.financial_events_data.append({
                        'event_date': event_date,
                        'event_type': 'salary_cost',
                        'team_code': str(row['团队']).strip(),
                        'amount': salary,
                        'description': f"{row['月份']} {row['团队']}团队工资成本",
                        'notes': str(row.get('成本备注', ''))
                    })

                # 运营杂费
                misc = Decimal(str(row.get('运营杂费', 0) or 0))
                if misc > 0:
                    self.financial_events_data.append({
                        'event_date': event_date,
                        'event_type': 'operation_cost',
                        'team_code': str(row['团队']).strip(),
                        'amount': misc,
                        'description': f"{row['月份']} {row['团队']}团队运营杂费",
                        'notes': str(row.get('成本备注', ''))
                    })

            print(f"提取财务事件: {len(self.financial_events_data)} 条")

        except Exception as e:
            print(f"处理收支表失败: {e}")
            import traceback
            traceback.print_exc()

    def process_topup_summary(self):
        """处理ZZ-代理充值汇总表 - 提取渠道商和充值记录"""
        print("\n" + "=" * 60)
        print("处理代理充值汇总表...")
        print("=" * 60)

        try:
            xl = pd.ExcelFile(FILES['topup'])
            sheet_names = xl.sheet_names
            print(f"Sheet数量: {len(sheet_names)}")
            print(f"Sheet列表: {sheet_names[:10]}...")  # 只显示前10个

            # 排除模板和汇总sheet
            skip_sheets = ['模板', '12月充值汇总']

            for sheet_name in sheet_names:
                if sheet_name in skip_sheets:
                    continue

                # 提取渠道商名称
                supplier_name = sheet_name.strip()

                # 检查是否已存在
                if not any(s['name'] == supplier_name for s in self.suppliers_data):
                    # 根据名称判断平台
                    platform = 'FB'  # 默认
                    if '谷歌' in supplier_name or 'Google' in supplier_name.lower():
                        platform = 'Google'
                    elif 'TK' in supplier_name.upper() or 'TikTok' in supplier_name:
                        platform = 'TikTok'

                    self.suppliers_data.append({
                        'name': supplier_name,
                        'platform': platform,
                        'status': 'active',
                        'notes': f'从充值汇总表导入 ({sheet_name})'
                    })

                # 读取充值记录
                try:
                    df = pd.read_excel(FILES['topup'], sheet_name=sheet_name)

                    for _, row in df.iterrows():
                        # 跳过无效行
                        if pd.isna(row.get('日期')) or pd.isna(row.get('充值金额')):
                            continue

                        # 跳过开户费等非充值项
                        if str(row.get('充值金额', '')).strip() == '开户费':
                            continue

                        try:
                            amount = Decimal(str(row.get('充值金额', 0)))
                        except:
                            continue

                        if amount <= 0:
                            continue

                        topup_date = row.get('日期')
                        if isinstance(topup_date, pd.Timestamp):
                            topup_date = topup_date.to_pydatetime().date()
                        elif isinstance(topup_date, datetime):
                            topup_date = topup_date.date()
                        else:
                            continue

                        topup_record = {
                            'supplier_name': supplier_name,
                            'topup_date': topup_date,
                            'buyer_code': str(row.get('投手', '')).strip(),
                            'account_name': str(row.get('账户', '')).strip(),
                            'amount': amount,
                            'clear_amount': Decimal(str(row.get('户商清零金额', 0) or 0)),
                            'submit_clear': Decimal(str(row.get('提交清零金额', 0) or 0)),
                            'transfer_amount': Decimal(str(row.get('转移金额', 0) or 0)),
                            'settlement_status': str(row.get('结算', '')).strip(),
                            'notes': str(row.get('备注', '')).strip(),
                            'fee': Decimal(str(row.get('开户充值手续费', 0) or 0))
                        }
                        self.topups_data.append(topup_record)

                        # 提取投手信息
                        buyer_code = topup_record['buyer_code']
                        if buyer_code and not any(b['code'] == buyer_code for b in self.buyers_data):
                            self.buyers_data.append({
                                'code': buyer_code,
                                'name': buyer_code,
                                'team_code': 'ZZ',  # 从ZZ表导入
                                'status': 'active'
                            })

                        # 提取账户信息
                        account_name = topup_record['account_name']
                        if account_name and not any(a['name'] == account_name for a in self.accounts_data):
                            self.accounts_data.append({
                                'name': account_name,
                                'supplier_name': supplier_name,
                                'status': 'active'
                            })

                except Exception as e:
                    print(f"  处理sheet {sheet_name} 失败: {e}")
                    continue

            print(f"提取渠道商: {len(self.suppliers_data)} 个")
            print(f"提取投手: {len(self.buyers_data)} 个")
            print(f"提取账户: {len(self.accounts_data)} 个")
            print(f"提取充值记录: {len(self.topups_data)} 条")

        except Exception as e:
            print(f"处理代理充值汇总表失败: {e}")
            import traceback
            traceback.print_exc()

    def process_company_bills(self):
        """处理公司业务账单.xlsx - 提取财务收支明细"""
        print("\n" + "=" * 60)
        print("处理公司业务账单...")
        print("=" * 60)

        try:
            xl = pd.ExcelFile(FILES['company_bills'])
            # 选择2025年的sheet
            sheets_2025 = [s for s in xl.sheet_names if '2025年' in s and '收支财务报表' in s]
            print(f"2025年财务报表数量: {len(sheets_2025)}")

            income_count = 0
            expense_count = 0

            for sheet_name in sheets_2025[:3]:  # 只处理最近3个月
                try:
                    df = pd.read_excel(FILES['company_bills'], sheet_name=sheet_name, header=None)

                    # 解析月份
                    month_match = re.search(r'(\d+)月', sheet_name)
                    if not month_match:
                        continue
                    month = int(month_match.group(1))

                    # 找到数据行（从第5行开始通常是数据）
                    for idx in range(5, min(len(df), 200)):
                        row = df.iloc[idx]

                        # 检查是否有日期和金额
                        date_val = row.iloc[7] if len(row) > 7 else None

                        # 收入项目
                        if pd.notna(row.iloc[8]) and pd.notna(row.iloc[9]):
                            income_item = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ''
                            income_amount = row.iloc[9] if pd.notna(row.iloc[9]) else 0

                            if income_item and income_item not in ['项目', '收入', 'nan', ''] and income_amount:
                                try:
                                    amount = Decimal(str(income_amount))
                                    if amount > 0:
                                        event_date = date_val if isinstance(date_val, (datetime, date)) else date(2025, month, 1)
                                        if isinstance(event_date, datetime):
                                            event_date = event_date.date()

                                        self.financial_events_data.append({
                                            'event_date': event_date,
                                            'event_type': 'income',
                                            'amount': amount,
                                            'description': income_item,
                                            'notes': str(row.iloc[10]) if pd.notna(row.iloc[10]) else ''
                                        })
                                        income_count += 1
                                except:
                                    pass

                        # 支出项目
                        if pd.notna(row.iloc[12]) and pd.notna(row.iloc[13]):
                            expense_item = str(row.iloc[12]).strip() if pd.notna(row.iloc[12]) else ''
                            expense_amount = row.iloc[13] if pd.notna(row.iloc[13]) else 0

                            if expense_item and expense_item not in ['项目', '支出', 'nan', ''] and expense_amount:
                                try:
                                    amount = Decimal(str(expense_amount))
                                    if amount > 0:
                                        event_date = date_val if isinstance(date_val, (datetime, date)) else date(2025, month, 1)
                                        if isinstance(event_date, datetime):
                                            event_date = event_date.date()

                                        self.financial_events_data.append({
                                            'event_date': event_date,
                                            'event_type': 'expense',
                                            'amount': amount,
                                            'description': expense_item,
                                            'notes': str(row.iloc[14]) if pd.notna(row.iloc[14]) else ''
                                        })
                                        expense_count += 1
                                except:
                                    pass

                except Exception as e:
                    print(f"  处理sheet {sheet_name} 失败: {e}")
                    continue

            print(f"提取收入事件: {income_count} 条")
            print(f"提取支出事件: {expense_count} 条")

        except Exception as e:
            print(f"处理公司业务账单失败: {e}")
            import traceback
            traceback.print_exc()

    def process_monthly_summary(self):
        """处理12月收支表汇总.xlsx - 提取渠道收支数据"""
        print("\n" + "=" * 60)
        print("处理月度收支汇总...")
        print("=" * 60)

        try:
            # 读取渠道总支出收入sheet
            df = pd.read_excel(
                FILES['summary'],
                sheet_name='2025年12月渠道总支出收入',
                header=None
            )

            # 找到表头行
            header_row = None
            for idx in range(10):
                row = df.iloc[idx]
                if any('渠道商' in str(cell) for cell in row.values if pd.notna(cell)):
                    header_row = idx
                    break

            if header_row is None:
                print("未找到表头行")
                return

            print(f"表头行: {header_row}")

            # 从表头下一行开始读取数据
            channel_count = 0
            for idx in range(header_row + 1, min(len(df), header_row + 50)):
                row = df.iloc[idx]

                # 渠道商名称通常在第一列
                channel_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''

                if not channel_name or channel_name == 'nan':
                    continue

                # 提取渠道商数据
                total_topup = Decimal(str(row.iloc[1])) if pd.notna(row.iloc[1]) else Decimal('0')
                refund = Decimal(str(row.iloc[2])) if pd.notna(row.iloc[2]) else Decimal('0')

                if total_topup > 0 or refund > 0:
                    # 添加或更新渠道商
                    existing = next((s for s in self.suppliers_data if s['name'] == channel_name), None)
                    if existing:
                        existing['total_topup'] = str(total_topup)
                        existing['total_refund'] = str(refund)
                    else:
                        self.suppliers_data.append({
                            'name': channel_name,
                            'platform': 'FB',
                            'status': 'active',
                            'total_topup': str(total_topup),
                            'total_refund': str(refund),
                            'notes': '从渠道收支汇总导入'
                        })
                    channel_count += 1

            print(f"处理渠道收支: {channel_count} 条")

        except Exception as e:
            print(f"处理月度收支汇总失败: {e}")
            import traceback
            traceback.print_exc()

    def get_summary(self):
        """获取处理结果摘要"""
        summary = {
            'teams': self.teams_data,
            'buyers': self.buyers_data,
            'suppliers': self.suppliers_data,
            'accounts': self.accounts_data[:50],  # 限制数量
            'topups': self.topups_data[:100],  # 限制数量
            'daily_reports': self.daily_reports_data[:50],  # 限制数量
            'financial_events': self.financial_events_data[:100],  # 限制数量
            'stats': {
                'teams_count': len(self.teams_data),
                'buyers_count': len(self.buyers_data),
                'suppliers_count': len(self.suppliers_data),
                'accounts_count': len(self.accounts_data),
                'topups_count': len(self.topups_data),
                'daily_reports_count': len(self.daily_reports_data),
                'financial_events_count': len(self.financial_events_data)
            }
        }
        return summary

    def export_to_json(self, output_path='processed_data.json'):
        """导出处理后的数据到JSON文件"""
        summary = self.get_summary()

        # 转换日期和Decimal为字符串
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=serialize)

        print(f"\n数据已导出到: {output_path}")
        return output_path


def main():
    """主函数"""
    print("=" * 60)
    print("Excel数据处理与导入工具")
    print("=" * 60)

    # 检查文件是否存在
    for name, path in FILES.items():
        if os.path.exists(path):
            print(f"[OK] {name}: {path}")
        else:
            print(f"[X] {name}: {path} (文件不存在)")

    print()

    # 处理数据
    processor = ExcelDataProcessor()
    summary = processor.process_all_files()

    # 打印统计信息
    print("\n" + "=" * 60)
    print("处理结果统计")
    print("=" * 60)
    print(f"团队数量: {summary['stats']['teams_count']}")
    print(f"投手数量: {summary['stats']['buyers_count']}")
    print(f"渠道商数量: {summary['stats']['suppliers_count']}")
    print(f"账户数量: {summary['stats']['accounts_count']}")
    print(f"充值记录: {summary['stats']['topups_count']}")
    print(f"日报数据: {summary['stats']['daily_reports_count']}")
    print(f"财务事件: {summary['stats']['financial_events_count']}")

    # 导出JSON
    processor.export_to_json('D:/project/AI_ad_spend02/processed_data.json')

    # 显示部分数据预览
    print("\n" + "=" * 60)
    print("数据预览")
    print("=" * 60)

    print("\n--- 团队 ---")
    for team in summary['teams'][:5]:
        print(f"  {team}")

    print("\n--- 渠道商 (前10个) ---")
    for supplier in summary['suppliers'][:10]:
        print(f"  {supplier['name']} ({supplier.get('platform', 'N/A')})")

    print("\n--- 投手 (前10个) ---")
    for buyer in summary['buyers'][:10]:
        print(f"  {buyer['code']} - {buyer.get('team_code', 'N/A')}")


if __name__ == '__main__':
    main()
