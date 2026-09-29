# -*- coding: utf-8 -*-
"""紀錄與追蹤 g01–g04 旁白字幕：用與 _gen_audio.py 相同的 voice/rate 串流 edge-tts，只取句子邊界時間（不覆蓋 mp3），輸出 g0N.vtt。
文字來源＝_卡片旁白稿_草稿.md（與目前 g01–g04.mp3 相同的 draft 稿）。用法：PYTHONUTF8=1 python _gen_subs_g.py"""
import asyncio, re, pathlib, edge_tts
HERE = pathlib.Path(__file__).resolve().parent
VOICE, RATE = "zh-TW-YunJheNeural", "-5%"
md = (HERE / "_卡片旁白稿_草稿.md").read_text(encoding="utf-8")
cards = dict(re.findall(r"^## (g0\d)｜[^\n]*\n(.+?)(?=\n\n|\n## |\Z)", md, re.M | re.S))

def ts(t):  # 100ns 單位 → VTT 時間
    ms = int(t / 10000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"

def chunks(text, n=22):  # 句子太長再依逗號切，字幕每行不超過約 n 字
    out = []
    for sent in re.findall(r"[^。！？]+[。！？]?", text):
        buf = ""
        for part in re.findall(r"[^，、；：]+[，、；：]?", sent):
            if buf and len(buf) + len(part) > n: out.append(buf); buf = ""
            buf += part
        if buf: out.append(buf)
    return [c.strip() for c in out if c.strip()]

async def one(gid, text):
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    words = []
    async for ch in comm.stream():
        if ch["type"] == "WordBoundary": words.append((ch["offset"], ch["offset"] + ch["duration"], ch["text"]))
    # 把逐詞時間對回每個字幕片段（依字元累計）
    segs = chunks(text); plain = lambda s: re.sub(r"[，。、；：！？「」（）\s]", "", s)
    pos = 0; wi = 0; cues = []
    for seg in segs:
        need = len(plain(seg)); start = None; end = None; got = 0
        while wi < len(words) and got < need:
            b, e, w = words[wi]; start = b if start is None else start; end = e; got += len(plain(w)); wi += 1
        if start is not None: cues.append((start, end, seg))
    for i in range(len(cues) - 1):  # 字幕延續到下一句開始
        cues[i] = (cues[i][0], cues[i + 1][0], cues[i][2])
    vtt = "WEBVTT\n\n" + "\n".join(f"{ts(b)} --> {ts(e)}\n{t}\n" for b, e, t in cues)
    (HERE / f"{gid}.vtt").write_text(vtt, encoding="utf-8")
    print(gid, len(cues), "cues, end", ts(cues[-1][1]))

async def main():
    for gid, text in sorted(cards.items()): await one(gid, text.strip())
asyncio.run(main())
