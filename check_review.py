"""D7 每日复习验收：临时文件与模拟候选，不修改真实个人记录。"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import review_store


def main():
    original_path = review_store.REVIEW_FILE
    original_bytes = original_path.read_bytes() if original_path.exists() else None

    try:
        with tempfile.TemporaryDirectory(prefix="studydocs-review-") as temporary:
            review_store.REVIEW_FILE = Path(temporary) / "daily_review.json"
            candidates = []

            with patch.object(
                review_store,
                "list_familiar",
                new=lambda: candidates.copy(),
            ):
                empty = review_store.get_daily_review("2026-10-14")
                assert empty == {"date": "2026-10-14", "items": []}
                assert not review_store.REVIEW_FILE.exists()
                print("PASS: 空库返回零项，不占用当天首次抽取")

                candidates.append("python_print.md")
                one = review_store.get_daily_review("2026-10-14")
                assert one == {"date": "2026-10-14", "items": ["python_print.md"]}
                assert review_store.get_daily_review("2026-10-14") == one
                candidates.append("python_dict_lookup.md")
                assert review_store.get_daily_review("2026-10-14") == one
                print("PASS: 单条、同日复用、当天新增不补抽")

                two = review_store.get_daily_review("2026-10-15")
                assert two["date"] == "2026-10-15"
                assert len(two["items"]) == 2
                assert set(two["items"]) == set(candidates)
                print("PASS: 次日生成新记录，不足三条全部选出")

                candidates.extend(["c_pointer_array.md", "synthetic_extra.md"])
                three = review_store.get_daily_review("2026-10-16")
                assert three["date"] == "2026-10-16"
                assert len(three["items"]) == 3
                assert len(set(three["items"])) == 3
                assert set(three["items"]).issubset(set(candidates))
                assert review_store.get_daily_review("2026-10-16") == three
                print("PASS: 四个模拟候选抽三条，组内不重复且同日顺序固定")

                child_code = (
                    "import json,sys; from pathlib import Path; "
                    "import review_store as r; "
                    "r.REVIEW_FILE=Path(sys.argv[1]); "
                    "r.list_familiar=lambda:json.loads(sys.argv[2]); "
                    "print(json.dumps(r.get_daily_review(sys.argv[3])))"
                )
                child = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        child_code,
                        str(review_store.REVIEW_FILE),
                        json.dumps(candidates),
                        "2026-10-16",
                    ],
                    cwd=Path(__file__).resolve().parent,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                assert json.loads(child.stdout) == three
                print("PASS: 新 Python 进程恢复同一天同一组")

                removed = three["items"][0]
                candidates.remove(removed)
                retained = [
                    item for item in three["items"] if item in candidates
                ]
                after_removal = review_store.get_daily_review("2026-10-16")
                assert after_removal == {
                    "date": "2026-10-16",
                    "items": retained,
                }
                assert len(after_removal["items"]) == 2
                candidates.clear()
                assert review_store.get_daily_review("2026-10-16")["items"] == []
                candidates.append("python_print.md")
                assert review_store.get_daily_review("2026-10-16")["items"] == []
                next_day = review_store.get_daily_review("2026-10-17")
                assert next_day == {
                    "date": "2026-10-17",
                    "items": ["python_print.md"],
                }
                print("PASS: 撤销立即移除、同日不补抽、下一日恢复候选抽取")
    finally:
        review_store.REVIEW_FILE = original_path

    current_bytes = original_path.read_bytes() if original_path.exists() else None
    assert current_bytes == original_bytes
    print("全部检查通过；真实复习文件未修改。")
    print("其中第四个候选为模拟条目，只验证抽取逻辑，不代表已收录资料。")


if __name__ == "__main__":
    main()
