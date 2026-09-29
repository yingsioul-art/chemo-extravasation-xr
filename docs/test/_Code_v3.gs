/**
 * 外滲 XR 教材｜前後測成績接收（Web App）v3（2026-09-30）
 * v3 新增：payload.type==='activity' → 使用者後台紀錄表（工作表 activity，可批次 events[]）；前後測寫入不變。
 * v2 變更：欄位改「依標題名稱寫入」，標題列缺的欄位自動補在最右邊；
 *          新增自我效能 SE1–SE10、課程滿意度（V0／V_WHY／V_PREF／OPEN＝開放建議／2D_*／VR_*）。
 * 已有資料可在編輯器執行 backfill() 一次，從「原始JSON」欄回填新欄位。
 */
var SHEET_NAME = 'responses';
var N_Q = 27;
var GROUP_KEYS = ['learn', 'handson', 'coach', 'record'];
var GROUP_LABELS = ['自學題', '③初步處理', '④後續處置', '⑤紀錄與追蹤'];
var SE_KEYS = ['SE1','SE2','SE3','SE4','SE5','SE6','SE7','SE8','SE9','SE10'];
var SAT_ITEMS = ['PU1','PU2','EU1','EU2','BI1','A1','R1','R2','C1','S1','M1','M2'];
var SAT_VR_ONLY = ['IM1','IM2'];

function headers_() {
  var h = ['收到時間', '代號', '階段', '開始時間', '送出時間', '作答秒數', '總分', '滿分'];
  for (var g = 0; g < GROUP_LABELS.length; g++) h.push(GROUP_LABELS[g], GROUP_LABELS[g] + '_滿分');
  for (var q = 1; q <= N_Q; q++) h.push('Q' + q + '_答');
  for (var q2 = 1; q2 <= N_Q; q2++) h.push('Q' + q2 + '_對');
  h.push('submission_id', '版本', 'UA', '原始JSON');
  // v2 新增
  h.push('開放建議', '使用版本', '未用另一版原因', '版本偏好', '自我效能平均');
  SE_KEYS.forEach(function (k) { h.push(k); });
  ['2D', 'VR'].forEach(function (v) {
    SAT_ITEMS.forEach(function (k) { h.push(v + '_' + k); });
    if (v === 'VR') SAT_VR_ONLY.forEach(function (k) { h.push('VR_' + k); });
  });
  return h;
}

function doGet(e) { return json_({ ok: true, service: 'xr-test', v: 3, time: new Date().toISOString() }); }

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var p = JSON.parse((e && e.postData && e.postData.contents) || '');
    if (p && p.type === 'activity') return json_(writeActivity_(p));
    if (!p || !p.code || !p.phase) return json_({ ok: false, error: 'missing code/phase' });
    var sh = getSheet_();
    var hdr = ensureHeaders_(sh);
    if (p.submission_id) {
      var idCol = hdr.indexOf('submission_id') + 1, last = sh.getLastRow();
      if (last >= 2) {
        var ids = sh.getRange(2, idCol, last - 1, 1).getValues();
        for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === String(p.submission_id)) return json_({ ok: true, duplicate: true, row: i + 2 });
      }
    }
    var m = rowMap_(p, true);
    sh.appendRow(hdr.map(function (k) { return m.hasOwnProperty(k) ? m[k] : ''; }));
    return json_({ ok: true, row: sh.getLastRow() });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  } finally { try { lock.releaseLock(); } catch (x) {} }
}

/** 標題列：空的就整列寫入；已有標題就把缺的欄位補在最右邊（不動既有欄位順序） */
function ensureHeaders_(sh) {
  var want = headers_();
  var lastCol = sh.getLastColumn();
  var have = lastCol ? sh.getRange(1, 1, 1, lastCol).getValues()[0].map(String) : [];
  if (!have.length || have[0] === '') {
    sh.getRange(1, 1, 1, want.length).setValues([want]).setFontWeight('bold'); sh.setFrozenRows(1); return want;
  }
  var add = want.filter(function (k) { return have.indexOf(k) < 0; });
  if (add.length) { sh.getRange(1, have.length + 1, 1, add.length).setValues([add]).setFontWeight('bold'); have = have.concat(add); }
  return have;
}

/** 一筆送出資料 → {欄名: 值} */
function rowMap_(p, withTime) {
  var m = {};
  if (withTime) m['收到時間'] = new Date();
  m['代號'] = "'" + String(p.code).toUpperCase();   // 前導單引號＝文字，保留開頭的 0
  m['階段'] = p.phase_label || p.phase; m['開始時間'] = p.started_at || ''; m['送出時間'] = p.submitted_at || '';
  m['作答秒數'] = p.duration_sec != null ? p.duration_sec : ''; m['總分'] = p.total != null ? p.total : ''; m['滿分'] = p.max != null ? p.max : '';
  var groups = p.groups || {};
  for (var g = 0; g < GROUP_KEYS.length; g++) { var gg = groups[GROUP_KEYS[g]] || {}; m[GROUP_LABELS[g]] = gg.score != null ? gg.score : ''; m[GROUP_LABELS[g] + '_滿分'] = gg.max != null ? gg.max : ''; }
  (p.answers || []).forEach(function (a) { m['Q' + a.id + '_答'] = a.chosen || ''; m['Q' + a.id + '_對'] = a.correct ? 1 : 0; });
  m['submission_id'] = p.submission_id || ''; m['版本'] = p.version || ''; m['UA'] = p.ua || ''; m['原始JSON'] = JSON.stringify(p);
  var se = p.self_efficacy || {};
  SE_KEYS.forEach(function (k) { if (se[k] != null) m[k] = se[k]; });
  if (p.se_mean != null) m['自我效能平均'] = p.se_mean;
  var s = p.satisfaction || {};
  var V0L = { '2d': '只有2D', 'vr': '只有VR', 'both': '兩個都用', 'none': '都沒用' };
  if (s.V0) m['使用版本'] = V0L[s.V0] || s.V0;
  if (s.V_WHY) m['未用另一版原因'] = s.V_WHY;
  if (s.V_PREF) m['版本偏好'] = s.V_PREF;
  if (s.OPEN) m['開放建議'] = s.OPEN;
  Object.keys(s).forEach(function (k) { if (/^(2D|VR)_/.test(k)) m[k] = s[k]; });
  return m;
}

/** 在編輯器手動執行一次：依「原始JSON」回填 v2 新欄位（不覆蓋已有值） */
function backfill() {
  var sh = getSheet_(); var hdr = ensureHeaders_(sh); var last = sh.getLastRow();
  if (last < 2) return;
  var rng = sh.getRange(2, 1, last - 1, hdr.length); var vals = rng.getValues();
  var jc = hdr.indexOf('原始JSON'); var n = 0;
  vals.forEach(function (row) {
    var p; try { p = JSON.parse(row[jc]); } catch (e) { return; }
    var m = rowMap_(p, false);
    hdr.forEach(function (k, i) { if ((row[i] === '' || row[i] == null) && m.hasOwnProperty(k) && k !== '代號') { row[i] = m[k]; n++; } });
  });
  rng.setValues(vals); Logger.log('backfilled cells: ' + n);
}

function getSheet_() { var ss = SpreadsheetApp.getActiveSpreadsheet(); return ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME); }
function json_(obj) { return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON); }

/* ===== v3：使用者後台紀錄表（activity） ===== */
var ACT_SHEET = 'activity';
var ACT_HDR = ['收到時間', '事件時間', '代號', '頁面', '動作', '項目', '選擇', '對錯', '嘗試次數', '停留秒數', '數值', '詳細', 'session_id', '裝置', '方向', '頭顯', '事件ID'];
function writeActivity_(p) {
  var evs = (p.events || []).slice(0, 500);
  if (!evs.length) return { ok: true, n: 0 };
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(ACT_SHEET) || ss.insertSheet(ACT_SHEET);
  if (sh.getLastRow() === 0) { sh.getRange(1, 1, 1, ACT_HDR.length).setValues([ACT_HDR]).setFontWeight('bold'); sh.setFrozenRows(1); }
  // 去重：同一批最後 2000 筆的事件ID
  var last = sh.getLastRow(), seen = {};
  if (last >= 2) { var from = Math.max(2, last - 1999); sh.getRange(from, ACT_HDR.length, last - from + 1, 1).getValues().forEach(function (r) { seen[String(r[0])] = 1; }); }
  var now = new Date(), rows = [];
  evs.forEach(function (ev) {
    if (!ev || seen[String(ev.eid)]) return; seen[String(ev.eid)] = 1;
    var ok = ev.correct === true ? 1 : ev.correct === false ? 0 : '';
    rows.push([now, ev.t || '', ev.code ? "'" + String(ev.code).toUpperCase() : '', ev.page || '', ev.action || '', ev.item != null ? String(ev.item) : '',
      ev.choice != null ? String(ev.choice) : '', ok, ev.attempt != null ? ev.attempt : '', ev.dwell != null ? ev.dwell : '', ev.value != null ? ev.value : '',
      ev.extra ? JSON.stringify(ev.extra) : '', ev.sid || '', ev.dev || '', ev.orient || '', ev.xr ? 1 : 0, ev.eid || '']);
  });
  if (rows.length) sh.getRange(sh.getLastRow() + 1, 1, rows.length, ACT_HDR.length).setValues(rows);
  return { ok: true, n: rows.length };
}
