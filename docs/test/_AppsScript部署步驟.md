# 前後測成績回傳｜Google Apps Script 部署步驟

> 目的：學員在 `docs/test/index.html` 送出後，成績以 JSON POST 到 Apps Script Web App，寫進您的 Google 試算表一列。
> 全程約 10 分鐘。做完把 Web App 網址貼回 `index.html` 檔頭的 `ENDPOINT` 常數，交 S0 push。

> ✅ **2026-09-26 12:07 已由 S2 用 Playwright 代為完成**（使用者授權「你來做」）：
> - 試算表：`外滲XR_前後測成績`（https://docs.google.com/spreadsheets/d/1ak7cejwNhw8q6hQVY5kPtN87uVxse1VilM6F5J29Ot8/edit ，工作表 `responses`）
> - Apps Script 專案：`外滲XR成績`（綁定上述試算表；部署 v1，執行身分＝我、存取＝所有人）
> - Web App 網址（已寫進 `index.html` ENDPOINT）：`https://script.google.com/macros/s/AKfycby8y3kZ0DrQeeNRm7CpHuokuO8F1g4Q3WRfuE_zmEq8q91G2vdbyC0pp7wX7BEHx6RuVA/exec`
> - 驗證：GET 健康檢查 ok；curl POST 寫入＋同 submission_id 重送回 duplicate；本機瀏覽器端到端（代號 E2E1）→「成績已送出 ✅（試算表第 4 列）」；三列測試資料已刪，標題列保留。
> - 之後改 Code.gs 請看第六節（要「管理部署作業 → 新版本」網址才不變）。以下步驟留作重做或換帳號時參考。

## 一、建試算表

1. 到 Google 雲端硬碟 → 新增 → **Google 試算表**，命名例如 `外滲XR_前後測成績`。
2. 不用建任何欄位或工作表，程式第一次收到資料時會自動建 `responses` 工作表與標題列。

## 二、貼程式碼

1. 在該試算表上方選單 → **擴充功能 → Apps Script**（會開新分頁，專案已綁定這份試算表）。
2. 左側 `Code.gs` 內容全部刪掉，貼上下面「Code.gs 全文」。
3. 按 💾 儲存（Ctrl+S）。專案名稱隨意，例如 `外滲XR成績`。

## 三、部署為 Web App

1. 右上 **部署 → 新增部署作業**。
2. 左上齒輪 → 類型選 **網頁應用程式**。
3. 設定：
   - 說明：`v1`（隨意）
   - 執行身分：**我**（您的帳號）
   - 誰可以存取：**任何人**（一定要選這個，學員不會登入 Google）
4. 按 **部署** → 第一次會要求授權：選您的帳號 → 「Google 尚未驗證這個應用程式」→ 進階 → 前往（專案名稱）（不安全）→ 允許。
5. 複製畫面上的 **網頁應用程式網址**（形如 `https://script.google.com/macros/s/AKfycb…/exec`）。

## 四、貼回網頁

1. 開 `C:\dev\chemo-extravasation-xr\docs\test\index.html`，找到檔頭：
   ```js
   const ENDPOINT = "";
   ```
   改成
   ```js
   const ENDPOINT = "https://script.google.com/macros/s/AKfycb…/exec";
   ```
2. 交 S0 commit＋push；Pages 約 1–2 分鐘更新。

## 五、測試

1. 手機或電腦開 `https://yingsioul-art.github.io/chemo-extravasation-xr/test/`，代號輸 `TEST`、選前測、隨便作答到送出。
2. 成績頁最下方應顯示「成績已送出 ✅（試算表第 N 列）」。
3. 回試算表看 `responses` 工作表多一列。**正式試教前把 TEST 那幾列刪掉**。
4. 也可以在瀏覽器直接開 Web App 網址（GET），看到 `{"ok":true,"service":"xr-test"}` 代表部署成功。

## 六、之後改程式碼要注意

- 改了 `Code.gs` 之後要 **部署 → 管理部署作業 → 編輯（鉛筆）→ 版本選「新版本」→ 部署**，網址不變；只按儲存不會生效。
- 若改成「新增部署作業」，網址會變，要重新貼回 `ENDPOINT`。

## 七、試算表欄位（程式自動建）

| 欄 | 內容 |
|---|---|
| 收到時間 | 伺服器收到的時間 |
| 代號 | 學員 4 碼代號 |
| 階段 | 前測／後測 |
| 開始時間、送出時間、作答秒數 | 學員端時間 |
| 總分、滿分 | 答對題數／27 |
| 自學題、③初步處理、④後續處置、⑤紀錄與追蹤 | 各組得分（滿分另欄） |
| Q1_答 … Q27_答 | 學員選的選項代號（**JSON 原始代號，正解一律是 A**；網頁顯示時順序已隨機打亂，這裡記的是原始代號） |
| Q1_對 … Q27_對 | 1＝答對、0＝答錯 |
| submission_id | 每次送出的唯一碼，用來去重（同一份重送不會多一列） |
| 版本、UA、原始JSON | 除錯用 |

分析時：同一代號的前測列與後測列相減即進步分數；`Qn_對` 欄各題平均即答對率。

---

## Code.gs 全文

```javascript
/**
 * 外滲 XR 教材｜前後測成績接收（Web App）
 * POST JSON → 寫入本試算表 responses 工作表一列；GET → 健康檢查。
 * 由 docs/test/index.html 送出；欄位定義見 _AppsScript部署步驟.md 第七節。
 */
var SHEET_NAME = 'responses';
var N_Q = 27;                       // 題數（與 questions.json 一致；題數改了這裡也要改）
var GROUP_KEYS = ['learn', 'handson', 'coach', 'record'];
var GROUP_LABELS = ['自學題', '③初步處理', '④後續處置', '⑤紀錄與追蹤'];

function doGet(e) {
  return json_({ ok: true, service: 'xr-test', time: new Date().toISOString() });
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);                       // 多人同時送出時排隊寫入
    var body = (e && e.postData && e.postData.contents) || '';
    var p = JSON.parse(body);
    if (!p || !p.code || !p.phase) return json_({ ok: false, error: 'missing code/phase' });

    var sh = getSheet_();
    setHeaders(sh);

    // 去重：同一 submission_id 已存在就不再寫
    if (p.submission_id) {
      var last = sh.getLastRow();
      if (last >= 2) {
        var idCol = headerIndex_(sh, 'submission_id');
        var ids = sh.getRange(2, idCol, last - 1, 1).getValues();
        for (var i = 0; i < ids.length; i++) {
          if (String(ids[i][0]) === String(p.submission_id)) return json_({ ok: true, duplicate: true, row: i + 2 });
        }
      }
    }

    var row = buildRow_(p);
    sh.appendRow(row);
    return json_({ ok: true, row: sh.getLastRow() });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  } finally {
    try { lock.releaseLock(); } catch (x) {}
  }
}

/** 標題列：工作表是空的才寫（第一次收到資料時自動建） */
function setHeaders(sh) {
  if (sh.getLastRow() >= 1 && String(sh.getRange(1, 1).getValue()) !== '') return;
  var h = ['收到時間', '代號', '階段', '開始時間', '送出時間', '作答秒數', '總分', '滿分'];
  for (var g = 0; g < GROUP_LABELS.length; g++) h.push(GROUP_LABELS[g], GROUP_LABELS[g] + '_滿分');
  for (var q = 1; q <= N_Q; q++) h.push('Q' + q + '_答');
  for (var q2 = 1; q2 <= N_Q; q2++) h.push('Q' + q2 + '_對');
  h.push('submission_id', '版本', 'UA', '原始JSON');
  sh.getRange(1, 1, 1, h.length).setValues([h]).setFontWeight('bold');
  sh.setFrozenRows(1);
}

function buildRow_(p) {
  var row = [new Date(), String(p.code).toUpperCase(), p.phase_label || p.phase,
             p.started_at || '', p.submitted_at || '', p.duration_sec != null ? p.duration_sec : '',
             p.total != null ? p.total : '', p.max != null ? p.max : ''];
  var groups = p.groups || {};
  for (var g = 0; g < GROUP_KEYS.length; g++) {
    var gg = groups[GROUP_KEYS[g]] || {};
    row.push(gg.score != null ? gg.score : '', gg.max != null ? gg.max : '');
  }
  var byId = {};
  (p.answers || []).forEach(function (a) { byId[a.id] = a; });
  for (var q = 1; q <= N_Q; q++) row.push(byId[q] ? (byId[q].chosen || '') : '');
  for (var q2 = 1; q2 <= N_Q; q2++) row.push(byId[q2] ? (byId[q2].correct ? 1 : 0) : '');
  row.push(p.submission_id || '', p.version || '', p.ua || '', JSON.stringify(p));
  return row;
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) sh = ss.insertSheet(SHEET_NAME);
  return sh;
}

function headerIndex_(sh, name) {
  var h = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  for (var i = 0; i < h.length; i++) if (String(h[i]) === name) return i + 1;
  throw new Error('header not found: ' + name);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

/** 在編輯器手動執行一次可測試寫入（會多一列 TEST，測完刪掉） */
function testPost() {
  var fake = { submission_id: 'test-' + Date.now(), version: 'manual', code: 'TEST', phase: 'pre', phase_label: '前測',
    started_at: '2026-09-26T12:00:00+08:00', submitted_at: '2026-09-26T12:08:00+08:00', duration_sec: 480,
    total: 20, max: 27,
    groups: { learn: { score: 10, max: 12 }, handson: { score: 6, max: 8 }, coach: { score: 2, max: 3 }, record: { score: 2, max: 4 } },
    answers: [] };
  for (var i = 1; i <= N_Q; i++) fake.answers.push({ id: i, chosen: i % 3 ? 'A' : 'B', correct: i % 3 !== 0 });
  var r = doPost({ postData: { contents: JSON.stringify(fake) } });
  Logger.log(r.getContent());
}
```

## 八、網頁端送出方式（給除錯看）

- `fetch(ENDPOINT, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON})`：`text/plain` 屬簡單請求，不會觸發 CORS 預檢；Apps Script 會 302 轉到 `script.googleusercontent.com`，fetch 自動跟隨並讀到 `{ok:true,row:N}`。
- 讀不到回應時，網頁自動改 `mode:'no-cors'` 再送一次（伺服器端以 `submission_id` 去重），並提供「重新送出成績」按鈕。
- 送出失敗的成績會留在學員手機的 localStorage（`xrtest:pending`），成績頁截圖也可作備援。

---

## 九、v2（2026-09-28 22:07 部署第 2 版，網址不變）

- 程式碼改為 `_Code_v2.gs`（本資料夾）：依標題名稱寫入、缺的欄位自動補在最右邊。
- 新增欄位：開放建議、使用版本、未用另一版原因、版本偏好、自我效能平均、SE1–SE10、2D_*／VR_* 滿意度各題。
- 已執行 `backfill()` 一次，從「原始JSON」回填舊列（173 格）。
- 代號欄改存文字（保留開頭的 0）。

## 八、v3：加「使用者後台紀錄表」（2026-09-30，⏸ 待使用者部署）

前端已上線並開始送 `type:"activity"`；**在後端更新成 v3 之前，這些紀錄會被舊版（v2）拒收、不會進試算表**（前後測成績不受影響）。

1. 開試算表「外滲XR_前後測成績」→ 擴充功能 → Apps Script（專案「外滲XR成績」）。
2. 把 `Code.gs` 全部內容換成本資料夾 `_Code_v3.gs` 全文 → 儲存。
3. 部署 → **管理部署作業** → 選現有那一個 → 右上鉛筆（編輯）→ 版本選 **新版本** → 部署（網址不變，不用改網頁）。若跳授權就照第三節第 4 步允許。
4. 驗證：瀏覽器開 Web App 網址，看到 `"v":3` 就成功。之後打開網站、首頁輸入測試代號 `0000_0101` 走幾步，試算表會多出 `activity` 工作表；測完刪掉測試列。
