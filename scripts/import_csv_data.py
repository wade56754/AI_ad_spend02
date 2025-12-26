"""
CSV 数据批量导入脚本

将 dataset/out/csv 目录下的数据导入到 Supabase 数据库

数据类型:
1. 日报数据 (tou_shou_ri_bao_hui_fu_*) → daily_reports 表
2. 消耗汇总 (xiao_hao_hui_zong_*) → ad_spends 或 daily_reports 表
3. 充值汇总 (zz_dai_li_chong_zhi_*) → topup_requests 表

使用方法:
    python scripts/import_csv_data.py --type daily_reports
    python scripts/import_csv_data.py --type all
    python scripts/import_csv_data.py --dry-run

Author: AI Code Factory
Date: 2025-12-22
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, List, Any, Tuple
from uuid import UUID, uuid4
import re
import io

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.core.config import get_settings
from backend.models import User, Project
from backend.models.accounts.ad_account import AdAccount
from backend.models.workflow.daily_report import DailyReport
from backend.models.core.channel import Channel


# ==================== 配置 ====================

CSV_DIR = project_root / "dataset" / "out" / "csv"

# 地区映射 (中文 → 英文)
REGION_MAP = {
    "印度": "India",
    "印度（India）": "India",
    "土耳其": "Turkey",
    "土耳其(Turkey)": "Turkey",
    "巴西": "Brazil",
    "意大利": "Italy",
    "德国": "Germany",
    "英国": "UK",
    "韩国": "Korea",
    "法国": "France",
    "马来西亚": "Malaysia",
    "日本": "Japan",
    "奥地利": "Austria",
    "西班牙": "Spain",
    "尼日利亚": "Nigeria",
    "新加坡": "Singapore",
    "比利时": "Belgium",
    "瑞典": "Sweden",
    "加拿大": "Canada",
    "印尼": "Indonesia",
    "印度尼西亚": "Indonesia",
    "美国": "USA",
    "爱尔兰": "Ireland",
}

# 平台映射
PLATFORM_MAP = {
    "FB": "FB",
    "Facebook": "FB",
    "Google": "Google",
    "TikTok": "TikTok",
    "Tiktok": "TikTok",
    "": "Other",
}


class DataImporter:
    """CSV 数据导入器"""

    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.settings = get_settings()
        self.engine = create_engine(self.settings.database_url)
        self.Session = sessionmaker(bind=self.engine)

        # 缓存
        self._users_cache: Dict[str, UUID] = {}
        self._accounts_cache: Dict[str, int] = {}
        self._channels_cache: Dict[str, int] = {}

        # 统计
        self.stats = {
            "daily_reports": {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0},
            "ad_accounts": {"created": 0, "found": 0},
            "users": {"created": 0, "found": 0},
        }

    def log(self, msg: str, level: str = "INFO"):
        """打印日志"""
        if self.verbose:
            prefix = {"INFO": "[INFO]", "OK": "[OK]", "WARN": "[WARN]", "ERR": "[ERR]", "SKIP": "[SKIP]"}
            print(f"{prefix.get(level, '')} {msg}")

    # ==================== 辅助方法 ====================

    def normalize_region(self, region: str) -> str:
        """标准化地区名称"""
        if not region:
            return "Other"
        region = region.strip()
        return REGION_MAP.get(region, region)

    def normalize_platform(self, platform: str) -> str:
        """标准化平台名称"""
        if not platform:
            return "Other"
        platform = platform.strip()
        return PLATFORM_MAP.get(platform, platform)

    def parse_decimal(self, value: str) -> Decimal:
        """解析数值为 Decimal"""
        if not value or value.strip() == "":
            return Decimal("0.00")
        try:
            # 移除逗号和空格
            cleaned = value.replace(",", "").replace(" ", "").strip()
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    def parse_int(self, value: str) -> int:
        """解析数值为整数"""
        if not value or value.strip() == "":
            return 0
        try:
            # 处理浮点数格式 (如 "9.0")
            cleaned = value.replace(",", "").replace(" ", "").strip()
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0

    def parse_date(self, value: str) -> Optional[date]:
        """解析日期"""
        if not value or value.strip() == "":
            return None

        # 尝试多种格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        value = value.strip()
        for fmt in formats:
            try:
                return datetime.strptime(value.split(" ")[0], fmt.split(" ")[0]).date()
            except ValueError:
                continue

        self.log(f"无法解析日期: {value}", "WARN")
        return None

    def extract_account_id(self, account_str: str) -> Optional[str]:
        """从账户字符串提取 ID (如 'BA VORNIX 9  1412307579460468' → '1412307579460468')"""
        if not account_str:
            return None
        # 查找数字串 (通常是 Facebook 账户 ID)
        match = re.search(r'\d{10,}', account_str)
        if match:
            return match.group()
        return account_str.strip()

    # ==================== 数据库操作 ====================

    def get_or_create_user(self, session, username: str) -> Optional[UUID]:
        """获取或创建用户 (投手)"""
        if not username:
            return None

        username = username.strip()
        if username in self._users_cache:
            return self._users_cache[username]

        # 查找现有用户
        user = session.query(User).filter(
            User.username == username
        ).first()

        if user:
            self._users_cache[username] = user.id
            self.stats["users"]["found"] += 1
            return user.id

        # 如果不是 dry_run，创建新用户
        if not self.dry_run:
            # 创建基础用户 (需要最小信息)
            new_user_id = uuid4()  # 手动生成 UUID
            user = User(
                id=new_user_id,
                username=username,
                email=f"{username.lower().replace(' ', '_')}@import.local",
                role="media_buyer",  # 投手角色
                is_active=True,
            )
            session.add(user)
            session.flush()
            self._users_cache[username] = user.id
            self.stats["users"]["created"] += 1
            self.log(f"创建用户: {username}", "OK")
            return user.id

        return None

    def get_or_create_account(
        self,
        session,
        account_name: str,
        account_id: Optional[str] = None,
        platform: str = "FB",
        region: str = "Other"
    ) -> Optional[int]:
        """获取或创建广告账户"""
        if not account_name:
            return None

        cache_key = account_name.strip()
        if cache_key in self._accounts_cache:
            return self._accounts_cache[cache_key]

        # 尝试通过名称或 ID 查找
        account = None
        if account_id:
            account = session.query(AdAccount).filter(
                AdAccount.account_id == account_id
            ).first()

        if not account:
            account = session.query(AdAccount).filter(
                AdAccount.name == account_name.strip()
            ).first()

        if account:
            self._accounts_cache[cache_key] = account.id
            self.stats["ad_accounts"]["found"] += 1
            return account.id

        # 如果不是 dry_run，创建新账户
        if not self.dry_run:
            # 获取或创建渠道
            channel_id = self.get_or_create_channel(session, platform)

            account = AdAccount(
                account_id=account_id or f"IMP-{cache_key[:20]}",
                name=account_name.strip()[:200],
                platform=self.normalize_platform(platform),
                channel_id=channel_id,
                status="active",
                balance=Decimal("0.00"),
            )
            session.add(account)
            session.flush()
            self._accounts_cache[cache_key] = account.id
            self.stats["ad_accounts"]["created"] += 1
            self.log(f"创建账户: {account_name[:50]}", "OK")
            return account.id

        return None

    def get_or_create_channel(self, session, platform: str) -> Optional[int]:
        """获取或创建渠道"""
        platform = self.normalize_platform(platform)
        if platform in self._channels_cache:
            return self._channels_cache[platform]

        channel = session.query(Channel).filter(
            Channel.name == platform
        ).first()

        if channel:
            self._channels_cache[platform] = channel.id
            return channel.id

        if not self.dry_run:
            channel = Channel(
                name=platform,
                platform=platform,
                is_active=True,
            )
            session.add(channel)
            session.flush()
            self._channels_cache[platform] = channel.id
            return channel.id

        return None

    # ==================== 日报导入 ====================

    def import_daily_reports(self) -> Dict[str, int]:
        """导入日报数据"""
        self.log("=" * 60)
        self.log("开始导入日报数据...")

        # 查找日报 CSV 文件
        daily_report_file = CSV_DIR / "tou_shou_ri_bao_hui_fu_di_1_zhang_biao_dan_hui_fu.csv"

        if not daily_report_file.exists():
            self.log(f"文件不存在: {daily_report_file}", "ERR")
            return self.stats["daily_reports"]

        session = self.Session()

        try:
            with open(daily_report_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.log(f"读取到 {len(rows)} 条记录")

            for i, row in enumerate(rows):
                try:
                    self._process_daily_report_row(session, row, i + 1)

                    # 每 100 条提交一次
                    if (i + 1) % 100 == 0:
                        if not self.dry_run:
                            session.commit()
                        self.log(f"已处理 {i + 1}/{len(rows)} 条")

                except Exception as e:
                    self.stats["daily_reports"]["errors"] += 1
                    self.log(f"行 {i + 1} 错误: {e}", "ERR")
                    session.rollback()

            # 最终提交
            if not self.dry_run:
                session.commit()

            self.log(f"日报导入完成: 插入 {self.stats['daily_reports']['inserted']}, "
                    f"更新 {self.stats['daily_reports']['updated']}, "
                    f"跳过 {self.stats['daily_reports']['skipped']}, "
                    f"错误 {self.stats['daily_reports']['errors']}")

        except Exception as e:
            self.log(f"导入失败: {e}", "ERR")
            session.rollback()
            raise
        finally:
            session.close()

        return self.stats["daily_reports"]

    def _process_daily_report_row(self, session, row: Dict[str, str], row_num: int):
        """处理单条日报记录"""
        # 解析字段
        # CSV 列: 时间戳记, 日期, 投手, 地区, 广告消耗（AD Spend） 美元(USD),
        #         成效（result）, 进粉数（people）, 平台, 单粉成本, 单次成效费用, 所属团队

        report_date = self.parse_date(row.get("日期", ""))
        if not report_date:
            self.stats["daily_reports"]["skipped"] += 1
            return

        pitcher_name = row.get("投手", "").strip()
        region = self.normalize_region(row.get("地区", ""))
        platform = self.normalize_platform(row.get("平台", ""))
        raw_spend = self.parse_decimal(row.get("广告消耗（AD Spend） 美元(USD)", "0"))
        result_count = self.parse_int(row.get("成效（result）", "0"))
        follows_count = self.parse_int(row.get("进粉数（people）", "0"))
        team = row.get("所属团队（team）", "").strip()

        # 获取或创建用户
        user_id = self.get_or_create_user(session, pitcher_name)

        # 需要账户 - 使用投手名+日期+地区作为唯一标识创建虚拟账户
        account_name = f"导入账户-{pitcher_name}-{region}"
        account_id = self.get_or_create_account(
            session,
            account_name,
            account_id=None,
            platform=platform,
            region=region
        )

        if not account_id:
            self.stats["daily_reports"]["skipped"] += 1
            return

        # 检查是否已存在
        existing = session.query(DailyReport).filter(
            DailyReport.ad_account_id == account_id,
            DailyReport.report_date == report_date
        ).first()

        if existing:
            # 更新现有记录
            existing.region = region
            existing.platform = platform
            existing.raw_spend = raw_spend
            existing.result_count = result_count
            existing.follows_count = follows_count
            existing.notes = f"团队: {team}" if team else None
            self.stats["daily_reports"]["updated"] += 1
        else:
            # 创建新记录
            if not self.dry_run:
                daily_report = DailyReport(
                    report_date=report_date,
                    ad_account_id=account_id,
                    region=region,
                    platform=platform,
                    raw_spend=raw_spend,
                    result_count=result_count,
                    follows_count=follows_count,
                    conversions_raw=follows_count,
                    status="raw_submitted",
                    submitted_by=user_id,
                    submitted_at=datetime.now(),
                    notes=f"团队: {team}" if team else "CSV导入",
                )
                session.add(daily_report)
            self.stats["daily_reports"]["inserted"] += 1

    # ==================== 消耗数据导入 ====================

    def import_spend_data(self) -> Dict[str, int]:
        """导入消耗汇总数据"""
        self.log("=" * 60)
        self.log("开始导入消耗数据...")

        # 查找所有消耗汇总 CSV 文件
        spend_files = list(CSV_DIR.glob("12yue_xiao_hao_hui_zong_zz_*_xiao_hao_hui_zong_biao.csv"))

        if not spend_files:
            self.log("未找到消耗汇总文件", "WARN")
            return {}

        self.log(f"找到 {len(spend_files)} 个消耗汇总文件")

        session = self.Session()
        total_rows = 0

        try:
            for csv_file in spend_files:
                self.log(f"处理: {csv_file.name}")

                with open(csv_file, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                if not rows:
                    continue

                for i, row in enumerate(rows):
                    try:
                        self._process_spend_row(session, row, i + 1)
                        total_rows += 1

                        if total_rows % 100 == 0:
                            if not self.dry_run:
                                session.commit()
                            self.log(f"已处理 {total_rows} 条消耗记录")

                    except Exception as e:
                        self.log(f"行 {i + 1} 错误: {e}", "ERR")

            if not self.dry_run:
                session.commit()

            self.log(f"消耗数据导入完成: 共处理 {total_rows} 条")

        except Exception as e:
            self.log(f"导入失败: {e}", "ERR")
            session.rollback()
            raise
        finally:
            session.close()

        return {"total": total_rows}

    def _process_spend_row(self, session, row: Dict[str, str], row_num: int):
        """处理单条消耗记录"""
        # CSV 列: 日期, 地区, 投手, 账户名称/ID, 账户种类, 代理商, 平台,
        #         转点截图Today MAX, 转点截图yesterday MAX, 备注, 手续费, 实际消耗, 包含手续费的消耗

        report_date = self.parse_date(row.get("日期", ""))
        if not report_date:
            return

        pitcher_name = row.get("投手", "").strip()
        region = self.normalize_region(row.get("地区", ""))
        platform = self.normalize_platform(row.get("平台", "FB"))
        account_str = row.get("账户名称/ID", "").strip()
        actual_spend = self.parse_decimal(row.get("实际消耗", "0"))
        fee = self.parse_decimal(row.get("手续费", "0"))

        if not account_str or actual_spend == 0:
            return

        # 获取或创建用户
        user_id = self.get_or_create_user(session, pitcher_name)

        # 提取账户 ID
        account_id_str = self.extract_account_id(account_str)

        # 获取或创建账户
        account_id = self.get_or_create_account(
            session,
            account_str,
            account_id=account_id_str,
            platform=platform,
            region=region
        )

        if not account_id:
            return

        # 检查是否已存在日报
        existing = session.query(DailyReport).filter(
            DailyReport.ad_account_id == account_id,
            DailyReport.report_date == report_date
        ).first()

        if existing:
            # 更新消耗数据
            existing.raw_spend = actual_spend
            existing.real_spend = actual_spend + fee
        else:
            # 创建新日报
            if not self.dry_run:
                daily_report = DailyReport(
                    report_date=report_date,
                    ad_account_id=account_id,
                    region=region,
                    platform=platform,
                    raw_spend=actual_spend,
                    real_spend=actual_spend + fee,
                    status="raw_submitted",
                    submitted_by=user_id,
                    submitted_at=datetime.now(),
                    notes=f"消耗汇总导入",
                )
                session.add(daily_report)

    # ==================== 主入口 ====================

    def import_all(self):
        """导入所有数据"""
        self.log("=" * 60)
        self.log("开始批量导入 CSV 数据")
        self.log(f"数据目录: {CSV_DIR}")
        self.log(f"Dry Run: {self.dry_run}")
        self.log("=" * 60)

        # 1. 导入日报
        self.import_daily_reports()

        # 2. 导入消耗数据
        self.import_spend_data()

        # 打印统计
        self.log("=" * 60)
        self.log("导入统计:")
        self.log(f"  日报: 插入 {self.stats['daily_reports']['inserted']}, "
                f"更新 {self.stats['daily_reports']['updated']}, "
                f"跳过 {self.stats['daily_reports']['skipped']}, "
                f"错误 {self.stats['daily_reports']['errors']}")
        self.log(f"  账户: 创建 {self.stats['ad_accounts']['created']}, "
                f"复用 {self.stats['ad_accounts']['found']}")
        self.log(f"  用户: 创建 {self.stats['users']['created']}, "
                f"复用 {self.stats['users']['found']}")


def main():
    parser = argparse.ArgumentParser(description="导入 CSV 数据到数据库")
    parser.add_argument(
        "--type",
        choices=["daily_reports", "spend", "all"],
        default="all",
        help="导入类型"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅模拟运行，不实际写入数据库"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="静默模式"
    )

    args = parser.parse_args()

    importer = DataImporter(
        dry_run=args.dry_run,
        verbose=not args.quiet
    )

    if args.type == "daily_reports":
        importer.import_daily_reports()
    elif args.type == "spend":
        importer.import_spend_data()
    else:
        importer.import_all()


if __name__ == "__main__":
    main()
