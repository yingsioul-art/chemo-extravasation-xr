# -*- coding: utf-8 -*-
r"""網頁版 ③ 立即處理 360 VR（不用 MAKAR；A-Frame）— 素材建置腳本（可重跑）
來源（單一來源，本腳本只讀不改）：
  圖卡＋語音：D:\Zettelkasten\20_教學\Makar\10_XR教材_1002成果發表\04_MAKAR建置\MAKAR圖卡_③VR\{cards,cards2,audio}
  查詢站作法卡：…\04_MAKAR建置\MAKAR圖卡_查詢站\cards\A0*.png
  360 環景：…\01_工作坊課程\練習教材\素材\01_場景一.png、03_備物後到病人旁.png；
            02 備物空間用修正版 …\10_XR教材_1002成果發表\03_圖片音檔素材\360_02_備物空間場景_繁中修正.png
  題目正解：docs/assets/data/questions.json
產出：docs/vr/assets/{sky,cards,audio}/…、docs/vr/assets/scenes.json
圖卡檔名以「主檔名」比對（.png／.jpg 皆可），圖卡重製後重跑本腳本即可同步。
用法：PYTHONUTF8=1 python _build_vr_site.py
"""
import json, pathlib, shutil, hashlib
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent            # docs/vr
DOCS = HERE.parent
MK = pathlib.Path(r"D:\Zettelkasten\20_教學\Makar")
VR3 = MK / r"10_XR教材_1002成果發表\04_MAKAR建置\MAKAR圖卡_③VR"
LOOKC = MK / r"10_XR教材_1002成果發表\04_MAKAR建置\MAKAR圖卡_查詢站\cards"
NEW360 = MK / "10_XR教材_1002成果發表/03_圖片音檔素材/360新版"   # 9/29 ChatGPT 生圖版（prompt 在 03_圖片音檔素材/360環景prompt/）
SKYS = {
    "room": NEW360 / "sky_room.png",
    "store": NEW360 / "sky_store.png",
    "bed": NEW360 / "sky_bed.png",
}
A = HERE / "assets"
for d in ("sky", "cards", "audio"):
    (A / d).mkdir(parents=True, exist_ok=True)
Q = {q["id"]: q for q in json.load(open(DOCS / "assets/data/questions.json", encoding="utf-8"))["questions"]}
MAXW = 2560   # 圖卡最大寬（高解析重製版 3200 寬會縮到這裡，VR 內已足夠清楚）

# ---------- 環景 ----------
for k, src in SKYS.items():
    im = Image.open(src).convert("RGB")
    if im.width > 4096:
        im = im.resize((4096, 2048), Image.LANCZOS)
    im.save(A / "sky" / f"{k}.jpg", "JPEG", quality=80, optimize=True)

# ---------- 圖卡：依主檔名找來源 ----------
def find(stem):
    for d in (VR3 / "cards", VR3 / "cards2", LOOKC, HERE / "_extra", HERE / "_extra/hs", HERE / "_extra/lookup"):
        for ext in (".png", ".jpg", ".jpeg"):
            p = d / f"{stem}{ext}"
            if p.exists():
                return p
    raise FileNotFoundError(stem)

SIZES = {}
def card(stem):
    """複製並壓縮一張圖卡，回傳網站用檔名；同時記下原始比例。"""
    if stem in SIZES:
        return SIZES[stem]["f"]
    im = Image.open(find(stem))
    alpha = im.mode in ("RGBA", "LA") and im.getextrema()[-1][0] < 255
    im = im.convert("RGBA" if alpha else "RGB")
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    safe = stem.encode("ascii", "ignore").decode() or "c"
    # 中文檔名轉安全 ASCII 名（避免伺服器／URL 編碼問題）
    f = f"{safe}{hashlib.md5(stem.encode()).hexdigest()[:6]}" if safe != stem else stem
    f += ".png" if alpha else ".jpg"
    if alpha:
        im.save(A / "cards" / f, optimize=True)
    else:
        im.save(A / "cards" / f, "JPEG", quality=86, optimize=True)
    SIZES[stem] = {"f": f, "w": im.width, "h": im.height}
    return f

# ---------- 網頁版專用小卡（Playwright 渲染，風格同 MAKAR 卡） ----------
EXTRA = HERE / "_extra"; EXTRA.mkdir(exist_ok=True)
CSS = """*{box-sizing:border-box;margin:0}body{font-family:"Microsoft JhengHei","Noto Sans TC",sans-serif}
.c{width:1600px;height:900px;background:#f4f7fb;padding:60px 90px;position:relative;display:flex;flex-direction:column;justify-content:center}
.c .bar{position:absolute;left:0;top:0;bottom:0;width:30px;background:#123a6b}
h1{font-size:84px;line-height:1.3;color:#123a6b}p{font-size:54px;line-height:1.55;margin-top:24px;color:#1c2430}
.b{width:1000px;height:300px;border-radius:70px;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center}
.b h1{color:#fff;font-size:92px;line-height:1.1}.b p{color:#fff;font-size:46px;margin-top:8px;opacity:.92}"""
EXTRAS = {
    "W_LOOKUP": ('<div class="b" style="background:#7a3fb5"><h1>🔍 開啟敷療查詢站</h1><p>2D 網頁・57 個藥品</p></div>', (1000, 300)),
    "W_HANDSON": ('<div class="b" style="background:#d9541e"><h1>🖐️ 開啟 2D 動手版</h1><p>同一案例的平面互動</p></div>', (1000, 300)),
    "W_NOTICE": ('<div class="c"><div class="bar"></div><h1>頭顯模式看不到 2D 網頁</h1>'
                 '<p>查詢站是一般網頁，請按右下角「離開 VR」後再點一次。<br>下面先放三張作法卡給你看：冷敷、熱敷、DMSO。</p>'
                 '<p style="font-size:44px;color:#5b6675">點這張卡片 關閉</p></div>', (1600, 900)),
    "W_START": ('<div class="c"><div class="bar"></div><h1>③ 外滲當下怎麼做・360 VR</h1>'
                '<p>轉動手機或拖曳畫面看四周；點卡片作答。<br>每一站都有語音，按「🔇 停止語音」可以關掉。</p></div>', (1600, 900)),
}
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=True)
    for name, (h, (w, hh)) in EXTRAS.items():
        pg = br.new_page(viewport={"width": w, "height": hh}, device_scale_factor=1.28)
        pg.set_content(f"<style>{CSS}</style>{h}")
        pg.locator(".c,.b").first.screenshot(path=str(EXTRA / f"{name}.png"), omit_background=True)
        pg.close()
    br.close()

# ---------- 語音 ----------
for mp3 in (VR3 / "audio").glob("*.mp3"):
    dst = A / "audio" / mp3.name
    if not dst.exists() or dst.stat().st_size != mp3.stat().st_size:
        shutil.copy2(mp3, dst)

# ---------- 場景流程（依 MAKAR ③VR：開場→找線索→D1→D4 備物防護→D5 回抽→D2 不可壓→D3 標示筆→查詢站） ----------
def quiz(code, qcard, opts, ok, bad, nar, okau, badau, opt_prefix=""):
    """選擇題：qcard 題目卡、opts=[(key,stem)]、ok 正解卡、bad={key:卡}。"""
    return {"type": "quiz", "q": card(qcard), "nar": nar,
            "opts": [{"k": k, "img": card(s)} for k, s in opts],
            "ok": {"img": card(ok), "au": okau},
            "bad": {k: {"img": card(v), "au": badau[k]} for k, v in bad.items()}}

ans = lambda i: Q[i]["answer"]
assert all(ans(i) == "A" for i in (13, 14, 15, 17)), "正解不是 A，請檢查選項對應"
# 動手版搬進來的站（PPE 選物、選空針、按住回抽、解毒劑、敷療、九步驟總覽、案例二 DMSO、案例三 抬高；三案例皆必做）
from _build_vr_handson import build as build_handson
HS, CASE2, CASE3, PAINT, GOTO = build_handson(card)
HS["ppe"]["ok"]["img"] = card("D4OKh"); HS["ppe"]["ng"]["img"] = card("D4XBh")   # PPE 答對／答錯沿用 MAKAR 卡與語音（Q14）
HS["ppe"]["poster"] = {"img": card("PPE"), "au": "VPPE"}
HS["syr"]["poster"] = {"img": card("SYR"), "au": "VSYR"}
# 案例一流程＝動手版 FLOW1：d1→ppe→syr→asp→anti→press(d2)→pen(d3)→comp→總覽；VR 原本 D4／D5 選擇題由 ppe／syr＋asp 取代（同 Q14／Q15，保留一份）
steps = [
    {"id": "intro", "case": 1, "title": "情境", "sky": "room", "type": "info", "main": card("S1_情境開場"), "nar": "VN01",
     "next": card("BTN_下一步")},
    {"id": "clues", "case": 1, "title": "找線索", "sky": "room", "type": "clues", "main": card("T2"), "nar": "VN02",
     "hs": [{"img": card(f"H{i}"), "ex": card(f"GH{i}"), "au": f"VE{i}"} for i in range(1, 6)],
     "next": card("NEXT2")},
    dict(quiz("D1", "D1_題目", [(k, f"D1_選項{k}") for k in "ABC"], "D1_正解",
              {"B": "D1_後果B", "C": "D1_後果C"}, "VND1", "VD1OK", {"B": "VD1XB", "C": "VD1XC"}),
         id="d1", case=1, title="決定一：第一個動作", sky="room"),
    dict(HS["ppe"], case=1), dict(HS["syr"], case=1), dict(HS["asp"], case=1),
    dict(HS["antig"], case=1), dict(HS["anti"], case=1),
    dict(quiz("D2", "D2_題目", [(k, f"D2_選項{k}") for k in "AB"], "D2_正解",
              {"B": "D2_後果B"}, "VND2", "VD2OK", {"B": "VD2XB"}),
         id="d2", case=1, title="決定二：可以壓嗎", sky="bed"),
    dict(quiz("D3", "D3_題目", [(k, f"D3_選項{k}") for k in "ABC"], "D3_正解",
              {"B": "D3_後果B", "C": "D3_後果C"}, "VND3", "VD3OK", {"B": "VD3XB", "C": "VD3XC"}),
         id="d3", case=1, title="決定三：標示範圍", sky="bed", grid=True),
    dict(HS["compg"], case=1), dict(HS["comp"], case=1), dict(HS["q19"], case=1), dict(HS["sum1"], case=1),
] + CASE2 + CASE3 + [   # 9/29 使用者定：三個案例都必做 → 案例一→二→三 依序，最後才到查詢站
    {"id": "lookup", "case": 4, "title": "外滲處置查詢站", "sky": "store", "type": "end", "nar": "VN08",
     "lookup": card("W_LOOKUP"), "handson": card("W_HANDSON"), "notice": card("W_NOTICE"),
     "vrcards": [card(s) for s in ("A01_作法_冷敷作法", "A02_作法_熱敷作法", "A03_作法_DMSO作法")],
     "again": card("BTN_從頭再玩"), "home": card("BTN_回教材首頁"), "toC2": GOTO["toC2"], "toC3": GOTO["toC3"],
     # 9/29：補回 MAKAR 查詢站的環繞卡片（作法 3／原理 6／藥品 5）＋QR；點卡片播放／停止對應語音（_extra/lookup 來自 MAKAR 查詢站合成卡）
     "ring": [{"img": card(k), "au": ("V" + k[1:]) if k != "LQR" else None} for k in
              ("LA01", "LA02", "LA03", "LB00", "LB01", "LB02", "LB03", "LB04", "LB05", "LP1", "LP2", "LP3", "LP4", "LP5", "LQR")]},
]
common = {"mute": card("MUTE"), "listen": card("LISTENQ"), "start": card("W_START")}
json.dump({"ver": int(__import__("time").time()), "steps": steps, "common": common, "paint": PAINT, "sizes": {v["f"]: [v["w"], v["h"]] for v in SIZES.values()}},
          open(A / "scenes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 清掉已不用的舊圖卡
used = {v["f"] for v in SIZES.values()}
for f in (A / "cards").iterdir():
    if f.name not in used:
        f.unlink()
tot = sum(f.stat().st_size for f in A.rglob("*") if f.is_file())
print(f"{len(used)} cards, {len(list((A/'audio').glob('*.mp3')))} audio, total {tot/1e6:.1f} MB")
