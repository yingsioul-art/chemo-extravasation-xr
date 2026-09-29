# -*- coding: utf-8 -*-
r"""網頁 VR：把 2D 動手版（docs/handson/）有、VR 沒有的設計搬進來（2026-09-29）
由 _build_vr_site.py 呼叫：build(card) → dict(各站定義)。
單一來源：
  - 題目／講解：docs/assets/data/questions.json（Q13–Q20）
  - 用物、後果、九步驟、DMSO 三題、抬高四情境、塗抹判定常數：從 docs/handson/index.html 讀出（Playwright 取頁內常數＋regex 取內嵌字串）
  - 圖：docs/assets/img/h_*.png
產出：docs/vr/_extra/hs/*.png（新圖卡）、docs/vr/assets/audio/HS_*.mp3（新語音；文字沒變就不重生，快取 _extra/hs/_tts.json）
"""
import json, re, base64, io, asyncio, pathlib, hashlib
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
DOCS = HERE.parent
IMG = DOCS / "assets/img"
OUT = HERE / "_extra/hs"; OUT.mkdir(parents=True, exist_ok=True)
AUD = HERE / "assets/audio"
TTS_CACHE = OUT / "_tts.json"
VOICE, RATE = "zh-TW-YunJheNeural", "-5%"
Q = {q["id"]: q for q in json.load(open(DOCS / "assets/data/questions.json", encoding="utf-8"))["questions"]}


# ---------- 讀動手版常數（單一來源） ----------
def read_handson():
    src = (DOCS / "handson/index.html").read_text(encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True); pg = b.new_page()
        pg.goto((DOCS / "handson/index.html").as_uri()); pg.wait_for_timeout(800)
        H = pg.evaluate("""()=>({PPE,SYR,PENS,COMP,CQ,STEPS9,DM,EL,LOOKUP_DOXO,EL_SRC,SCENES,
            DMSO_SCALE,PAINT_PASS_COVER,PAINT_MAX_OUTSIDE,PAINT_SPOT})""")
        b.close()

    def lit(pat):
        m = re.search(pat, src)
        if not m: raise RuntimeError("handson 找不到：" + pat)
        return m.group(1)
    H["caseNote"] = lit(r"const caseNote = '([^']+)'")
    H["antiNote"] = lit(r"expBox\('info', '本案結論', '([^']+)'")
    H["aspFull"] = int(lit(r"const FULL = (\d+);"))
    H["aspML"] = float(lit(r"const MAXML = ([\d.]+);"))
    H["aspEarly"] = lit(r"toast\('(太早放開了[^']*)'")
    H["paintOK"] = lit(r"pass\('(塗對了[^']*)'")
    H["paintSmall"] = (lit(r"title = '(塗太小了)'"), lit(r"title = '塗太小了'; text = '([^']+)'"))
    H["paintBig"] = (lit(r"title = '(塗太大了)'"), lit(r"title = '塗太大了'; text = '([^']+)'"))
    H["paintOff"] = (lit(r"title = '(位置偏了)'"), lit(r"title = '位置偏了'; text = '([^']+)'"))
    H["paintShow"] = lit(r"pass\('(正確範圍[^']*)'")
    H["paintSrc"] = lit(r"const SRC = '([^']+)'")
    keyp = lit(r"const KEYP = `<ul class=\"keyp\">(.+?)</ul>`")
    H["keyp"] = [re.sub(r"<[^>]+>", "", li) for li in re.findall(r"<li>(.+?)</li>", keyp)]
    H["antiTitleNg"] = lit(r"showCQ\(\{title:'(不是一律拔[^']*)'")
    H["compDmsoNg"] = lit(r"showCQ\(\{title:'(DMSO 不是 Cisplatin[^']*)'")
    H["compWarn"] = lit(r"expBox\('warn', '(熱敷：[^']+)'")
    H["compOk"] = lit(r"expBox\('ok', '(本案走冷敷)'")
    H["aspTitle"] = lit(r"expBox\('ok', `(完成：回抽到抽不出為止)")
    H["sc1"] = re.sub(r"<[^>]+>", "", lit(r"RENDER.scene1[\s\S]+?<p style=\"margin-top:12px\">(.+?)</p>"))
    H["sc2"] = re.sub(r"<[^>]+>", "", lit(r"RENDER.scene2[\s\S]+?<p style=\"margin-top:12px\">(.+?)</p>"))
    H["sc3"] = re.sub(r"<[^>]+>", "", lit(r"RENDER.scene3[\s\S]+?</div>\s*<p>(.+?)</p>"))
    H["sc3key"] = re.sub(r"<[^>]+>", "", lit(r"記住兩件事</div><div>(.+?)</div>"))
    H["el_one"] = re.sub(r"<[^>]+>", "", lit(r"一句話帶走</div><div>(.+?)</div>"))
    return H


# ---------- 圖卡樣式（同 MAKAR ③VR 卡） ----------
CSS = """*{box-sizing:border-box;margin:0}body{margin:0;font-family:"Microsoft JhengHei","Noto Sans TC",sans-serif;color:#1c2430}
.c{width:1600px;height:900px;background:#f4f7fb;padding:56px 80px 56px 90px;position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:center}
.c .bar{position:absolute;left:0;top:0;bottom:0;width:30px;background:var(--a,#123a6b)}
.kick{font-size:50px;color:#5b6675;margin-bottom:16px;font-weight:700}
h1{font-size:88px;line-height:1.28;color:var(--h,#123a6b)}
p,li{font-size:62px;line-height:1.5}p+p{margin-top:18px}
ul{margin:14px 0 0 1.1em;padding:0}
.src{font-size:36px;color:#8a95a5;margin-top:18px}
.ok{--a:#1f8a4c;--h:#1f8a4c}.ng{--a:#c81e3a;--h:#c81e3a}.warn{--a:#b7791f;--h:#9a6200}.info{--a:#123a6b}.dm{--a:#7a3fb5;--h:#7a3fb5}
.hint{position:absolute;left:90px;bottom:40px;padding:12px 32px;border-radius:40px;color:#fff;font-size:46px;font-weight:800;background:var(--a,#123a6b)}
.split{display:flex;gap:40px;align-items:center}.split img{width:560px;border-radius:24px;flex:none;background:#fff}
.opt{display:flex;gap:34px;align-items:center}.key{flex:none;width:140px;height:140px;border-radius:34px;background:#123a6b;color:#fff;font-size:96px;font-weight:800;display:flex;align-items:center;justify-content:center}
.opt p{font-size:72px;line-height:1.3}
.io{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;text-align:center}
.io img{height:360px;max-width:740px;object-fit:contain;border-radius:18px;background:#fff}
.io b{font-size:96px;line-height:1.15}.io span{font-size:62px;line-height:1.2;color:#5b6675}
.btn{display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;text-align:center;padding:0 30px;white-space:nowrap}
.g9big div{font-size:60px!important}.g9big img{width:300px!important;height:210px!important}
.big .kick{font-size:56px}.big h1{font-size:100px}.big p{font-size:76px!important;line-height:1.45}
.grid9{display:grid;grid-template-columns:repeat(3,1fr);gap:12px 16px;margin-top:6px}
.grid9 div{display:flex;flex-direction:column;gap:8px;align-items:center;text-align:center;font-size:48px;line-height:1.3;background:#fff;border-radius:16px;padding:8px}
.grid9 img{width:240px;height:170px;object-fit:contain;flex:none}.grid9 i{font-style:normal;font-weight:800;color:#123a6b;font-size:44px}
"""
FIT_JS = """()=>{const r=document.querySelector('[data-root]');if(!r)return 1;
  const over=()=>{if(r.scrollHeight>r.clientHeight+1||r.scrollWidth>r.clientWidth+1)return true;
    const R=r.getBoundingClientRect(),h=r.querySelector(':scope>.hint'),lim=h?h.getBoundingClientRect().top-8:R.bottom+1;
    for(const e of r.querySelectorAll('h1,p,li,.src,.kick,img,b,span,.grid9')){if(e.closest('.hint'))continue;const b=e.getBoundingClientRect();
      if(b.width&&(b.bottom>lim||b.right>R.right+1))return true;}return false;};
  const els=[...r.querySelectorAll('*')].filter(e=>!e.closest('.hint'));const base=els.map(e=>parseFloat(getComputedStyle(e).fontSize));
  let f=1;for(let i=0;i<16&&over();i++){f*=0.93;els.forEach((e,k)=>e.style.fontSize=(base[k]*f)+'px');}return f;}"""


def img64(name, w=700):
    im = Image.open(IMG / name).convert("RGBA"); im.thumbnail((w, w))
    bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[-1])
    b = io.BytesIO(); bg.save(b, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


e = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
HINT = {"next": ("點這張卡片 ▶ 下一步", None), "retry": ("點這張卡片 ↺ 再選一次", None), "close": ("點這張卡片 關閉", "#5b6675")}


def fbcard(cls, title, text, src=None, img=None, hint="next", extra=""):
    ht, hc = HINT[hint] if hint in HINT else (hint, None)
    body = f'<h1>{e(title)}</h1><p style="margin-top:20px">{e(text)}</p>{extra}' + (f'<div class="src">{e(src)}</div>' if src else "")
    if img: body = f'<div class="split"><img src="{img64(img)}"><div>{body}</div></div>'
    return f'<div class="c {cls}" data-root><div class="bar"></div>{body}<div class="hint"{f" style=background:{hc}" if hc else ""}>{e(ht)}</div></div>', (1600, 900)


def qcard(kick, stem, hint="點選你的答案", cls="info", extra=""):
    return f'<div class="c {cls}" data-root><div class="bar"></div><div class="kick">{e(kick)}</div><h1>{e(stem)}</h1>{extra}<p style="margin-top:26px;color:#5b6675;font-size:52px">{e(hint)}</p></div>', (1600, 900)


def optcard(k, text):
    return f'<div class="c" data-root style="height:500px;padding:40px 70px"><div class="bar"></div><div class="opt"><div class="key">{k}</div><p>{e(text)}</p></div></div>', (1600, 500)


def imgopt(img, name, sub=""):
    return (f'<div class="c io" data-root style="width:800px;height:600px;padding:24px"><div class="bar" style="width:18px"></div><img src="{img64(img, 720)}">'
            f'<b>{e(name)}</b>{f"<span>{e(sub)}</span>" if sub else ""}</div>'), (800, 600)


def btncard(text, color, w=800, h=300, size=84):
    return f'<div class="btn" data-root style="width:{w}px;height:{h}px;background:{color};font-size:{size}px;border-radius:{h//4}px">{e(text)}</div>', (w, h)


def infocard(kick, title, body, cls="info", img=None, hint=None, extra=""):
    inner = f'<div class="kick">{e(kick)}</div><h1>{e(title)}</h1><p style="margin-top:22px">{body}</p>{extra}'
    if img: inner = f'<div class="split"><img src="{img64(img)}"><div>{inner}</div></div>'
    h = f'<div class="hint">{e(hint)}</div>' if hint else ""
    return f'<div class="c {cls}" data-root><div class="bar"></div>{inner}{h}</div>', (1600, 900)


# ---------- 塗抹：VR 頭顯模式的三張範圍圖（同動手版畫法） ----------
ARM_JS = """(s)=>{const W=1400,H=Math.round(W*0.62);const cv=document.createElement('canvas');cv.width=W;cv.height=H;document.body.appendChild(cv);const c=cv.getContext('2d');
 c.fillStyle='#f7f9fc';c.fillRect(0,0,W,H);const gr=c.createLinearGradient(0,H*.12,0,H*.96);gr.addColorStop(0,'#e5b392');gr.addColorStop(.35,'#f4d0b5');gr.addColorStop(.7,'#f3cdb0');gr.addColorStop(1,'#dca783');
 c.fillStyle=gr;c.strokeStyle='#c98f6d';c.lineWidth=3;c.beginPath();c.moveTo(0,H*.13);c.bezierCurveTo(W*.35,H*.16,W*.7,H*.21,W*.9,H*.25);c.lineTo(W,H*.26);c.lineTo(W,H*.85);c.lineTo(W*.9,H*.85);c.bezierCurveTo(W*.7,H*.88,W*.35,H*.93,0,H*.97);c.closePath();c.fill();c.stroke();
 c.fillStyle='#5b6675';c.font='700 40px "Microsoft JhengHei"';c.textBaseline='top';c.textAlign='left';c.fillText('← 手肘',12,10);c.textAlign='right';c.fillText('手腕 →',W-12,10);
 const cx=W*.52,cy=H*.55,cm=W*.07,a=s.w/2*cm,b=s.h/2*cm;
 if(s.k>0){c.fillStyle='rgba(122,63,181,.55)';c.beginPath();c.ellipse(cx,cy,a*s.k,b*s.k,0,0,Math.PI*2);c.fill();}
 const rg=c.createRadialGradient(cx,cy,0,cx,cy,a);rg.addColorStop(0,'rgba(214,72,72,.45)');rg.addColorStop(1,'rgba(214,72,72,.12)');c.fillStyle=rg;c.beginPath();c.ellipse(cx,cy,a,b,0,0,Math.PI*2);c.fill();
 c.setLineDash([12,8]);c.strokeStyle='#1c2430';c.lineWidth=5;c.stroke();c.setLineDash([]);return cv.toDataURL('image/jpeg',0.9);}"""


def build(card):
    """card(stem) → 網站用檔名（由 _build_vr_site.py 提供：找 _extra/hs 下的 png 並壓縮）。回傳 steps 片段與設定。"""
    H = read_handson()
    cards, tts = {}, {}

    def C(name, spec, say=None):
        cards[name] = spec
        if say: tts[name] = say
        return name
    q13, q14, q15, q16, q17, q18, q19, q20 = (Q[i] for i in range(13, 21))

    # ---- PPE 選 4 件（取代 VR 原本 PPE 選擇題）----
    C("HS_PPE_Q", qcard("備物・防護　選物", q14["stem"], "點選要穿戴的 4 件（不分順序），選好按「檢查」；多的 4 張是干擾"),
      "備物與防護。" + q14["stem"] + "從八張用物裡，點選要穿戴的四件，選好按檢查。")
    for p in H["PPE"]:
        C(f"HS_{p['id']}", imgopt(f"h_{p['id']}.png", p["name"], p.get("sub", "")))
    C("HS_CHECK", btncard("✔ 檢查", "#1f8a4c"))
    C("HS_NEED4", fbcard("warn", "要選滿 4 件", "要穿戴的是 4 件：再點選到剛好 4 件，然後按「檢查」。", hint="close"), "要選滿四件，再按檢查。")
    C("HS_PPE_SHOW", fbcard("ng", "正解 4 件已幫你選好", q14["explain_ng"], f"文字來源：規格檔 Q14（表單 {q14['form_item']}）", hint="next"))
    # ---- 選空針 ----
    C("HS_SYR_Q", qcard("回抽　選物（表單 10）", q15["stem"], "先移除裝有剩餘藥品的注射器／輸液套管，然後──接哪一支？"),
      "回抽。先移除裝有剩餘藥品的注射器或輸液套管，然後，接哪一支空針？")
    for s in H["SYR"]:
        C(f"HS_{s['id']}", imgopt(f"h_{s['id']}.png", s["name"], s.get("sub", "")))
        if not s["ok"]:
            C(f"HS_{s['id']}_NG", fbcard("warn", f"{s['name']}？不是這一支", q15["explain_ng"], f"文字來源：規格檔 Q15（表單 10）", hint="retry"), f"{s['name']}，不是這一支。" + q15["explain_ng"])
    C("HS_SYR_OK", fbcard("ok", "接對了", q15["explain_ok"].removeprefix("答對了。"), "文字來源：規格檔 Q15（表單 10）", hint="點這張卡片 ▶ 開始回抽"), "接對了。" + q15["explain_ok"].removeprefix("答對了。"))
    # ---- 回抽按住 ----
    C("HS_ASP_Q", qcard("回抽　動作（表單 11）", "從原靜脈注射處回抽", "按住「回抽」不要放，直到量筒滿、抽不出為止"),
      "從原靜脈注射處回抽。按住回抽按鈕不要放，直到抽不出為止。")
    C("HS_ASP_BTN", btncard("🩸 按住回抽", "#c81e3a", 900, 300, 88))
    C("HS_ASP_GAUGE", ('<div data-root style="width:360px;height:900px;background:transparent;position:relative;font-family:Microsoft JhengHei">'
                       '<div style="position:absolute;left:90px;top:60px;width:180px;height:780px;border:10px solid #5b6675;border-radius:0 0 40px 40px"></div>'
                       + "".join(f'<div style="position:absolute;left:90px;width:80px;top:{840 - n * 180}px;border-top:8px solid #5b6675"></div>'
                                 f'<div style="position:absolute;left:288px;top:{812 - n * 180}px;font-size:46px;font-weight:800;color:#1c2430">{n}</div>' for n in (1, 2, 3, 4))
                       + '<div style="position:absolute;left:250px;top:8px;font-size:40px;font-weight:800;color:#1c2430">mL</div></div>', (360, 900)))
    C("HS_ASP_EARLY", fbcard("warn", H["aspEarly"].split("：")[0], H["aspEarly"].split("：", 1)[-1], hint="點這張卡片 ↺ 再按住一次"), H["aspEarly"])
    asp_t = f"{H['aspTitle']}，估計回抽量約 {H['aspML']:g} mL，記錄下來"
    C("HS_ASP_OK", fbcard("ok", asp_t, q15["explain_ok"].removeprefix("答對了。"), "文字來源：規格檔 Q15（表單 11）"), asp_t + "。" + q15["explain_ok"].removeprefix("答對了。"))
    # ---- 解毒劑（先查查詢站）----
    C("HS_ANTI_GATE", infocard(f"判斷（表單 {q16['form_item']}）", "先查：本案 Cisplatin 稀釋滴注，有沒有適用的解毒劑？",
                               "開查詢站，輸入 <b>Cisplatin</b>，看「處置」欄。查完回來按「我查過了」。", cls="info big"),
      "先查：本案 Cisplatin 稀釋滴注，有沒有適用的解毒劑？開查詢站，輸入 Cisplatin，看處置欄。查完回來按我查過了。")
    C("HS_OPEN_CIS", btncard("🔍 開查詢站查 Cisplatin", "#123a6b", 1000, 300, 70))
    C("HS_CHECKED", btncard("我查過了 ▶", "#1f8a4c", 800, 300, 80))
    C("HS_ANTI_Q", qcard(f"判斷（表單 {q16['form_item']}）", q16["stem"]), q16["stem"] + "點選你的答案。")
    for o in q16["options"]: C(f"HS_ANTI_{o['key']}", optcard(o["key"], o["text"]))
    C("HS_ANTI_OK", fbcard("ok", "答對了", q16["explain_ok"], "本院規則（分工檔）", hint="點這張卡片 ▶ 拔針",
                           extra=f'<p style="margin-top:18px;font-weight:800;color:#123a6b">本案結論：{e(H["antiNote"])}</p>'), q16["explain_ok"] + "本案結論：" + H["antiNote"])
    C("HS_ANTI_NG", fbcard("warn", H["antiTitleNg"], q16["explain_ng"], f"文字來源：規格檔 Q16（表單 {q16['form_item']}）", hint="retry"), H["antiTitleNg"] + "。" + q16["explain_ng"])
    # ---- 敷療（先查）----
    C("HS_COMP_GATE", infocard(f"查詢後決策（表單 {q19['form_item']}）", "本案 Cisplatin 外滲，敷什麼？",
                               "不憑印象，先查：開查詢站，輸入 <b>Cisplatin</b>，看它是冷敷、熱敷還是 DMSO。查完回來按「我查過了」。", cls="info big"),
      "本案 Cisplatin 外滲，敷什麼？不憑印象，先查。開查詢站輸入 Cisplatin，看它是冷敷、熱敷還是 DMSO。")
    C("HS_COMP_Q", qcard("查詢後決策", "本案 Cisplatin 外滲，敷什麼？"), "本案 Cisplatin 外滲，敷什麼？點選你的答案。")
    for c in H["COMP"]: C(f"HS_{c['id']}", imgopt(f"h_{c['id']}.png", c["name"], c.get("sub", "")))
    C("HS_COMP_OK", fbcard("ok", H["compOk"], H["caseNote"], "本院規則（分工檔）＋查詢站", hint="點這張卡片 ▶ 原則題"), H["compOk"] + "。" + H["caseNote"])
    C("HS_COMP_WARN", fbcard("warn", H["compWarn"], H["caseNote"], "本院規則（分工檔）＋查詢站", hint="點這張卡片 ▶ 原則題"), H["compWarn"] + "。" + H["caseNote"])
    C("HS_COMP_NG", fbcard("ng", H["compDmsoNg"], q20["explain_ng"], f"文字來源：規格檔 Q20", hint="retry"), H["compDmsoNg"] + "。" + q20["explain_ng"])
    C("HS_Q19_Q", qcard(f"原則題（表單 {q19['form_item']}）", q19["stem"]), q19["stem"] + "點選你的答案。")
    for o in q19["options"]: C(f"HS_Q19_{o['key']}", optcard(o["key"], o["text"]))
    C("HS_Q19_OK", fbcard("ok", "答對了", q19["explain_ok"], f"文字來源：規格檔 Q19（表單 {q19['form_item']}）", hint="點這張卡片 ▶ 看九步驟總覽"), "答對了。" + q19["explain_ok"])
    C("HS_Q19_NG", fbcard("ng", "正解說明", q19["explain_ng"], f"文字來源：規格檔 Q19（表單 {q19['form_item']}）", hint="點這張卡片 ▶ 看九步驟總覽"), q19["explain_ng"])
    # ---- 九步驟總覽 ----
    g9 = "".join(f'<div><img src="{img64("h_" + s["id"] + ".png", 240)}"><span><i>{i + 1}</i> {e(s["t"])}</span></div>' for i, s in enumerate(H["STEPS9"]))
    # 9/29：九步驟總覽拆兩張（1–5、6–9）並排，字才夠大；語音掛在第一張
    def g9card(lo, hi, title, foot=""):
        cells = "".join(f'<div><img src="{img64("h_" + s["id"] + ".png", 300)}"><span><i>{i + 1}</i> {e(s["t"])}</span></div>'
                        for i, s in enumerate(H["STEPS9"]) if lo <= i + 1 <= hi)
        return (f'<div class="c ok" data-root style="justify-content:flex-start;padding-top:40px;height:1200px"><div class="bar"></div><div class="kick">完成案例一・九步驟總覽</div>'
                f'<h1 style="font-size:84px">{e(title)}</h1><div class="grid9 g9big">{cells}</div>'
                + (f'<p style="font-size:50px;color:#5b6675;margin-top:14px">{e(foot)}</p>' if foot else "") + '</div>', (1600, 1200))
    C("HS_SUM1", g9card(1, 5, "第 1–5 步"),
      "完成案例一。初步處理九個步驟：" + "；".join(f"第{i + 1}，{s['t']}" for i, s in enumerate(H["STEPS9"])) + "。第九步 DMSO 在案例二。")
    C("HS_SUM1B", g9card(6, 9, "第 6–9 步", "第 9 步 DMSO 在案例二。"))
    C("HS_GO_LOOKUP", btncard("下一站：查詢站 ▶", "#123a6b", 1000, 300, 72))
    C("HS_GO_C2", btncard("🟣 案例二 DMSO", "#7a3fb5", 1000, 300, 72))
    C("HS_GO_C3", btncard("⏰ 案例三 抬高 48 小時", "#b7791f", 1100, 300, 68))
    C("HS_GO_C1", btncard("↺ 回案例一從頭做", "#5b6675", 1000, 300, 70))
    C("HS_NEXT_C2", btncard("下一站：案例二 DMSO ▶", "#7a3fb5", 1100, 300, 68))
    C("HS_NEXT_C3", btncard("下一站：案例三 抬高 48 小時 ▶", "#b7791f", 1300, 300, 64))

    # ---- 案例二 DMSO ----
    C("HS_C2_INTRO", infocard("案例二｜情境", "Doxorubicin（小紅莓）外滲", e(H["sc2"]), img="h_sc02.png", cls="dm"), "案例二。" + H["sc2"])
    C("HS_C2_GATE", infocard("查詢（表單 16）", "Doxorubicin 外滲，查詢站說要怎麼敷？",
                             "開查詢站，輸入 <b>Doxorubicin</b>（或 Adriamycin、小紅莓），記住：塗多大範圍、風乾還是覆蓋、幾天。", cls="dm big"),
      "Doxorubicin 外滲，查詢站說要怎麼敷？開查詢站，輸入 Doxorubicin，記住：塗多大範圍、風乾還是覆蓋、幾天。")
    C("HS_OPEN_DOX", btncard("🔍 開查詢站查 Doxorubicin", "#7a3fb5", 1100, 300, 66))
    C("HS_C2_FOUND", fbcard("dm", "查到了：DMSO＋冷敷", H["LOOKUP_DOXO"], "查詢站 Doxorubicin 列（院內 2023.5 版）", hint="點這張卡片 ▶ 開始三題",
                            extra=f'<p style="margin-top:16px;font-size:48px;color:#1c2430">為什麼是 DMSO：{e(q20["explain_ok"].removeprefix("答對了。"))}</p>'),
      "查到了：DMSO 加冷敷。" + H["LOOKUP_DOXO"])
    for i, d in enumerate(H["DM"]):
        C(f"HS_{d['key']}_Q", qcard(f"DMSO {i + 1}／3", d["stem"], cls="dm"), d["stem"] + "點選你的答案。")
        for j, o in enumerate(d["opts"]): C(f"HS_{d['key']}_{'ABC'[j]}", optcard("ABC"[j], o))
        C(f"HS_{d['key']}_OK", fbcard("ok", "答對了", H["LOOKUP_DOXO"], "查詢站 Doxorubicin 列（院內 2023.5 版）"), "答對了。" + H["LOOKUP_DOXO"])
        C(f"HS_{d['key']}_NG", fbcard("ng", "正解：" + d["opts"][d["ans"]], H["LOOKUP_DOXO"], "查詢站 Doxorubicin 列（院內 2023.5 版）"), "正解是，" + d["opts"][d["ans"]] + "。" + H["LOOKUP_DOXO"])
    sp = H["PAINT_SPOT"]
    C("HS_PAINT_Q", infocard("動手塗　DMSO 範圍", "動手塗一次：DMSO 要塗到多大？",
                             f"黑色虛線＝油性筆畫的外滲範圍（{sp['w']}×{sp['h']} cm）。點下面「開始塗抹」，用手指或滑鼠塗到你認為的<b>患部兩倍範圍</b>。", cls="dm"),
      f"動手塗一次：DMSO 要塗到多大？黑色虛線是油性筆畫的外滲範圍。點開始塗抹，塗到你認為的患部兩倍範圍。")
    C("HS_PAINT_BTN", btncard("🖌️ 開始塗抹", "#7a3fb5", 900, 300, 80))
    C("HS_PAINT_VRQ", qcard("動手塗　DMSO 範圍（頭顯版）", "DMSO 要塗到多大？哪一張的紫色範圍對？", "頭顯內無法用手指塗，改成選圖", cls="dm"),
      "DMSO 要塗到多大？哪一張的紫色範圍是對的？點選你的答案。")
    keyp_html = "<ul>" + "".join(f"<li style='font-size:46px;line-height:1.4'>{e(x)}</li>" for x in H["keyp"]) + "</ul>"
    C("HS_PAINT_OK", fbcard("ok", H["paintOK"], "", H["paintSrc"], extra=keyp_html), H["paintOK"] + "。" + "；".join(H["keyp"]))
    C("HS_PAINT_SMALL", fbcard("warn", *H["paintSmall"], H["paintSrc"], hint="retry"), "。".join(H["paintSmall"]))
    C("HS_PAINT_BIG", fbcard("warn", *H["paintBig"], H["paintSrc"], hint="retry"), "。".join(H["paintBig"]))
    C("HS_C2_SUM", infocard("完成案例二", "記住這一行", e(H["LOOKUP_DOXO"]), cls="ok",
                            extra=f'<div class="src">查詢站 Doxorubicin 列（院內 2023.5 版）　九步驟第 9 步：{e(H["STEPS9"][8]["t"])}</div>'),
      "完成案例二。記住這一行：" + H["LOOKUP_DOXO"])

    # ---- 案例三 抬高 48 小時（9/29 使用者定：三個案例都必做）----
    C("HS_C3_INTRO", infocard("案例三｜情境", "外滲後的 48 小時", e(H["sc3"]) + f'<br><b>{e(H["sc3key"])}</b>', cls="warn",
                              extra=f'<div class="src">{e(H["EL_SRC"])}</div>'), "案例三，外滲後的四十八小時。" + H["sc3"] + H["sc3key"])
    for i, d in enumerate(H["EL"]):
        C(f"HS_{d['key']}_Q", qcard(f"情境 {i + 1}／{len(H['EL'])}　{d['ic']} {d['when']}", d["stem"], cls="warn"), d["when"] + "。" + d["stem"] + "點選你的答案。")
        right = next(o for o in d["opts"] if o["ok"])
        for j, o in enumerate(d["opts"]):
            C(f"HS_{d['key']}_{'ABC'[j]}", optcard("ABC"[j], o["t"]))
            if o["ok"]:
                C(f"HS_{d['key']}_{'ABC'[j]}_FB", fbcard("ok", "答對了", o["why"], H["EL_SRC"]), "答對了。" + o["why"])
            else:
                C(f"HS_{d['key']}_{'ABC'[j]}_FB", fbcard("ng", "這樣不對", o["why"], None, hint="retry",
                                                           extra=f'<p style="margin-top:18px;font-size:50px;color:#1f8a4c;font-weight:800">正解：{e(right["t"])}</p>'),
                  "這樣不對。" + o["why"])
    C("HS_C3_SUM", infocard("完成案例三", "一句話帶走", e(H["el_one"]), cls="ok", extra=f'<div class="src">{e(H["EL_SRC"])}</div>'), "完成案例三。" + H["el_one"])

    # ---- 渲染 ----
    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome", headless=True)
        pg = br.new_page(device_scale_factor=1.6)   # 9/29：提高解析度（1600→2560 寬）
        shrunk = []
        for name, (html, (w, h)) in cards.items():
            pg.set_viewport_size({"width": w, "height": h})
            pg.set_content(f"<style>{CSS}</style>{html}"); pg.wait_for_timeout(60)
            f = pg.evaluate(FIT_JS)
            if f < 0.999: shrunk.append((name, round(f, 2)))
            pg.locator("[data-root]").first.screenshot(path=str(OUT / f"{name}.png"), omit_background=True)
        # 塗抹三張範圍圖（頭顯版）：只塗患部／約兩倍／整片
        arm = {}
        for k, s in (("A", 1.0), ("B", H["DMSO_SCALE"]), ("C", 2.9)):
            pg.set_viewport_size({"width": 1400, "height": 900})
            url = pg.evaluate(ARM_JS, {"w": sp["w"], "h": sp["h"], "k": s})
            im = Image.open(io.BytesIO(base64.b64decode(url.split(",")[1])))
            b = io.BytesIO(); im.save(b, "JPEG", quality=88)
            html = (f'<div class="c io" data-root style="width:800px;height:600px;padding:18px"><div class="bar" style="width:18px"></div>'
                    f'<img src="data:image/jpeg;base64,{base64.b64encode(b.getvalue()).decode()}" style="height:470px"><b>{k}</b></div>')
            pg.set_viewport_size({"width": 800, "height": 600}); pg.set_content(f"<style>{CSS}</style>{html}"); pg.wait_for_timeout(60)
            pg.locator("[data-root]").first.screenshot(path=str(OUT / f"HS_PAINT_{k}.png"))
            arm[k] = f"HS_PAINT_{k}"
        # 2D 塗抹面板用的前臂底圖（不塗）
        pg.set_viewport_size({"width": 1400, "height": 900})
        url = pg.evaluate(ARM_JS, {"w": sp["w"], "h": sp["h"], "k": 0})
        br.close()
    if shrunk: print("縮字：", shrunk)

    # ---- 語音（文字沒變就不重生）----
    cache = json.loads(TTS_CACHE.read_text(encoding="utf-8")) if TTS_CACHE.exists() else {}
    todo = {k: v for k, v in tts.items() if cache.get(k) != v or not (AUD / f"{k}.mp3").exists()}
    if todo:
        import edge_tts
        async def one(k, t):
            await edge_tts.Communicate(t, VOICE, rate=RATE).save(str(AUD / f"{k}.mp3"))
        async def run():
            sem = asyncio.Semaphore(4)
            async def w(k, t):
                async with sem:
                    for i in range(3):
                        try: await one(k, t); return
                        except Exception as ex:
                            if i == 2: raise
                            await asyncio.sleep(2)
            await asyncio.gather(*(w(k, t) for k, t in todo.items()))
        asyncio.run(run())
        cache.update(todo); TTS_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"handson→VR：{len(cards)} 張新卡、語音新生 {len(todo)} 支")

    A = lambda n: card(n)          # 交給網站壓縮
    au = lambda n: n if n in tts else None

    S = {}
    S["ppe"] = {"id": "ppe", "title": "備物・防護：選物", "sky": "store", "type": "multi", "q": A("HS_PPE_Q"), "nar": "HS_PPE_Q",
                "items": [{"img": A(f"HS_{p['id']}"), "need": p["order"] > 0} for p in H["PPE"]],
                "check": A("HS_CHECK"), "need4": {"img": A("HS_NEED4"), "au": "HS_NEED4"},
                "ok": {"img": None, "au": "VD4OK"}, "ng": {"img": None, "au": "VD4XB"}, "show": {"img": A("HS_PPE_SHOW"), "au": "VD4XB"}}
    S["syr"] = {"id": "syr", "title": "回抽：選空針", "sky": "bed", "type": "mcq", "grid": True, "q": A("HS_SYR_Q"), "nar": "HS_SYR_Q",
                "opts": [{"img": A(f"HS_{s['id']}"), "fb": A("HS_SYR_OK" if s["ok"] else f"HS_{s['id']}_NG"),
                          "au": "HS_SYR_OK" if s["ok"] else f"HS_{s['id']}_NG", "adv": s["ok"]} for s in H["SYR"]]}
    S["asp"] = {"id": "asp", "title": "回抽：按住回抽", "sky": "bed", "type": "hold", "q": A("HS_ASP_Q"), "nar": "HS_ASP_Q",
                "btn": A("HS_ASP_BTN"), "gauge": A("HS_ASP_GAUGE"), "ms": H["aspFull"],
                "early": {"img": A("HS_ASP_EARLY"), "au": "HS_ASP_EARLY"}, "done": {"img": A("HS_ASP_OK"), "au": "HS_ASP_OK"}}
    S["antig"] = {"id": "antig", "title": "解毒劑：先查", "sky": "bed", "type": "gate", "main": A("HS_ANTI_GATE"), "nar": "HS_ANTI_GATE",
                  "open": A("HS_OPEN_CIS"), "url": "../lookup/?tab=q&kw=Cisplatin", "utitle": "敷療查詢站：Cisplatin", "checked": A("HS_CHECKED")}
    S["anti"] = {"id": "anti", "title": "解毒劑 → 拔針", "sky": "bed", "type": "mcq", "q": A("HS_ANTI_Q"), "nar": "HS_ANTI_Q",
                 "opts": [{"img": A(f"HS_ANTI_{o['key']}"), "fb": A("HS_ANTI_OK" if o["key"] == q16["answer"] else "HS_ANTI_NG"),
                           "au": "HS_ANTI_OK" if o["key"] == q16["answer"] else "HS_ANTI_NG", "adv": o["key"] == q16["answer"]} for o in q16["options"]]}
    S["compg"] = {"id": "compg", "title": "敷療：先查", "sky": "bed", "type": "gate", "main": A("HS_COMP_GATE"), "nar": "HS_COMP_GATE",
                  "open": A("HS_OPEN_CIS"), "url": "../lookup/?tab=q&kw=Cisplatin", "utitle": "敷療查詢站：Cisplatin", "checked": A("HS_CHECKED")}
    cfb = {"ok": ("HS_COMP_OK", True), "warn": ("HS_COMP_WARN", True), "ng": ("HS_COMP_NG", False)}
    S["comp"] = {"id": "comp", "title": "敷療：本案敷什麼", "sky": "bed", "type": "mcq", "grid": True, "q": A("HS_COMP_Q"), "nar": "HS_COMP_Q",
                 "opts": [{"img": A(f"HS_{c['id']}"), "fb": A(cfb[c["kind"]][0]), "au": cfb[c["kind"]][0], "adv": cfb[c["kind"]][1]} for c in H["COMP"]]}
    S["q19"] = {"id": "q19", "title": "敷療：原則題", "sky": "bed", "type": "mcq", "q": A("HS_Q19_Q"), "nar": "HS_Q19_Q",
                "opts": [{"img": A(f"HS_Q19_{o['key']}"), "fb": A("HS_Q19_OK" if o["key"] == q19["answer"] else "HS_Q19_NG"),
                          "au": "HS_Q19_OK" if o["key"] == q19["answer"] else "HS_Q19_NG", "adv": True} for o in q19["options"]]}
    S["sum1"] = {"id": "sum1", "title": "案例一完成：九步驟總覽", "sky": "store", "type": "info", "main": A("HS_SUM1"), "main2": A("HS_SUM1B"), "nar": "HS_SUM1",
                 "btns": [{"img": A("HS_NEXT_C2"), "to": "c2intro"}]}
    # 案例二
    C2 = [{"id": "c2intro", "case": 2, "title": "案例二：情境", "sky": "bed", "type": "info", "main": A("HS_C2_INTRO"), "nar": "HS_C2_INTRO", "next": card("BTN_下一步")},
          {"id": "c2gate", "case": 2, "title": "案例二：查詢站", "sky": "bed", "type": "gate", "main": A("HS_C2_GATE"), "nar": "HS_C2_GATE",
           "open": A("HS_OPEN_DOX"), "url": "../lookup/?tab=q&kw=Doxorubicin", "utitle": "敷療查詢站：Doxorubicin", "checked": A("HS_CHECKED"),
           "after": {"img": A("HS_C2_FOUND"), "au": "HS_C2_FOUND"}}]
    for i, d in enumerate(H["DM"]):
        C2.append({"id": d["key"], "case": 2, "title": f"案例二：DMSO {i + 1}／3", "sky": "bed", "type": "mcq", "q": A(f"HS_{d['key']}_Q"), "nar": f"HS_{d['key']}_Q",
                   "opts": [{"img": A(f"HS_{d['key']}_{'ABC'[j]}"), "fb": A(f"HS_{d['key']}_{'OK' if j == d['ans'] else 'NG'}"),
                             "au": f"HS_{d['key']}_{'OK' if j == d['ans'] else 'NG'}", "adv": True} for j in range(len(d["opts"]))]})
        if d["key"] == "dm1":
            C2.append({"id": "paint", "case": 2, "title": "案例二：動手塗 DMSO", "sky": "bed", "type": "paint", "main": A("HS_PAINT_Q"), "nar": "HS_PAINT_Q",
                       "btn": A("HS_PAINT_BTN"), "vrq": A("HS_PAINT_VRQ"),
                       "vropts": [{"img": A(arm["A"]), "fb": A("HS_PAINT_SMALL"), "au": "HS_PAINT_SMALL", "adv": False},
                                  {"img": A(arm["B"]), "fb": A("HS_PAINT_OK"), "au": "HS_PAINT_OK", "adv": True},
                                  {"img": A(arm["C"]), "fb": A("HS_PAINT_BIG"), "au": "HS_PAINT_BIG", "adv": False}]})
    C2.append({"id": "c2sum", "case": 2, "title": "案例二完成", "sky": "bed", "type": "info", "main": A("HS_C2_SUM"), "nar": "HS_C2_SUM",
               "btns": [{"img": A("HS_NEXT_C3"), "to": "c3intro"}]})
    # 案例三
    C3 = [{"id": "c3intro", "case": 3, "title": "案例三：抬高 48 小時", "sky": "room", "type": "info", "main": A("HS_C3_INTRO"), "nar": "HS_C3_INTRO", "next": card("BTN_下一步")}]
    for i, d in enumerate(H["EL"]):
        C3.append({"id": d["key"], "case": 3, "title": f"案例三：情境 {i + 1}／{len(H['EL'])}", "sky": "room", "type": "mcq", "q": A(f"HS_{d['key']}_Q"), "nar": f"HS_{d['key']}_Q",
                   "opts": [{"img": A(f"HS_{d['key']}_{'ABC'[j]}"), "fb": A(f"HS_{d['key']}_{'ABC'[j]}_FB"), "au": f"HS_{d['key']}_{'ABC'[j]}_FB", "adv": o["ok"]}
                            for j, o in enumerate(d["opts"])]})
    C3.append({"id": "c3sum", "case": 3, "title": "案例三完成", "sky": "room", "type": "info", "main": A("HS_C3_SUM"), "nar": "HS_C3_SUM",
               "btns": [{"img": A("HS_GO_LOOKUP"), "to": "lookup"}]})
    paint_cfg = {"scale": H["DMSO_SCALE"], "cover": H["PAINT_PASS_COVER"], "outside": H["PAINT_MAX_OUTSIDE"], "spot": sp,
                 "small": H["paintSmall"], "big": H["paintBig"], "off": H["paintOff"], "ok": H["paintOK"], "show": H["paintShow"],
                 "keyp": H["keyp"], "src": H["paintSrc"]}
    return S, C2, C3, paint_cfg, {"toC2": A("HS_GO_C2"), "toC3": A("HS_GO_C3")}
