# 待 AI 生圖清單（S4 → 使用者；2026-09-26）

素材庫 `素材_全院pptx/` 找不到合適圖的題目。目前先用暫用圖（見 `_對照表.md` ⚠ 列）讓 S1 排版，生好圖後請存到 `素材_全院pptx/gen_qNN_*.png`，我再壓成 `docs/assets/img/qNN.png`（或直接覆蓋，寬 1200、≤300 KB）。

風格統一（四張共用）：**扁平教學插畫、不寫實**（使用者 9/26 18:43 定：寫實版看了不舒服）＝簡化形狀、細外框、粉彩臨床色、無切開組織、無血泊、紅腫只用淡色；淺膚色、白底、無文字浮水印、標註只留字母。畫面 16:9。

---

## gen_q03／q04：留置針管徑對血管的影響（Q3、Q4 共用一張）

**用途**：Q3「選 22 號或更小」、Q4「大管徑傷血管壁、阻礙針頭下方血流」

**Prompt（英文，貼給 ChatGPT／Gemini）**：
> Flat infographic-style schematic, side-by-side in one 16:9 frame, white background, NOT photorealistic. Two identical horizontal blue tubes (the same peripheral vein) drawn as simple outlines. Left panel labelled "A": a THICK grey rod (20G cannula) nearly fills the tube, tube outline bulges and turns soft amber, one thin flow arrow downstream, a few amber dots just outside the tube. Right panel labelled "B": a THIN grey rod (22G–24G) with plenty of space, three thick blue flow arrows carrying green dots away, tube outline clean blue. No text other than "A", "B", "20G", "22G". Flat shapes, no cross-section shading, no blood, no watermark.

**中文說明給生圖時參考**：左＝大管徑（20G）塞滿血管、管壁紅、下游血流細、藥品滲出；右＝小管徑（22–24G）血流充足把藥帶走、管壁完整。

---

## gen_q07：淋巴水腫肢體不注射

**用途**：Q7「右側乳癌術後右上肢淋巴水腫，不可在右手注射」

**Prompt**：
> Flat stylized medical illustration, 16:9, white background, NOT photorealistic, soft pastel colors, thin outlines. A woman's torso and both arms viewed from the front, chest area neutral (no anatomical detail). Her RIGHT arm (viewer's left) is visibly swollen with lymphedema from upper arm to hand, skin slightly tight and shiny; a large red prohibition circle-with-slash is overlaid on the right forearm. Her LEFT arm is normal size with a small green check mark near the forearm. A subtle dashed line at the right axilla suggests prior surgery. No text, no watermark, soft shadows.

---

## gen_q08：下肢（腳背）不注射化療藥品

**用途**：Q8「雙上肢無法建立周邊靜脈，不可改打腳背」

**Prompt**：
> Flat stylized medical illustration, 16:9, white background, NOT photorealistic, soft pastel colors, thin outlines. Close-up of a human foot (dorsum) with visible superficial veins; an IV cannula is about to be inserted on the dorsum of the foot, but a large red prohibition circle-with-slash is overlaid on it. In the upper-right corner, a small inset shows a chest with an implanted port (Port-A-Cath) under the skin with a green check mark, indicating the correct alternative. No text, no watermark, soft shadows.

---

## （S3 交清單後補）③ 後果卡三張

S3 的 `docs/handson/_卡片清單.md` 尚未交來（11:45 查無此檔）。清單到了再補一輪。

⚠ 先說一件事：**s285–293 在素材庫裡沒有任何圖檔**（`ls 素材_全院pptx | grep s28[5-9]` 為 0），這幾張是純文字投影片（減少危害／穿 PPE／單面防水吸水紙／停止給藥／移開化療 set 勿拔針），所以「用物卡用 s285–293 裁切」做不到，用物 8 張也要走生圖或用文字卡。

---

# ③ 動手互動圖卡：走生圖方案（使用者 9/26 12:0x 定）

S3 清單 12:05 仍未交。先依規格檔 7-1 盤點表（用物 8＝PPE 4 正確＋4 干擾、空針 3、筆 3、後果 3）把 prompt 寫好；S3 清單若改名或增減，只調對應那張。生好後請存 `素材_全院pptx/gen_h_*.png`，我壓成 `docs/assets/img/h_*.png`（寬 600、正方形卡片、≤100 KB，S3 從 `../assets/img/h_ppe01.png` 引用）。

**共用風格（全部 17 張一致，貼在每段 prompt 前面）**：
> Flat vector icon style, single object centered on a plain white background, soft pastel colors, thin dark outline, no text, no watermark, square 1:1 composition, consistent lighting. Suitable as a card in a nursing e-learning quiz.

## 用物卡 8 張（表單 9：從 8 張挑 4 張並排序）

正確四件（順序＝防水隔離衣 → 雙層手套套住袖口 → 外科口罩 → 護目鏡／面罩）：

| 檔名 | 物件 | Prompt 主體 |
|---|---|---|
| h_ppe01 | 防水隔離衣（後開式、長袖、袖口可束緊） | A light-blue fluid-resistant isolation gown, long sleeves with elastic cuffs, ties at the back, shown hanging flat front view. |
| h_ppe02 | 雙層手套套住袖口 | Two pairs of nitrile gloves worn double-layered, the outer glove cuff pulled over the sleeve cuff of a blue gown; close-up of forearm and hand. |
| h_ppe03 | 外科口罩 | A standard pleated surgical face mask, light blue, with ear loops, front view. |
| h_ppe04 | 護目鏡／防護面罩 | Clear protective goggles and a clear full face shield side by side. |

干擾四件（S4 提議，S3 可換）：

| 檔名 | 物件 | Prompt 主體 |
|---|---|---|
| h_ppe05 | 一般布隔離衣（不防水） | A plain yellow cloth isolation gown, thin fabric, no cuffs, clearly non-waterproof, hanging flat. |
| h_ppe06 | 單層手套 | A single pair of thin latex examination gloves lying flat. |
| h_ppe07 | 髮帽 | A disposable blue bouffant surgical cap. |
| h_ppe08 | 鞋套 | A pair of disposable blue shoe covers. |

## 空針卡 3 張（表單 10：接哪一支）

| 檔名 | 物件 | Prompt 主體 |
|---|---|---|
| h_syr03 | 3 mL 空針 | A small empty 3 mL Luer-lock syringe without needle, plunger fully pushed in, side view, scale marks visible but no numbers. |
| h_syr10 | 10 mL 空針（正解） | An empty 10 mL Luer-lock syringe without needle, plunger fully pushed in, side view, sterile packaging half-open beside it. |
| h_syr50 | 50 mL 空針 | A large empty 50 mL syringe without needle, side view, noticeably bulky. |

（三張要能一眼比出大小：建議一次生成一張「三支並排」的圖再裁成三張，比例才一致。）

## 筆卡 3 張（表單 14：選筆）

| 檔名 | 物件 | Prompt 主體 |
|---|---|---|
| h_pen_oil | 油性筆（正解） | A black permanent marker pen (oil-based), cap off, thin tip, a short bold line drawn beside it that looks smudge-proof. |
| h_pen_ball | 原子筆 | An ordinary blue ballpoint pen, cap off, a thin faint line drawn beside it. |
| h_pen_water | 水性麥克筆 | A water-based marker pen with a broad tip, a line beside it partly washed out by a water droplet. |

## 後果卡 3 張（錯誤動作的後果頁；S3 清單定 **4:3**（1200×900）；白底無文字；**仍是扁平插畫，不寫實**——使用者 9/26 定）

| 檔名 | 後果 | Prompt |
|---|---|---|
| h_bad_pull | 拔針 → 藥留組織、失去回抽路徑（**9/27 v3**：v2 左格針尖仍畫在血管內，與外滲情境不符；v1／v2 棄用存素材夾） | Flat stylized medical education infographic, 4:3, white background, NOT photorealistic, no gore, soft pastel colors, thin dark outlines. Two side-by-side panels showing the SAME simplified forearm cross-section drawn as three smooth color bands: skin on top, a pale subcutaneous layer in the middle, and a blue vein running horizontally near the bottom — no fat globules, no muscle texture. In BOTH panels the situation is extravasation: a pale-yellow pool of leaked drug sits in the subcutaneous layer ABOVE the vein; the vein itself is intact and slightly pushed aside, with NO drug inside it. LEFT panel (correct, soft green tint at the top edge): a soft plastic IV cannula (no metal needle) still passes through the skin, but its tip has slipped OUT of the vein and rests inside the subcutaneous layer right next to the drug pool, tip pointing left toward the elbow; a syringe is attached to the cannula hub with the plunger being pulled back; the pool is shrinking, with small curved arrows flowing from the pool into the cannula tip and up into the syringe. RIGHT panel (wrong, soft amber tint at the top edge): the cannula has been pulled out and lies on the skin surface (soft plastic tube only, no metal needle); a tiny closed puncture dot on the skin; the same yellow pool now sits sealed in the subcutaneous layer, larger and spread wider; a syringe hovers above the skin with a red circle-slash over it, and a short dashed line from its tip stops at the skin surface. No text, no letters, no labels; leave a clear white margin at the top for captions. |
| h_bad_press | 壓迫 → 浸潤範圍擴大 | Flat stylized illustration, 4:3, white background, NOT photorealistic. A gloved hand pressing gauze onto a forearm IV site drawn as a simple outline; the drug under the skin shown as a semi-transparent pale-yellow blob seen through the skin (no cut-open view), with small motion arrows pushing its edge outward well past a dashed outline of the original small area. A soft pink tint around it. No text, no blood. |
| h_bad_ballpen | 原子筆 → 48 小時後看不到範圍 | Medical illustration, 4:3, white background, two-panel before/after. Left: a swollen red area on a forearm outlined with a thin blue ballpoint line. Right: the same forearm two days later, the ballpoint line has faded and smeared to almost nothing under sweat and a dressing edge, so the redness border can no longer be compared. A small faded clock icon between panels. No text. |

---

# S3 清單（17:5x 交）補的一輪：情境 2＋敷療 1＋步驟 4

素材庫可裁的 7 張已產（h_cp01 冰敷袋、h_cp02 熱敷袋、h_st01 立即處置、h_st04 回抽回血照、h_st05 醫療處置、h_st07 油性筆圈範圍、h_st08 冰敷＋熱敷），見 `_對照表.md`。以下 7 張素材庫沒有，走生圖：

## 情境卡 2 張｜16:9（1200×675）

| 檔名 | Prompt |
|---|---|
| h_sc01 | Flat stylized medical illustration, 16:9, NOT photorealistic, soft pastel colors, thin outlines, hospital ward. A middle-aged Taiwanese male patient ("張示範") lying in a hospital bed, an IV infusion running into a peripheral cannula on his LEFT forearm; the skin around the insertion site is visibly swollen and tight with mild redness, he grimaces in pain and looks at his arm. IV pole with a clear infusion bag beside the bed. Soft daylight, calm colors, no text, no watermark, no name tags. |
| h_sc02 | Flat stylized medical illustration, 16:9, NOT photorealistic, soft pastel colors, thin outlines, hospital ward. The same middle-aged Taiwanese male patient sitting up in bed; a nurse's gloved hand is slowly pushing a syringe of bright RED liquid (doxorubicin) into a peripheral cannula on his RIGHT forearm; the skin around the insertion site is swollen and red. No text, no watermark, no name tags. |

## 敷療卡 1 張｜1:1（600×600）

| 檔名 | Prompt 主體（前面貼共用風格句） |
|---|---|
| h_cp03 | A small amber glass medicine bottle labelled only with a blank white label, next to a cotton-tipped applicator swab, suggesting a topical solution (DMSO) for skin application. No readable text. |

## 步驟卡 4 張｜1:1（600×600）

| 檔名 | 步驟 | Prompt 主體（前面貼共用風格句） |
|---|---|---|
| h_st02 | 穿戴 PPE 四件 | A nurse shown from the waist up wearing a light-blue fluid-resistant gown, double gloves pulled over the cuffs, surgical mask and clear goggles, arms slightly raised to display the full set. |
| h_st03 | 接無菌 10 mL 空針 | 直接複製 h_syr10（同一張，不必再生）。 |
| h_st06 | 勿壓迫 | A forearm IV site with a swollen area; a gloved hand hovering just above it NOT touching, with a large red prohibition circle-with-slash over the hand to mean "do not press". |
| h_st09 | DMSO 局部塗抹 | A gloved hand applying clear liquid with a cotton swab onto a reddened patch of skin on a forearm, an amber bottle beside it. No text. |
