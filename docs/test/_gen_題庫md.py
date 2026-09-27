# -*- coding: utf-8 -*-
"""
從 docs/assets/data/questions.json 產出 docs/test/_題庫_v1.md（給使用者對照用，唯讀產物）。
題目文字單一來源＝規格檔 → questions.json；本檔不手抄。
用法：PYTHONUTF8=1 python docs/test/_gen_題庫md.py
"""
import json, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "assets" / "data" / "questions.json"
OUT = HERE / "_題庫_v1.md"

GROUPS = [  # 成績頁四組（依 block 字母歸組，與 index.html 一致）
    ("自學題", "ABCD", "Q1–Q12"),
    ("③ 初步處理", "E", "Q13–Q20"),
    ("④ 後續處置", "F", "Q21–Q23"),
    ("⑤ 紀錄與追蹤", "G", "Q24–Q27"),
]

def group_of(block):
    for name, letters, rng in GROUPS:
        if block in letters:
            return name
    return "？"

def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    qs = data["questions"]
    lines = []
    lines.append("# 前後測題庫 v1（自 questions.json 產出，對照用）")
    lines.append("")
    lines.append(f"> 來源：`docs/assets/data/questions.json`（由 `tools/build_questions.py` 解析規格檔 `{data.get('source','')}`）")
    lines.append(f"> 產出時間：{datetime.datetime.now():%Y-%m-%d %H:%M}｜共 {len(qs)} 題｜**本檔為唯讀產物，校字請改規格檔再重跑 build_questions.py 與本腳本**")
    lines.append("> 前後測頁面：題目順序與選項順序皆隨機；作答時不顯示對錯；成績頁顯示總分與四組分數。")
    lines.append("")
    # 對照總表
    lines.append("## 對照總表")
    lines.append("")
    lines.append("| 題號 | 區塊 | 成績組 | 表單題號 | 正解 | 選項數 | 題幹 |")
    lines.append("|---|---|---|---|---|---|---|")
    for q in qs:
        stem = q["stem"].replace("|", "｜")
        lines.append(f"| Q{q['id']} | {q['block']} {q['block_name']} | {group_of(q['block'])} | {q['form_item']} | {q['answer']} | {len(q['options'])} | {stem} |")
    lines.append("")
    # 各組題數
    lines.append("## 成績頁四組")
    lines.append("")
    lines.append("| 組 | 區塊 | 題號 | 題數 |")
    lines.append("|---|---|---|---|")
    for name, letters, rng in GROUPS:
        n = sum(1 for q in qs if q["block"] in letters)
        lines.append(f"| {name} | {'、'.join(letters)} | {rng} | {n} |")
    lines.append("")
    # 逐題全文
    lines.append("## 逐題全文")
    lines.append("")
    cur_block = None
    for q in qs:
        if q["block"] != cur_block:
            cur_block = q["block"]
            lines.append(f"### 區塊 {cur_block}｜{q['block_name']}")
            lines.append("")
        lines.append(f"**Q{q['id']}**（表單 {q['form_item']}；正解 {q['answer']}）{q['stem']}")
        if q.get("note"):
            lines.append(f"> 備註：{q['note']}")
        for o in q["options"]:
            mark = " ✓" if o["key"] == q["answer"] else ""
            lines.append(f"- {o['key']} {o['text']}{mark}")
        lines.append(f"- 講解-對：{q['explain_ok']}")
        lines.append(f"- 講解-錯：{q['explain_ng']}")
        lines.append(f"- 圖：{q['img']}")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"→ {OUT}（{len(qs)} 題）")

if __name__ == "__main__":
    main()
