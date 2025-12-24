#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间戳注�?Hook - SessionStart 时注入北京时间上下文
�?Claude 了解当前时间、日期、工作日等信�?
用法:
    作为 SessionStart hook 自动运行
    或手动运�? python inject_timestamp.py
"""

import io
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Windows UTF-8 编码设置
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

# 2025年中国法定节假日（可根据实际情况更新�?HOLIDAYS_2025 = {
    "2025-01-01",  # 元旦
    "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",  # 春节
    "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04",
    "2025-04-04", "2025-04-05", "2025-04-06",  # 清明
    "2025-05-01", "2025-05-02", "2025-05-03", "2025-05-04", "2025-05-05",  # 劳动�?    "2025-05-31", "2025-06-01", "2025-06-02",  # 端午
    "2025-10-01", "2025-10-02", "2025-10-03", "2025-10-04",  # 国庆+中秋
    "2025-10-05", "2025-10-06", "2025-10-07",
}

# 调休工作�?WORKDAYS_2025 = {
    "2025-01-26", "2025-02-08",  # 春节调休
    "2025-04-27",  # 劳动节调�?    "2025-09-28", "2025-10-11",  # 国庆调休
}


def get_beijing_time() -> dict:
    """获取北京时间及相关信�?""
    now = datetime.now(BEIJING_TZ)
    date_str = now.strftime("%Y-%m-%d")
    
    weekdays_cn = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekdays_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_idx = now.weekday()
    
    # 判断是否工作�?    is_weekend = weekday_idx >= 5
    is_holiday = date_str in HOLIDAYS_2025
    is_makeup_workday = date_str in WORKDAYS_2025
    
    if is_makeup_workday:
        is_workday = True
        day_type = "调休工作�?
    elif is_holiday:
        is_workday = False
        day_type = "法定假日"
    elif is_weekend:
        is_workday = False
        day_type = "周末"
    else:
        is_workday = True
        day_type = "工作�?
    
    # 时段判断
    hour = now.hour
    periods = [
        (5, 9, "早晨", "morning", "🌅"),
        (9, 12, "上午", "forenoon", "☀�?),
        (12, 14, "中午", "noon", "🌞"),
        (14, 18, "下午", "afternoon", "🌤�?),
        (18, 22, "晚上", "evening", "🌆"),
    ]
    period, period_en, emoji = "深夜", "night", "🌙"
    for start, end, p, p_en, e in periods:
        if start <= hour < end:
            period, period_en, emoji = p, p_en, e
            break
    
    # 季节
    month = now.month
    seasons = {(3,4,5): "春季", (6,7,8): "夏季", (9,10,11): "秋季", (12,1,2): "冬季"}
    season = next(s for months, s in seasons.items() if month in months)
    
    return {
        "timestamp": now.isoformat(),
        "date": date_str,
        "time": now.strftime("%H:%M:%S"),
        "year": now.year, "month": now.month, "day": now.day,
        "hour": now.hour, "minute": now.minute,
        "weekday": weekday_idx,
        "weekday_cn": weekdays_cn[weekday_idx],
        "weekday_en": weekdays_en[weekday_idx],
        "is_workday": is_workday,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "day_type": day_type,
        "period": period,
        "period_en": period_en,
        "period_emoji": emoji,
        "season": season,
        "display_cn": f"{now.strftime('%Y�?m�?d�?)} {weekdays_cn[weekday_idx]} {period} {now.strftime('%H:%M')}",
    }


def main():
    time_info = get_beijing_time()
    workday_icon = "💼" if time_info["is_workday"] else "🏖�?
    
    msg = f"""
┌─────────────────────────────────────────────────────�?�? {time_info['period_emoji']} 北京时间 (UTC+8)
�? 📅 {time_info['display_cn']}
�? 📆 {time_info['day_type']} {workday_icon} | {time_info['season']}
└─────────────────────────────────────────────────────�?"""
    print(msg, file=sys.stderr)
    
    # 保存日志
    try:
        log_dir = Path(".claude/data")
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "session_timestamps.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time_info["timestamp"], "date": time_info["date"]}, ensure_ascii=False) + "\n")
    except Exception:\r\n        pass
    
    print(json.dumps({"continue": True, "context": {"current_time": time_info}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
