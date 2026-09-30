# -*- coding: utf-8 -*-
"""頭顯內查詢站（VR 查詢面板）用圖卡：由 _build_vr_site.py 呼叫 build(card)。
- 每個藥品一張藥品卡（LK_*），文字一律取自 docs/lookup/index.html 的 DATA 原文，不自編
- 藥名按鈕（LKB_*）、索引頁標題卡（LKI_*）、面板操作鈕（LKN_*）
產出來源圖：docs/vr/_extra/lookupvr/*.png（再由 card() 壓縮進 assets/cards/）
"""
import json, re, pathlib, hashlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
LOOKUP = HERE.parent / "lookup" / "index.html"
OUT = HERE / "_extra" / "lookupvr"
PER_PAGE = 15   # 索引每頁藥名數（3 欄 × 5 列）

CSS = """*{box-sizing:border-box;margin:0}body{margin:0;font-family:"Microsoft JhengHei","Noto Sans TC",sans-serif;color:#1c2430}
:root{--cold:#1f6fd0;--warm:#d9541e;--dmso:#7a3fb5;--ves:#c81e3a;--irr:#d98a00;--none:#2e8b57;--na:#7d8794}
.c{width:1600px;height:900px;background:#f4f7fb;padding:48px 70px 40px 90px;position:relative;display:flex;flex-direction:column;overflow:hidden}
.c .bar{position:absolute;left:0;top:0;bottom:0;width:30px;background:#123a6b}
.kick{font-size:40px;color:#5b6675;font-weight:700}
h1{font-size:92px;line-height:1.1;color:#123a6b;margin-top:6px}
.b{font-size:46px;color:#5b6675;margin-top:6px}
.tags{margin-top:22px;display:flex;flex-wrap:wrap;gap:14px}
.tag{display:inline-block;font-size:44px;font-weight:800;padding:8px 22px;border-radius:14px;color:#fff}
.V{background:var(--ves)}.Ip,.I{background:var(--irr)}.Iq{background:var(--irr);opacity:.85}.N{background:var(--none)}.NA{background:var(--na)}
.tC{background:var(--cold)}.tW{background:var(--warm)}.tCW,.tT{background:linear-gradient(90deg,var(--cold),var(--warm))}.tD{background:var(--dmso)}.tNI,.tNA{background:var(--na)}
.k{font-size:40px;font-weight:800;color:#123a6b;margin-top:24px}
.txd{font-size:50px;line-height:1.4;margin-top:6px}
.note{font-size:38px;line-height:1.4;color:#5b6675;margin-top:16px}
.ref{position:absolute;right:40px;bottom:22px;font-size:26px;color:#8a95a5}
.btn{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;text-align:center;border-radius:40px;padding:0 24px;white-space:nowrap}
.nm{width:700px;height:150px;background:#fff;border:5px solid #123a6b;color:#123a6b;border-radius:30px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:800}
.nm b{font-size:52px;line-height:1.1}.nm span{font-size:28px;color:#5b6675;font-weight:600;margin-top:4px}
"""
FIT = """()=>{const r=document.querySelector('[data-root]');const els=[...r.querySelectorAll('*')];const base=els.map(e=>parseFloat(getComputedStyle(e).fontSize));
 let f=1;for(let i=0;i<14&&(r.scrollHeight>r.clientHeight+1||r.scrollWidth>r.clientWidth+1);i++){f*=0.93;els.forEach((e,k)=>e.style.fontSize=(base[k]*f)+'px');}return f;}"""
e = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
TAG = {"V": "V", "I+": "Ip", "I": "I", "I?": "Iq", "N": "N", "NA": "NA"}


def safe(g):
    s = re.sub(r"[^A-Za-z0-9]+", "_", g).strip("_")
    return s or hashlib.md5(g.encode()).hexdigest()[:8]


def build(card):
    src = LOOKUP.read_text(encoding="utf-8")
    DATA = json.loads(re.search(r"const DATA=(\[.*?\]);", src, re.S).group(1))
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []   # (名稱, html, w, h)
    for d in DATA:
        s = safe(d["g"])
        note = f'<div class="note">備註：{e(d["note"])}</div>' if d.get("note") else ""
        html = (f'<div class="c" data-root><div class="bar"></div><div class="kick">外滲處置查詢（院內 2023.5 版）</div>'
                f'<h1>{e(d["g"])}</h1><div class="b">商品名：{e(d["b"])}</div>'
                f'<div class="tags"><span class="tag {TAG.get(d["cc"], "NA")}">{e(d["cls"])}</span><span class="tag t{e(d["tc"])}">{e(d["tx"])}</span></div>'
                f'<div class="k">局部處置</div><div class="txd">{e(d["txd"] or "—")}</div>{note}'
                f'<div class="ref">文獻：{e(d["ref"])}</div></div>')
        jobs.append((f"LK_{s}", html, 1600, 900))
        jobs.append((f"LKB_{s}", f'<div class="nm" data-root><b>{e(d["g"])}</b><span>{e(d["tx"])}</span></div>', 700, 150))
    pages = [DATA[i:i + PER_PAGE] for i in range(0, len(DATA), PER_PAGE)]
    for i, pg in enumerate(pages):
        rng = f'{pg[0]["g"][0].upper()}–{pg[-1]["g"][0].upper()}'
        jobs.append((f"LKI_{i + 1}", f'<div class="c" data-root style="height:300px;justify-content:center"><div class="bar"></div>'
                                     f'<h1 style="font-size:84px">📖 藥名索引 {e(rng)}（{i + 1}／{len(pages)}）</h1>'
                                     f'<div class="b">點藥名看外滲處置</div></div>', 1600, 300))
    NAV = {"LKN_prev": ("◀ 上一張", "#5b6675"), "LKN_next": ("下一張 ▶", "#5b6675"), "LKN_index": ("📖 藥名索引", "#123a6b"),
           "LKN_guide": ("🧊🔥 作法與原理", "#7a3fb5"), "LKN_close": ("✕ 關閉", "#c81e3a")}
    for k, (t, c) in NAV.items():
        jobs.append((k, f'<div class="btn" data-root style="width:700px;height:200px;background:{c};font-size:80px">{e(t)}</div>', 700, 200))
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(device_scale_factor=1.28)
        for name, html, w, h in jobs:
            out = OUT / f"{name}.png"
            if out.exists() and out.with_suffix(".h").exists() and out.with_suffix(".h").read_text(encoding="utf-8") == hashlib.md5(html.encode()).hexdigest():
                continue
            pg.set_viewport_size({"width": w, "height": h})
            pg.set_content(f"<style>{CSS}</style>{html}")
            pg.evaluate(FIT)
            pg.locator("[data-root]").screenshot(path=str(out))
            out.with_suffix(".h").write_text(hashlib.md5(html.encode()).hexdigest(), encoding="utf-8")
        b.close()
    drugs = [{"g": d["g"], "card": card(f"LK_{safe(d['g'])}", q=78), "btn": card(f"LKB_{safe(d['g'])}", q=82)} for d in DATA]
    return {
        "drugs": drugs,
        "pages": [{"head": card(f"LKI_{i + 1}", q=82), "idx": list(range(i * PER_PAGE, i * PER_PAGE + len(pg)))} for i, pg in enumerate(pages)],
        "nav": {k.split("_")[1]: card(k, q=86) for k in ("LKN_prev", "LKN_next", "LKN_index", "LKN_guide", "LKN_close")},
    }
