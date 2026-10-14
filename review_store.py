import json
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from familiar_store import PROJECT_DIR, list_familiar


REVIEW_FILE = PROJECT_DIR / "data" / "private" / "daily_review.json"


def load_review():
    if not REVIEW_FILE.exists():
        return {"date": "", "items": []}

    text = REVIEW_FILE.read_text(encoding="utf-8")
    record = json.loads(text)

    if not isinstance(record, dict):
        raise ValueError("复习记录必须是字典。")

    if not isinstance(record.get("date"), str):
        raise ValueError("复习日期必须是字符串。")

    items = record.get("items")
    if not isinstance(items, list):
        raise ValueError("复习条目必须是列表。")

    for filename in items:
        if not isinstance(filename, str):
            raise ValueError("复习条目必须是文件名字符串。")

    return record


def save_review(record):
    REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, ensure_ascii=False, indent=2)
    REVIEW_FILE.write_text(text, encoding="utf-8")


def get_daily_review(today=None):
    if today is None:
        today = datetime.now(
            ZoneInfo("Asia/Shanghai")
        ).date().isoformat()

    familiar = list_familiar()
    record = load_review()
    remaining = []
    if record["date"] == today:
        for record_items in record["items"]:
            if record_items in familiar:
                remaining.append(record_items)
        record["items"] = remaining
        save_review(record)
        return record
    # 在这里实现下面说明的三个分支。
    if not familiar:
        return{"date":today,"items":[]}
    count = min(3,len(familiar))
    record = {
        "date":today,
        "items": random.sample(familiar,count),
    }
    save_review(record)
    return record
