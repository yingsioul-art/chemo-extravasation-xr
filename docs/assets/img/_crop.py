# -*- coding: utf-8 -*-
"""S4 圖片裁切腳本：從 素材_全院pptx/ 挑圖 → 16:9 或 4:3、寬 1200、≤300 KB PNG。
重跑安全：每次覆蓋本腳本自己產的檔（q10.jpg 不在此腳本範圍，不動）。
用法：PYTHONUTF8=1 python docs/assets/img/_crop.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

SRC = r"D:\Zettelkasten\20_教學\Makar\競賽報告\素材_全院pptx"
OUT = os.path.dirname(os.path.abspath(__file__))
W = 1200
FONT = "C:/Windows/Fonts/msjh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msjhbd.ttc"


def load(name, crop=None):
    """讀素材，白底壓平透明；crop=(左,上,右,下) 像素框。"""
    im = Image.open(os.path.join(SRC, name)).convert("RGBA")
    if crop:
        im = im.crop(crop)
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert("RGB")


def canvas(aspect):
    h = 675 if aspect == "16:9" else 900
    return Image.new("RGB", (W, h), (255, 255, 255))


def fit(im, box_w, box_h):
    """等比縮放到框內（允許放大，向量風格圖放大可接受）。"""
    r = min(box_w / im.width, box_h / im.height)
    return im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)


def paste_center(cv, im, cx, cy):
    cv.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def caption(cv, text, cx, cy, size=34, bold=True, color=(30, 30, 30)):
    d = ImageDraw.Draw(cv)
    f = ImageFont.truetype(FONT_BOLD if bold else FONT, size)
    bb = d.textbbox((0, 0), text, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2, cy - (bb[3] - bb[1]) / 2), text, font=f, fill=color)


def single(name, aspect, margin=24, crop=None):
    cv = canvas(aspect)
    im = fit(load(name, crop), W - 2 * margin, cv.height - 2 * margin)
    paste_center(cv, im, W / 2, cv.height / 2)
    return cv


def row(items, aspect="16:9", cap_h=70, gap=30, margin=40, cap_size=34):
    """items=[(name, caption, crop)] 橫排＋下方字幕。"""
    cv = canvas(aspect)
    n = len(items)
    cell_w = (W - 2 * margin - gap * (n - 1)) / n
    box_h = cv.height - 2 * margin - cap_h
    for i, (name, cap, crop) in enumerate(items):
        im = fit(load(name, crop), cell_w, box_h)
        cx = margin + cell_w * (i + 0.5) + gap * i
        paste_center(cv, im, cx, margin + box_h / 2)
        if cap:
            caption(cv, cap, cx, cv.height - margin - cap_h / 2, size=cap_size)
    return cv


def save(cv, fname, limit_kb=300):
    p = os.path.join(OUT, fname)
    cv.save(p, "PNG", optimize=True)
    if os.path.getsize(p) > limit_kb * 1024:
        q = cv.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        q.save(p, "PNG", optimize=True)
    for c, dith in ((128, Image.FLOYDSTEINBERG), (128, Image.NONE), (64, Image.NONE), (32, Image.NONE)):
        if os.path.getsize(p) > limit_kb * 1024:
            q = cv.quantize(colors=c, method=Image.MEDIANCUT, dither=dith)
            q.save(p, "PNG", optimize=True)
    if os.path.getsize(p) > limit_kb * 1024:
        # 照片型降色仍超標 → 改存 JPEG（同 q10.jpg 前例），移除 png
        os.remove(p)
        p = os.path.splitext(p)[0] + ".jpg"
        cv.save(p, "JPEG", quality=85, optimize=True)
    print(f"{os.path.basename(p):10s} {cv.width}x{cv.height} {os.path.getsize(p)//1024:4d} KB")


def main():
    # ── 區塊 A ──
    save(single("s251_image93.png", "16:9"), "q01.png")            # 優先性考量：靜脈導管種類／給藥順序
    save(single("s250_image92.png", "16:9"), "q02.png")            # 安全給藥 方法／評估／時機（起疱性 15 分鐘）
    # ── 區塊 B（素材庫無管徑圖，暫用周邊留置針剖面圖；待生圖）──
    save(single("s085_image48.png", "16:9"), "q03.png")
    save(single("s085_image48.png", "16:9"), "q04.png")
    # ── 區塊 C ──
    save(single("s102_image50.png", "16:9"), "q05.png")            # 前臂靜脈圖
    x = "s110_image51.png"
    cv = row([("s110_image52.png", "手背", None), ("s114_image53.png", "肘前窩", None)], gap=80)
    xm = fit(load(x), 110, 110)
    cv.paste(xm, (int(W * 0.25) + 120, 60)); cv.paste(xm, (int(W * 0.75) + 120, 60))
    save(cv, "q06.png")
    save(single("s142_image57.png", "4:3"), "q07.png")             # 部位 優先／避免 心智圖（含水腫肢體；暫用，待生圖）
    save(single("s142_image57.png", "4:3"), "q08.png")             # 同上（含下肢／放射治療肢體；暫用，待生圖）
    save(single("right-arm-elbow-medical-illustration.png", "16:9", margin=0, crop=(0, 200, 1448, 1014)), "q09.png")  # 前臂直而明顯的血管（照片型，降色至 ≤300 KB）
    # q10.jpg 已由 S0 放入（gen_q10 AI 生圖），本腳本不動
    # ── 區塊 D ──
    save(row([("s267_image103.png", "疼痛、燒灼感", None), ("s269_image104.png", "發紅、紅斑", None),
              ("s271_image105.png", "腫脹、硬結", None), ("s275_image107.png", "流速減慢", None)],
             cap_size=30), "q11.png")
    save(row([("s200_image83.png", "回抽是否有回血？推注有無阻力？", None),
              ("s213_image85.png", "回血須為全血", None)], gap=60, cap_size=30), "q12.png")
    # ── 區塊 G（⑤ 紀錄與追蹤）──
    # s337 上半部含病人資料 → 只取頁首以下區域（y≥228）
    nr = (212, 228, 1672, 1000)
    save(single("s337_image122.png", "16:9", margin=0, crop=nr), "q24.png")
    save(row([("s345_image125.png", "外滲當下拍照", None), ("s360_image128.png", "上傳 Portal", (0, 60, 1858, 938))],
             gap=40), "q25.png")
    rp = (10, 100, 1900, 990)   # 去掉瀏覽器工具列
    save(single("s338_image123.png", "16:9", margin=0, crop=rp), "q26.png")
    save(single("s361_image129.png", "4:3", margin=0, crop=(405, 180, 1465, 922)), "q27.png")
    # ⑤ 四張講解卡底圖
    save(single("s337_image122.png", "16:9", margin=0, crop=(212, 228, 1672, 640)), "g01.png")   # 護理過程紀錄（事件選擇區）
    save(single("s360_image128.png", "16:9", margin=0, crop=(0, 60, 1858, 938)), "g02.png")      # Portal 入口
    save(single("s338_image123.png", "16:9", margin=0, crop=(10, 100, 1250, 800)), "g03.png")    # 通報系統：功能選單（新增通報）＋標題
    save(row([("s349_image126.png", "第 1 週：病房護理師電訪", None),
              ("s357_image127.png", "第 2 週起：腫瘤品管每週追蹤", None),
              ("s361_image129.png", "追蹤到 6 週或外科處置後改善", (405, 180, 1465, 922))],
             gap=30, cap_size=26), "g04.png")


if __name__ == "__main__":
    main()


# ── ③ 動手互動卡（S3 清單 2026-09-26 17:5x；檔名 h_<id>；1:1＝600×600、後果 4:3、情境 16:9）──
def square(name, crop=None, size=600, margin=30):
    cv = Image.new("RGB", (size, size), (255, 255, 255))
    im = fit(load(name, crop), size - 2 * margin, size - 2 * margin)
    paste_center(cv, im, size / 2, size / 2)
    return cv


def handson_cards():
    save(square("s320_image119.png"), "h_cp01.png")                     # 冷敷：冰敷袋
    save(square("s321_image120.png"), "h_cp02.png")                     # 熱敷：熱敷袋
    save(square("s364_image130.png", crop=(0, 0, 589, 560)), "h_st01.png")  # 立即處置（去掉底部字）
    save(square("s213_image85.png", crop=(0, 60, 580, 640)), "h_st04.png")  # 回抽：回血照片
    save(square("s305_image112.png"), "h_st05.png")                     # 醫療處置（解毒劑→拔針）
    save(square("s299_image110.png"), "h_st07.png")                     # 油性筆標示範圍
    cv = Image.new("RGB", (600, 600), (255, 255, 255))                  # 冰敷或熱敷（依藥品）
    a = fit(load("s320_image119.png"), 280, 400); b = fit(load("s321_image120.png"), 240, 400)
    paste_center(cv, a, 160, 300); paste_center(cv, b, 440, 300)
    save(cv, "h_st08.png")


if __name__ == "__main__":
    handson_cards()
