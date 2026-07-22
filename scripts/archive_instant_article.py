"""Archive a delisted (下巿) instants (刮刮樂) article and remove it from the compare table.

已下巿的期別搬到存檔區，不再出現在「最新刮刮樂」與比較表格中：

- docs/_articles/all-instants/{期別}.md
    -> docs/_articles/all-instants-archive/{期別}.md
       (permalink: /all-instants/{期別}/ -> /all-instants-archive/{期別}/
        category: all-instants -> all-instants-archive)
- docs/_data/instants_compare.yml：移除該期別的區塊
- raw-data/archived-instants.json：加入該期別 id（排序、去重）

購買紀錄（raw-data/all-instants.csv）、raw-data/instant-games.json、
raw-data/instant-prize-structures/{期別}.json 不受影響。

Usage:
    python scripts/archive_instant_article.py 5123 5130
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "docs" / "_articles" / "all-instants"
ARCHIVE_DIR = ROOT / "docs" / "_articles" / "all-instants-archive"
COMPARE_YML = ROOT / "docs" / "_data" / "instants_compare.yml"
ARCHIVED_LIST_JSON = ROOT / "raw-data" / "archived-instants.json"

PERMALINK_RE = re.compile(r"^permalink: /all-instants/(\d+)/$", re.MULTILINE)
CATEGORY_RE = re.compile(r"^category: all-instants$", re.MULTILINE)


# ---------------------------------------------------------------------------
# File IO（一律 UTF-8 無 BOM；換行沿用 repo 工作區慣例 CRLF）
# ---------------------------------------------------------------------------

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text.replace("\r\n", "\n").replace("\n", "\r\n"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def load_archived_ids() -> list:
    if not ARCHIVED_LIST_JSON.exists():
        return []
    return json.loads(ARCHIVED_LIST_JSON.read_text(encoding="utf-8"))


def save_archived_ids(ids: list) -> None:
    ordered = sorted(set(ids), key=int)
    write_text(ARCHIVED_LIST_JSON, json.dumps(ordered, ensure_ascii=False, indent=4) + "\n")


def validate_article(issue: str) -> Path | None:
    """檢查文章是否存在且格式符合預期，不做任何寫入。"""
    src = ARTICLES_DIR / f"{issue}.md"
    if not src.exists():
        print(f"[skip] 找不到文章：{src}")
        return None

    text = read_text(src)
    if not PERMALINK_RE.search(text) or not CATEGORY_RE.search(text):
        print(f"[warn] {src} 的 permalink/category 格式不是預期的樣子，請確認後手動處理")
        return None

    return src


def move_article(issue: str, src: Path) -> None:
    text = read_text(src)
    text = PERMALINK_RE.sub(r"permalink: /all-instants-archive/\1/", text, count=1)
    text = CATEGORY_RE.sub("category: all-instants-archive", text, count=1)

    dest = ARCHIVE_DIR / f"{issue}.md"
    write_text(dest, text)
    src.unlink()
    print(f"[ok] 文章搬移：{src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


def remove_from_compare_yml(issue: str) -> bool:
    text = read_text(COMPARE_YML)
    if not text.endswith("\n"):
        text += "\n"
    block_re = re.compile(rf"(?m)^  - id: {issue}\n(?:    .*\n)*")
    if not block_re.search(text):
        print(f"[skip] 比較表中沒有期別 {issue} 的區塊")
        return False
    text = block_re.sub("", text, count=1)
    write_text(COMPARE_YML, text.rstrip("\n") + "\n")
    print(f"[ok] 已從 {COMPARE_YML.relative_to(ROOT)} 移除期別 {issue}")
    return True


def archive_issue(issue: str, archived_ids: list) -> None:
    if issue in archived_ids:
        print(f"[skip] 期別 {issue} 已在存檔清單中")
        return

    # 先驗證前置條件，通過才進行任何寫入，避免文章沒搬成功卻已經記錄成
    # 存檔狀態（compare.yml 移除了、archived-instants.json 也加了 id），
    # 導致之後 build_instant_all.py 產生指向不存在頁面的連結。
    src = validate_article(issue)
    if src is None:
        print(f"[skip] 期別 {issue} 未通過前置檢查，不做任何變更")
        return

    move_article(issue, src)
    remove_from_compare_yml(issue)
    archived_ids.append(issue)


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive delisted instants articles.")
    parser.add_argument("issues", nargs="+", help="期別，例如 5123 5130")
    args = parser.parse_args()

    archived_ids = load_archived_ids()
    for issue in args.issues:
        archive_issue(issue, archived_ids)

    save_archived_ids(archived_ids)
    print(f"[ok] 已更新 {ARCHIVED_LIST_JSON.relative_to(ROOT)}：{sorted(set(archived_ids), key=int)}")


if __name__ == "__main__":
    sys.exit(main())
