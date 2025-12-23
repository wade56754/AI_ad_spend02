from pathlib import Path
import pandas as pd
from frictionless import Package, Resource
from slugify import slugify

# =========================
# 配置路径
# =========================
PROJECT_ROOT = Path(__file__).parent
RAW_DIR = PROJECT_ROOT / "dataset" / "raw"
OUT_DIR = PROJECT_ROOT / "dataset" / "out"
CSV_DIR = OUT_DIR / "csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# 工具函数
# =========================
def resource_name_from(file_stem: str, sheet: str) -> str:
    """
    生成符合 Frictionless 规范的 resource.name
    规则：
    - 仅 ascii
    - 小写
    - 下划线分隔
    - 稳定可复现
    """
    raw = f"{file_stem}__{sheet}"
    return slugify(
        raw,
        lowercase=True,
        separator="_",
        allow_unicode=False
    )


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    基础清洗（MVP 级）：
    - 删除完全为空的列（常见 Unnamed: 0）
    - 保留原始字段名（不自动英文化，避免口径丢失）
    """
    df = df.dropna(axis=1, how="all")
    return df


# =========================
# 主流程
# =========================
resources = []
resource_map_rows = []

for xlsx in RAW_DIR.glob("*.xlsx"):
    try:
        excel = pd.ExcelFile(xlsx)
    except Exception as e:
        print(f"[SKIP] 无法读取 Excel: {xlsx.name} ({e})")
        continue

    for sheet in excel.sheet_names:
        try:
            df = excel.parse(sheet)
        except Exception as e:
            print(f"[SKIP] 无法读取 Sheet: {xlsx.name} / {sheet} ({e})")
            continue

        df = clean_dataframe(df)

        resource_name = resource_name_from(xlsx.stem, sheet)
        csv_path = CSV_DIR / f"{resource_name}.csv"

        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        resources.append(
            Resource(
                name=resource_name,
                path=str(csv_path.relative_to(OUT_DIR)),
                description=f"源文件: {xlsx.name} | Sheet: {sheet}"
            )
        )

        resource_map_rows.append({
            "resource_name": resource_name,
            "source_file": xlsx.name,
            "sheet_name": sheet,
            "row_count": len(df),
            "column_count": len(df.columns)
        })


# =========================
# 写出 Data Package
# =========================
package = Package(resources=resources)
package_path = OUT_DIR / "datapackage.json"
package.to_json(str(package_path))


# =========================
# 写出资源映射表（强烈建议保留）
# =========================
resource_map_df = pd.DataFrame(resource_map_rows)
resource_map_path = OUT_DIR / "resource_map.csv"
resource_map_df.to_csv(resource_map_path, index=False, encoding="utf-8-sig")


# =========================
# 控制台输出
# =========================
print("=" * 60)
print("[OK] Data Package 生成完成")
print(f"- datapackage.json : {package_path}")
print(f"- CSV 输出目录     : {CSV_DIR}")
print(f"- 资源映射表       : {resource_map_path}")
print(f"- 资源总数         : {len(resources)}")
print("=" * 60)
