"""
Excel导入/导出列映射配置
用于灵活匹配中英文列名和数据验证

Version: 1.0
Author: Claude协作开发
"""

from typing import Dict, List, Any, Optional
from datetime import date
from decimal import Decimal


class ColumnDefinition:
    """列定义"""
    def __init__(
        self,
        field_name: str,
        cn_name: str,
        en_name: str,
        required: bool,
        data_type: str,
        aliases: Optional[List[str]] = None,
        default: Any = None,
        max_length: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ):
        self.field_name = field_name  # 数据库字段名
        self.cn_name = cn_name  # 中文列名
        self.en_name = en_name  # 英文列名
        self.required = required  # 是否必需
        self.data_type = data_type  # 数据类型: str, int, decimal, date
        self.aliases = aliases or []  # 列名别名
        self.default = default  # 默认值
        self.max_length = max_length  # 字符串最大长度
        self.min_value = min_value  # 数值最小值
        self.max_value = max_value  # 数值最大值

    def get_all_names(self) -> List[str]:
        """获取所有可能的列名（中文、英文、别名）"""
        return [self.cn_name, self.en_name] + self.aliases


# Excel列定义（按导入顺序）
EXCEL_COLUMN_DEFINITIONS = [
    ColumnDefinition(
        field_name="report_date",
        cn_name="报表日期",
        en_name="Report Date",
        required=True,
        data_type="date",
        aliases=["日期", "Date", "报告日期"]
    ),
    ColumnDefinition(
        field_name="ad_account_id",
        cn_name="广告账户ID",
        en_name="Ad Account ID",
        required=True,
        data_type="int",
        aliases=["账户ID", "Account ID", "AccountID"],
        min_value=1
    ),
    ColumnDefinition(
        field_name="campaign_name",
        cn_name="广告系列名称",
        en_name="Campaign Name",
        required=False,
        data_type="str",
        aliases=["广告系列", "Campaign", "系列名称"],
        max_length=255
    ),
    ColumnDefinition(
        field_name="ad_group_name",
        cn_name="广告组名称",
        en_name="Ad Group Name",
        required=False,
        data_type="str",
        aliases=["广告组", "Ad Group", "组名称"],
        max_length=255
    ),
    ColumnDefinition(
        field_name="ad_creative_name",
        cn_name="广告创意名称",
        en_name="Ad Creative Name",
        required=False,
        data_type="str",
        aliases=["广告创意", "Creative", "创意名称"],
        max_length=255
    ),
    ColumnDefinition(
        field_name="impressions",
        cn_name="展示次数",
        en_name="Impressions",
        required=True,
        data_type="int",
        aliases=["展示", "Impr", "曝光次数"],
        default=0,
        min_value=0,
        max_value=999999999
    ),
    ColumnDefinition(
        field_name="clicks",
        cn_name="点击次数",
        en_name="Clicks",
        required=True,
        data_type="int",
        aliases=["点击", "Click"],
        default=0,
        min_value=0,
        max_value=999999999
    ),
    ColumnDefinition(
        field_name="spend",
        cn_name="消耗金额",
        en_name="Spend",
        required=True,
        data_type="decimal",
        aliases=["消耗", "Cost", "花费", "金额"],
        default=Decimal("0"),
        min_value=0,
        max_value=9999999.99
    ),
    ColumnDefinition(
        field_name="conversions",
        cn_name="转化次数",
        en_name="Conversions",
        required=True,
        data_type="int",
        aliases=["转化", "Conv", "转化数"],
        default=0,
        min_value=0,
        max_value=999999999
    ),
    ColumnDefinition(
        field_name="new_follows",
        cn_name="新增粉丝数",
        en_name="New Follows",
        required=True,
        data_type="int",
        aliases=["新增粉丝", "粉丝数", "Follows", "粉丝"],
        default=0,
        min_value=0,
        max_value=999999999
    ),
    ColumnDefinition(
        field_name="cpa",
        cn_name="CPA",
        en_name="CPA",
        required=False,
        data_type="decimal",
        aliases=["单次转化成本", "Cost Per Action"],
        min_value=0,
        max_value=999999.99
    ),
    ColumnDefinition(
        field_name="roas",
        cn_name="ROAS",
        en_name="ROAS",
        required=False,
        data_type="decimal",
        aliases=["广告支出回报率", "Return on Ad Spend"],
        min_value=0,
        max_value=9999.99
    ),
    ColumnDefinition(
        field_name="notes",
        cn_name="备注",
        en_name="Notes",
        required=False,
        data_type="str",
        aliases=["备注信息", "Remarks", "说明"],
        max_length=500
    ),
]


# 构建列名映射字典（用于快速查找）
def build_column_mapping() -> Dict[str, ColumnDefinition]:
    """
    构建列名到ColumnDefinition的映射
    支持通过任意列名（中文、英文、别名）查找
    """
    mapping = {}
    for col_def in EXCEL_COLUMN_DEFINITIONS:
        # 添加所有可能的列名
        for name in col_def.get_all_names():
            # 忽略大小写和空格
            normalized_name = name.strip().lower()
            mapping[normalized_name] = col_def
    return mapping


COLUMN_MAPPING = build_column_mapping()


def find_column_definition(column_name: str) -> Optional[ColumnDefinition]:
    """
    根据列名查找列定义（忽略大小写和空格）

    Args:
        column_name: Excel中的列名

    Returns:
        ColumnDefinition对象，如果找不到返回None
    """
    normalized_name = column_name.strip().lower()
    return COLUMN_MAPPING.get(normalized_name)


def get_required_columns() -> List[str]:
    """
    获取所有必需列的中文名称列表

    Returns:
        必需列名列表
    """
    return [col.cn_name for col in EXCEL_COLUMN_DEFINITIONS if col.required]


def get_export_column_names() -> List[str]:
    """
    获取导出Excel时的列名（中文）

    Returns:
        导出列名列表
    """
    return [col.cn_name for col in EXCEL_COLUMN_DEFINITIONS]


def validate_column_exists(df_columns: List[str]) -> tuple[bool, List[str]]:
    """
    验证Excel文件是否包含所有必需列

    Args:
        df_columns: DataFrame的列名列表

    Returns:
        (是否通过, 缺失的必需列名列表)
    """
    missing_required = []

    for col_def in EXCEL_COLUMN_DEFINITIONS:
        if not col_def.required:
            continue

        # 检查是否有任何一个可能的列名存在
        found = False
        for possible_name in col_def.get_all_names():
            normalized_possible = possible_name.strip().lower()
            for df_col in df_columns:
                if df_col.strip().lower() == normalized_possible:
                    found = True
                    break
            if found:
                break

        if not found:
            missing_required.append(col_def.cn_name)

    return len(missing_required) == 0, missing_required


# 文件限制配置
MAX_FILE_SIZE_MB = 5  # 最大文件大小（MB）
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# 导出限制配置
MAX_EXPORT_ROWS = 5000  # 单次最多导出行数
