#!/usr/bin/env python3
"""Scan local knowledge_all.csv for gambling keywords. Network: none."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "data" / "knowledge_all.csv"
GAMBLING = [
    "彩票", "竞彩", "足彩", "体彩", "福彩", "博彩", "赌博", "赌球",
    "投注", "下注", "赔率", "盘口", "让球", "大小球", "亚盘", "欧赔",
    "水位", "串关", "稳赚", "必中", "庄家",
]


def main() -> int:
    if not TARGET.exists():
        print(f"SKIP: {TARGET.relative_to(ROOT)} not found; add local data before scanning")
        return 0

    hits: list[str] = []
    for row in csv.DictReader(TARGET.open(encoding="utf-8")):
        blob = "".join(row.get(f, "") for f in ("question", "answer_short", "answer_detail", "keywords"))
        for w in GAMBLING:
            if w in blob:
                hits.append(f"{row['id']}: {w}")
    if hits:
        print(f"FAIL: {len(hits)} hit(s)")
        for h in hits[:20]:
            print(h)
        return 1
    print("PASS: zero gambling keyword hits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
