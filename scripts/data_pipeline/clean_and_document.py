"""
数据清洗与文档生成脚本
目标：将原始数据转换为 AI 可理解的规范化格式

输出：
1. dataset/out/clean/*.csv - 清洗后的核心表
2. dataset/out/schema/*.json - JSON Schema 定义
3. dataset/out/DATA_DICTIONARY.md - 数据字典文档
4. dataset/out/AI_CONTEXT.md - AI 专用上下文文档
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# =========================
# 配置
# =========================
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_CSV_DIR = PROJECT_ROOT / "dataset" / "out" / "csv"
OUT_DIR = PROJECT_ROOT / "dataset" / "out"
CLEAN_DIR = OUT_DIR / "clean"
SCHEMA_DIR = OUT_DIR / "schema"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)
SCHEMA_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# 核心表配置
# =========================
CORE_TABLES = {
    "ad_spend_daily": {
        "sources": [
            "12yue_xiao_hao_hui_zong_zz_7yue_xiao_hao_hui_zong_biao.csv",
            "12yue_xiao_hao_hui_zong_zz_8yue_xiao_hao_hui_zong_biao.csv",
            "12yue_xiao_hao_hui_zong_zz_9yue_xiao_hao_hui_zong_biao.csv",
            "12yue_xiao_hao_hui_zong_zz_10yue_xiao_hao_hui_zong_biao.csv",
            "12yue_xiao_hao_hui_zong_zz_11yue_xiao_hao_hui_zong_biao.csv",
            "12yue_xiao_hao_hui_zong_zz_12yue_xiao_hao_hui_zong_biao.csv",
        ],
        "description": "平台广告消耗明细表（日+账户粒度）",
        "domain": "数据域",
        "grain": "每日每账户消耗记录",
    },
    "daily_report": {
        "sources": ["tou_shou_ri_bao_hui_fu_di_1_zhang_biao_dan_hui_fu.csv"],
        "description": "投手日报事实表（投手自报）",
        "domain": "人域",
        "grain": "每日每投手每地区汇报",
    },
    "media_buyer_dim": {
        "sources": ["tou_shou_ri_bao_hui_fu_tou_shou_xin_xi.csv"],
        "description": "投手维度表",
        "domain": "人域",
        "grain": "一投手一行",
    },
    "project_pnl": {
        "sources": ["shou_zhi_biao_ming_xi_biao.csv"],
        "description": "项目收支明细表",
        "domain": "钱域",
        "grain": "每月每项目收支",
    },
    "monthly_finance_summary": {
        "sources": ["12yue_shou_zhi_biao_hui_zong_shou_zhi_biao_hui_zong.csv"],
        "description": "月度财务汇总表",
        "domain": "钱域",
        "grain": "每月汇总",
    },
}

# 字段映射（原始列名 -> 规范列名）
FIELD_MAPPINGS = {
    "ad_spend_daily": {
        0: "date",  # 日期
        1: "region",  # 地区
        2: "media_buyer",  # 投手
        3: "account_raw",  # 账户名称/ID（原始）
        4: "account_type",  # 账户种类
        5: "agent",  # 代理商
        6: "platform",  # 平台
        7: "spend_today_cumulative",  # 转点截图Today MAX
        8: "spend_yesterday_cumulative",  # 转点截图yesterday MAX
        9: "notes",  # 备注
        10: "fee",  # 手续费
        11: "actual_spend",  # 实际消耗
        12: "spend_with_fee",  # 包含手续费的消耗
    },
    "daily_report": {
        0: "timestamp",
        1: "date",
        2: "media_buyer",
        3: "region",
        4: "ad_spend_usd",
        5: "result_count",
        6: "lead_count",
        7: "platform",
        8: "cost_per_lead",
        9: "cost_per_result",
        10: "team",
    },
    "media_buyer_dim": {
        0: "media_buyer",
        1: "team_raw",
    },
    "project_pnl": {
        0: "month",
        1: "team",
        2: "business_type",
        3: "region",
        4: "project_name",
        5: "lead_count",
        6: "total_spend",
        7: "actual_revenue",
        8: "gross_profit",
        9: "prepaid_balance",
        10: "notes",
    },
}


# =========================
# 清洗函数
# =========================
def extract_platform_id(raw: str) -> dict:
    """从账户原始字段提取平台ID和账户名"""
    if pd.isna(raw):
        return {"platform_id": None, "account_name": None}
    raw = str(raw).strip()
    match = re.search(r"(\d{13,})$", raw)
    if match:
        platform_id = match.group(1)
        account_name = raw[: match.start()].strip()
        return {"platform_id": platform_id, "account_name": account_name}
    return {"platform_id": None, "account_name": raw}


def normalize_team(team_raw: str) -> str:
    """团队名称规范化"""
    if pd.isna(team_raw):
        return "UNKNOWN"
    team = str(team_raw).strip()
    mapping = {
        "深圳团队": "SZ",
        "郑州团队": "ZZ",
        "金边团队": "ZZ",  # 合并到郑州
        "外包团队": "EXT",
    }
    return mapping.get(team, team)


def normalize_region(region_raw: str) -> str:
    """地区名称规范化"""
    if pd.isna(region_raw):
        return "UNKNOWN"
    region = str(region_raw).strip()
    # 去除括号内容
    region = re.sub(r"\s*[（(].*?[)）]", "", region)
    mapping = {
        "印度": "IN",
        "India": "IN",
        "德国": "DE",
        "Germany": "DE",
        "新加坡": "SG",
        "Singapore": "SG",
        "加拿大": "CA",
        "Canada": "CA",
        "美国": "US",
        "USA": "US",
        "马来": "MY",
        "马来西亚": "MY",
        "Malaysia": "MY",
        "日本": "JP",
        "Japan": "JP",
        "印尼": "ID",
        "Indonesia": "ID",
        "土耳其": "TR",
        "Turkey": "TR",
        "瑞典": "SE",
        "Sweden": "SE",
        "韩国": "KR",
        "Korea": "KR",
        "尼日利亚": "NG",
        "Nigeria": "NG",
        "比利时": "BE",
        "Belgium": "BE",
    }
    return mapping.get(region, region)


def clean_numeric(val: Any) -> float | None:
    """清洗数值字段"""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s in ["", "-", "#DIV/0!", "#VALUE!", "#REF!"]:
        return None
    try:
        # 移除逗号和货币符号
        s = re.sub(r"[,$￥]", "", s)
        return float(s)
    except ValueError:
        return None


def clean_date(val: Any) -> str | None:
    """清洗日期字段"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    # 尝试解析常见格式
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(s[:10], fmt[:8] if len(s) >= 10 else fmt).strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            continue
    return s[:10] if len(s) >= 10 else s


# =========================
# 表清洗逻辑
# =========================
def clean_ad_spend_daily(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """清洗消耗明细表"""
    all_rows = []

    for df in dfs:
        # 重命名列
        df.columns = range(len(df.columns))
        mapping = FIELD_MAPPINGS["ad_spend_daily"]
        df = df.rename(columns={k: v for k, v in mapping.items() if k < len(df.columns)})

        for _, row in df.iterrows():
            # 提取平台ID
            account_info = extract_platform_id(row.get("account_raw", ""))

            clean_row = {
                "date": clean_date(row.get("date")),
                "region": normalize_region(row.get("region")),
                "media_buyer": str(row.get("media_buyer", "")).strip(),
                "platform_id": account_info["platform_id"],
                "account_name": account_info["account_name"],
                "account_type": str(row.get("account_type", "")).strip(),
                "agent": str(row.get("agent", "")).strip(),
                "platform": str(row.get("platform", "")).strip(),
                "spend_today_cumulative": clean_numeric(
                    row.get("spend_today_cumulative")
                ),
                "spend_yesterday_cumulative": clean_numeric(
                    row.get("spend_yesterday_cumulative")
                ),
                "fee": clean_numeric(row.get("fee")),
                "actual_spend": clean_numeric(row.get("actual_spend")),
                "spend_with_fee": clean_numeric(row.get("spend_with_fee")),
                "notes": str(row.get("notes", "")).strip()
                if pd.notna(row.get("notes"))
                else None,
            }

            # 过滤无效行
            if clean_row["date"] and clean_row["platform_id"]:
                # 仅保留2025年数据
                if clean_row["date"].startswith("2025"):
                    all_rows.append(clean_row)

    return pd.DataFrame(all_rows)


def clean_daily_report(df: pd.DataFrame) -> pd.DataFrame:
    """清洗投手日报"""
    df.columns = range(len(df.columns))
    mapping = FIELD_MAPPINGS["daily_report"]
    df = df.rename(columns={k: v for k, v in mapping.items() if k < len(df.columns)})

    clean_rows = []
    for _, row in df.iterrows():
        clean_row = {
            "date": clean_date(row.get("date")),
            "media_buyer": str(row.get("media_buyer", "")).strip(),
            "region": normalize_region(row.get("region")),
            "team": normalize_team(row.get("team")),
            "ad_spend_usd": clean_numeric(row.get("ad_spend_usd")),
            "result_count": clean_numeric(row.get("result_count")),
            "lead_count": clean_numeric(row.get("lead_count")),
            "platform": str(row.get("platform", "")).strip()
            if pd.notna(row.get("platform"))
            else None,
            "cost_per_lead": clean_numeric(row.get("cost_per_lead")),
            "cost_per_result": clean_numeric(row.get("cost_per_result")),
        }

        if clean_row["date"] and clean_row["media_buyer"]:
            if clean_row["date"].startswith("2025"):
                clean_rows.append(clean_row)

    return pd.DataFrame(clean_rows)


def clean_media_buyer_dim(df: pd.DataFrame) -> pd.DataFrame:
    """清洗投手维度表"""
    df.columns = range(len(df.columns))
    mapping = FIELD_MAPPINGS["media_buyer_dim"]
    df = df.rename(columns={k: v for k, v in mapping.items() if k < len(df.columns)})

    clean_rows = []
    seen = set()
    for _, row in df.iterrows():
        buyer = str(row.get("media_buyer", "")).strip()
        team = normalize_team(row.get("team_raw"))

        if buyer and buyer not in seen:
            seen.add(buyer)
            clean_rows.append({"media_buyer": buyer, "team": team})

    return pd.DataFrame(clean_rows)


def clean_project_pnl(df: pd.DataFrame) -> pd.DataFrame:
    """清洗项目收支表"""
    df.columns = range(len(df.columns))
    mapping = FIELD_MAPPINGS["project_pnl"]
    df = df.rename(columns={k: v for k, v in mapping.items() if k < len(df.columns)})

    clean_rows = []
    for _, row in df.iterrows():
        month_raw = str(row.get("month", "")).strip()
        # 跳过非数据行
        if not month_raw or month_raw in ["月份", ""]:
            continue

        clean_row = {
            "month": month_raw,
            "team": normalize_team(row.get("team")),
            "business_type": str(row.get("business_type", "")).strip(),
            "region": normalize_region(row.get("region")),
            "project_name": str(row.get("project_name", "")).strip(),
            "lead_count": clean_numeric(row.get("lead_count")),
            "total_spend": clean_numeric(row.get("total_spend")),
            "actual_revenue": clean_numeric(row.get("actual_revenue")),
            "gross_profit": clean_numeric(row.get("gross_profit")),
            "prepaid_balance": str(row.get("prepaid_balance", "")).strip()
            if pd.notna(row.get("prepaid_balance"))
            else None,
            "notes": str(row.get("notes", "")).strip()
            if pd.notna(row.get("notes"))
            else None,
        }

        if clean_row["project_name"]:
            clean_rows.append(clean_row)

    return pd.DataFrame(clean_rows)


# =========================
# Schema 生成
# =========================
def infer_schema(df: pd.DataFrame, table_config: dict) -> dict:
    """从 DataFrame 推断 JSON Schema"""
    properties = {}
    required = []

    for col in df.columns:
        dtype = df[col].dtype
        sample_values = df[col].dropna().head(3).tolist()

        if dtype == "object":
            col_type = "string"
        elif dtype in ["int64", "int32"]:
            col_type = "integer"
        elif dtype in ["float64", "float32"]:
            col_type = "number"
        elif dtype == "bool":
            col_type = "boolean"
        else:
            col_type = "string"

        properties[col] = {
            "type": [col_type, "null"],
            "examples": [str(v) for v in sample_values],
        }

        # 标记非空字段为必填
        if df[col].notna().all():
            required.append(col)

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": table_config.get("description", ""),
        "description": f"Domain: {table_config.get('domain', '')} | Grain: {table_config.get('grain', '')}",
        "type": "object",
        "properties": properties,
        "required": required,
    }


# =========================
# 文档生成
# =========================
def generate_data_dictionary(tables: dict[str, pd.DataFrame], configs: dict) -> str:
    """生成数据字典 Markdown"""
    lines = [
        "# 数据字典 (Data Dictionary)",
        "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "> 数据范围: 2025年",
        "",
        "## 概览",
        "",
        "| 表名 | 域 | 粒度 | 行数 | 说明 |",
        "|------|-----|------|------|------|",
    ]

    for name, df in tables.items():
        cfg = configs.get(name, {})
        lines.append(
            f"| {name} | {cfg.get('domain', '-')} | {cfg.get('grain', '-')} | {len(df)} | {cfg.get('description', '-')} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    for name, df in tables.items():
        cfg = configs.get(name, {})
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"**{cfg.get('description', '')}**")
        lines.append("")
        lines.append(f"- 域: {cfg.get('domain', '-')}")
        lines.append(f"- 粒度: {cfg.get('grain', '-')}")
        lines.append(f"- 行数: {len(df)}")
        lines.append("")
        lines.append("### 字段说明")
        lines.append("")
        lines.append("| 字段 | 类型 | 非空率 | 示例值 |")
        lines.append("|------|------|--------|--------|")

        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null_rate = f"{df[col].notna().mean() * 100:.1f}%"
            samples = df[col].dropna().head(2).tolist()
            sample_str = ", ".join([str(s)[:30] for s in samples])
            lines.append(f"| {col} | {dtype} | {non_null_rate} | {sample_str} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def generate_ai_context(tables: dict[str, pd.DataFrame], configs: dict) -> str:
    """生成 AI 专用上下文文档"""
    lines = [
        "# AI 数据上下文 (AI Data Context)",
        "",
        "本文档为 AI 助手提供数据理解的关键信息。",
        "",
        "## 业务背景",
        "",
        "这是一个 **广告代投管理系统** 的核心数据集，管理视角的四个维度：",
        "- **人**: 投手(media_buyer)、团队(team)、绩效",
        "- **事**: 项目(project)、地区(region)、进度",
        "- **钱**: 消耗(spend)、收入(revenue)、利润(profit)、充值(topup)",
        "- **数据**: 平台消耗对账、手续费计算、成效统计",
        "",
        "## 团队编码",
        "",
        "| 代码 | 名称 | 说明 |",
        "|------|------|------|",
        "| SZ | 深圳团队 | 主力团队 |",
        "| ZZ | 郑州团队 | 含原金边团队 |",
        "| EXT | 外包 | 单独核算 |",
        "",
        "## 地区编码 (ISO 3166-1)",
        "",
        "| 代码 | 名称 |",
        "|------|------|",
        "| IN | 印度 |",
        "| DE | 德国 |",
        "| SG | 新加坡 |",
        "| US | 美国 |",
        "| MY | 马来西亚 |",
        "| TR | 土耳其 |",
        "| ID | 印尼 |",
        "",
        "## 核心表关系",
        "",
        "```",
        "ad_spend_daily (平台真实消耗)",
        "    ├── media_buyer → media_buyer_dim.media_buyer",
        "    └── 对账 → daily_report (按 date + media_buyer + region)",
        "",
        "daily_report (投手自报)",
        "    └── team → media_buyer_dim.team",
        "",
        "project_pnl (项目收支)",
        "    └── team, region → 可聚合验证",
        "```",
        "",
        "## 金额口径说明",
        "",
        "| 字段 | 口径 | 计算逻辑 |",
        "|------|------|----------|",
        "| actual_spend | 实际消耗 | 当日平台扣费金额 |",
        "| fee | 手续费 | actual_spend × 代理商费率 |",
        "| spend_with_fee | 含手续费消耗 | actual_spend + fee |",
        "| ad_spend_usd | 投手自报消耗 | 投手填报金额，需与 actual_spend 对账 |",
        "| gross_profit | 项目毛利 | actual_revenue - total_spend |",
        "",
        "## 唯一键定义",
        "",
        "| 表 | 唯一键 |",
        "|-----|--------|",
        "| ad_spend_daily | (date, platform_id) |",
        "| daily_report | (date, media_buyer, region) |",
        "| media_buyer_dim | media_buyer |",
        "| project_pnl | (month, team, project_name) |",
        "",
        "## 数据质量注意",
        "",
        "1. `platform_id` 为 Facebook 广告账户 ID (15-16位数字)",
        "2. `#DIV/0!` 等 Excel 错误值已清洗为 null",
        "3. 2024年数据已归档，当前仅含2025年",
        "4. 代理商费率需从独立费率表获取",
        "",
    ]

    # 添加各表样本数据
    lines.append("## 样本数据")
    lines.append("")

    for name, df in tables.items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append("```json")
        sample = df.head(3).to_dict(orient="records")
        lines.append(json.dumps(sample, ensure_ascii=False, indent=2, default=str))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


# =========================
# 主流程
# =========================
def main():
    print("=" * 60)
    print("开始数据清洗与文档生成")
    print("=" * 60)

    cleaned_tables = {}

    # 1. 清洗 ad_spend_daily
    print("\n[1/5] 清洗 ad_spend_daily...")
    dfs = []
    for src in CORE_TABLES["ad_spend_daily"]["sources"]:
        path = RAW_CSV_DIR / src
        if path.exists():
            dfs.append(pd.read_csv(path))
            print(f"  - 加载: {src}")
    if dfs:
        cleaned_tables["ad_spend_daily"] = clean_ad_spend_daily(dfs)
        print(f"  - 清洗后行数: {len(cleaned_tables['ad_spend_daily'])}")

    # 2. 清洗 daily_report
    print("\n[2/5] 清洗 daily_report...")
    src = CORE_TABLES["daily_report"]["sources"][0]
    path = RAW_CSV_DIR / src
    if path.exists():
        df = pd.read_csv(path)
        cleaned_tables["daily_report"] = clean_daily_report(df)
        print(f"  - 清洗后行数: {len(cleaned_tables['daily_report'])}")

    # 3. 清洗 media_buyer_dim
    print("\n[3/5] 清洗 media_buyer_dim...")
    src = CORE_TABLES["media_buyer_dim"]["sources"][0]
    path = RAW_CSV_DIR / src
    if path.exists():
        df = pd.read_csv(path)
        cleaned_tables["media_buyer_dim"] = clean_media_buyer_dim(df)
        print(f"  - 清洗后行数: {len(cleaned_tables['media_buyer_dim'])}")

    # 4. 清洗 project_pnl
    print("\n[4/5] 清洗 project_pnl...")
    src = CORE_TABLES["project_pnl"]["sources"][0]
    path = RAW_CSV_DIR / src
    if path.exists():
        df = pd.read_csv(path)
        cleaned_tables["project_pnl"] = clean_project_pnl(df)
        print(f"  - 清洗后行数: {len(cleaned_tables['project_pnl'])}")

    # 5. 保存清洗后的数据
    print("\n[5/5] 保存清洗后的数据...")
    for name, df in cleaned_tables.items():
        # 保存 CSV
        csv_path = CLEAN_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"  - CSV: {csv_path}")

        # 保存 JSON Schema
        schema = infer_schema(df, CORE_TABLES.get(name, {}))
        schema_path = SCHEMA_DIR / f"{name}.schema.json"
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        print(f"  - Schema: {schema_path}")

    # 6. 生成文档
    print("\n[6/6] 生成文档...")

    # 数据字典
    dict_md = generate_data_dictionary(cleaned_tables, CORE_TABLES)
    dict_path = OUT_DIR / "DATA_DICTIONARY.md"
    with open(dict_path, "w", encoding="utf-8") as f:
        f.write(dict_md)
    print(f"  - 数据字典: {dict_path}")

    # AI 上下文
    ai_md = generate_ai_context(cleaned_tables, CORE_TABLES)
    ai_path = OUT_DIR / "AI_CONTEXT.md"
    with open(ai_path, "w", encoding="utf-8") as f:
        f.write(ai_md)
    print(f"  - AI 上下文: {ai_path}")

    print("\n" + "=" * 60)
    print("[OK] 数据清洗与文档生成完成")
    print(f"- 清洗后数据: {CLEAN_DIR}")
    print(f"- Schema 定义: {SCHEMA_DIR}")
    print(f"- 数据字典: {dict_path}")
    print(f"- AI 上下文: {ai_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

