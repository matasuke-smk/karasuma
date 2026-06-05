#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京都市営地下鉄 烏丸線の公式CSV(source/) から timetable.json を生成する。

行き = 国際会館 発 → 竹田 着   (下り「竹田/新田辺・近鉄奈良方面」CSV)
帰り = 竹田 発     → 国際会館 着 (上り「国際会館方面」CSV)

CSV構造: 0行目=タイトル, 1-2行目=注記, 3行目=ヘッダー(駅名), 4行目以降=1列車1行。
ヘッダー: [行先（終着）, 始発, 駅, 駅, ...]。終着駅は着時刻・他は発時刻。
"""
import csv
import io
import json
from pathlib import Path

SRC = Path(__file__).resolve().parent / "source"
OUT = Path(__file__).resolve().parent / "timetable.json"

FILES = {
    "weekday": {
        "down": "烏丸線　平日　下り（竹田／新田辺・近鉄奈良方面）.csv",
        "up":   "烏丸線　平日　上り（国際会館方面）.csv",
    },
    "holiday": {
        "down": "烏丸線　土曜・休日　下り（竹田／新田辺・近鉄奈良方面）.csv",
        "up":   "烏丸線　土曜・休日　上り（国際会館方面）.csv",
    },
}


def load(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return list(csv.reader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"decode failed: {path}")


def extract(rows, dep_station, arr_station):
    """ヘッダーから発駅・着駅の列を特定し、[行先, 発, 着] のリストを返す。"""
    header = rows[3]
    di = header.index(dep_station)
    ai = header.index(arr_station)
    trips = []
    for r in rows[4:]:
        if len(r) <= max(di, ai):
            continue
        dep = r[di].strip()
        arr = r[ai].strip()
        if not dep or not arr:
            continue            # その駅を通らない列車(始発が途中駅 等)は除外
        dest = (r[0] or "").strip()
        trips.append([dest, dep, arr])
    return trips


def main():
    data = {
        "line": "烏丸線",
        "revision": "2025-02-22",
        "source": "出典: 京都市オープンデータ「京都市営地下鉄時刻表（令和7年2月22日改正）」CC BY 4.0"
                  "／近鉄直通ダイヤは令和8年3月14日改正",
        "note": "土曜・休日は同一ダイヤ。祝日は休日ダイヤ。着時刻は終着駅は実着、"
                "途中通過の場合は発時刻(目安)。0:xx は翌日早朝。",
    }
    for day, fs in FILES.items():
        down = load(SRC / fs["down"])
        up = load(SRC / fs["up"])
        data[day] = {
            "go":   {"from": "国際会館", "to": "竹田",
                     "trips": extract(down, "国際会館", "竹田")},
            "back": {"from": "竹田", "to": "国際会館",
                     "trips": extract(up, "竹田", "国際会館")},
        }
        print(f"{day}: 行き {len(data[day]['go']['trips'])}本 / "
              f"帰り {len(data[day]['back']['trips'])}本")

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
