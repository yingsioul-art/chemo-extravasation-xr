# -*- coding: utf-8 -*-
"""S4 音檔產生腳本：讀 docs/assets/data/questions.json 的 explain_ok／explain_ng（不從 md 手抄），
用 edge-tts（zh-TW-YunJheNeural，rate -5%）產 mp3 到本資料夾。
- 產出命名：q01_ok.mp3／q01_ng.mp3；⑤ 講解卡 g01.mp3…（需 questions.json 有 "cards" 清單，見下）
- _manifest.json 記每檔 text_hash；重跑只重產 hash 變動或檔案不存在的檔（--force 全重產）
- 產完重寫 _時長表.md
用法：
  PYTHONUTF8=1 python docs/assets/audio/_gen_audio.py --only q01_ok   # 試聽 1 檔
  PYTHONUTF8=1 python docs/assets/audio/_gen_audio.py                 # 全跑（增量）
  PYTHONUTF8=1 python docs/assets/audio/_gen_audio.py --force         # 全重產
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys
import time

import edge_tts
from mutagen.mp3 import MP3

HERE = os.path.dirname(os.path.abspath(__file__))
QJSON = os.path.normpath(os.path.join(HERE, "..", "data", "questions.json"))
MANIFEST = os.path.join(HERE, "_manifest.json")
DUR_MD = os.path.join(HERE, "_時長表.md")
VOICE = "zh-TW-YunJheNeural"
RATE = "-5%"
LEARN_IDS = list(range(1, 13)) + [24, 25, 26, 27]   # A–D 12 題＋⑤ 自我檢核 Q24–Q27


def h8(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def collect(data):
    """回傳 [(檔名, 文字, hash, 內容摘要)]。"""
    items = []
    qs = {q["id"]: q for q in data["questions"]}
    for i in LEARN_IDS:
        q = qs[i]
        for kind in ("ok", "ng"):
            text = q[f"explain_{kind}"]
            th = (q.get("text_hash") or {}).get(kind) or h8(text)
            items.append((f"q{i:02d}_{kind}.mp3", text, th, f"Q{i} 講解-{'對' if kind == 'ok' else '錯'}"))
    # ⑤ 四張講解卡旁白：單一來源仍是 questions.json，需 build_questions.py 產出 "cards": [{"id":"g01","text":...}]
    for c in data.get("cards", []):
        items.append((f"{c['id']}.mp3", c["text"], c.get("text_hash") or h8(c["text"]), f"⑤ 講解卡 {c['id']}"))
    return items


def read_draft_cards():
    """讀 _卡片旁白稿_草稿.md：`## g01｜標題` 之後到下一個 `## ` 前的段落＝旁白；hash 前綴 draft_ 以便正式版出來必重產。"""
    import re
    md = open(os.path.join(HERE, "_卡片旁白稿_草稿.md"), encoding="utf-8").read()
    cards = []
    for m in re.finditer(r"^## (g\d\d)｜([^\n]+)\n(.*?)(?=^## |^---|\Z)", md, re.S | re.M):
        text = " ".join(l.strip() for l in m.group(3).splitlines() if l.strip())
        cards.append({"id": m.group(1), "title": m.group(2).strip(), "text": text, "text_hash": "draft_" + h8(text)})
    print(f"（草稿模式）讀到 {len(cards)} 張卡片旁白")
    return cards


async def synth(text, path):
    tts = edge_tts.Communicate(text, VOICE, rate=RATE)
    await tts.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="只產這一檔（不含 .mp3），例如 q01_ok")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--draft", action="store_true", help="questions.json 無 cards 時，改讀 _卡片旁白稿_草稿.md 產 g01–g04（試聽用）")
    a = ap.parse_args()

    data = json.load(open(QJSON, encoding="utf-8"))
    if a.draft and not data.get("cards"):
        data["cards"] = read_draft_cards()
    items = collect(data)
    if not data.get("cards"):
        print("⚠ questions.json 無 cards 清單 → ⑤ 講解卡 g01–g04 音檔未產（等旁白稿進單一來源）")
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}

    todo = []
    for fname, text, th, label in items:
        if a.only and fname != a.only + ".mp3":
            continue
        path = os.path.join(HERE, fname)
        if not a.force and os.path.exists(path) and manifest.get(fname, {}).get("hash") == th:
            continue
        todo.append((fname, text, th, label))
    print(f"待產 {len(todo)} 檔／共 {len(items)} 檔")

    for fname, text, th, label in todo:
        path = os.path.join(HERE, fname)
        for attempt in range(3):
            try:
                asyncio.run(synth(text, path))
                break
            except Exception as e:  # 網路抖動重試
                print(f"  retry {attempt+1} {fname}: {e}")
                time.sleep(3)
        else:
            print(f"🔴 失敗 {fname}")
            continue
        sec = round(MP3(path).info.length, 1)
        manifest[fname] = {"hash": th, "chars": len(text), "sec": sec, "label": label,
                           "voice": VOICE, "rate": RATE, "generated": time.strftime("%Y-%m-%d %H:%M")}
        print(f"  ✓ {fname:12s} {sec:5.1f}s  {label}")

    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 時長表：依 manifest 全表重寫（本檔只有 S4 寫）
    rows = []
    total = 0.0
    for fname, text, th, label in items:
        m = manifest.get(fname)
        if m and os.path.exists(os.path.join(HERE, fname)):
            rows.append(f"| {fname} | {m['sec']} | {m['chars']} | {label} | {m['hash']} |")
            total += m["sec"]
        else:
            rows.append(f"| {fname} | — | {len(text)} | {label}（未產） | {th} |")
    with open(DUR_MD, "w", encoding="utf-8") as f:
        f.write("# 音檔時長表（S4 維護；由 _gen_audio.py 自動重寫）\n\n")
        f.write(f"- 聲音：{VOICE}，rate {RATE}；文字來源＝`docs/assets/data/questions.json` explain_ok／explain_ng\n")
        f.write(f"- 已產 {sum(1 for r in rows if '（未產）' not in r)} 檔，合計 {total/60:.1f} 分鐘；更新 {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("| 檔名 | 秒 | 字數 | 內容 | text_hash |\n|---|---|---|---|---|\n")
        f.write("\n".join(rows) + "\n")
    print("時長表已更新", DUR_MD)


if __name__ == "__main__":
    main()
