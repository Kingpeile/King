/* ════════════════════════════════════════
   数据配置
════════════════════════════════════════ */
const TYPE_CONFIG = {
  weight:  {
    name:'体重', emoji:'⚖️', color:'#FFE566',
    fields:[{key:'weight', label:'体重', unit:'kg', placeholder:'68.0', type:'number', step:'0.1'}],
    format: d => `${d.weight}kg`,
    eval:   d => { const v=+d.weight; return v<45||v>120?{s:'warning',t:'注意'}:{s:'normal',t:'正常'}; },
    main:   d => +d.weight,
  },
  bp: {
    name:'血压', emoji:'💗', color:'#FFB5C8',
    fields:[
      {key:'systolic',  label:'收缩压', unit:'mmHg', placeholder:'120', type:'number'},
      {key:'diastolic', label:'舒张压', unit:'mmHg', placeholder:'80',  type:'number'},
    ],
    format: d => `${d.systolic}/${d.diastolic}`,
    eval:   d => { const s=+d.systolic; return s<=120?{s:'normal',t:'正常'}:s<=139?{s:'warning',t:'偏高'}:{s:'danger',t:'高'}; },
    main:   d => +d.systolic,
  },
  glucose: {
    name:'血糖', emoji:'🩸', color:'#FF9B6A',
    fields:[
      {key:'glucose', label:'血糖值',  unit:'mmol/L', placeholder:'5.6', type:'number', step:'0.1'},
      {key:'timing',  label:'检测时间', unit:'',       placeholder:'空腹 / 餐后2h', type:'text'},
    ],
    format: d => `${d.glucose} mmol/L`,
    eval:   d => { const g=+d.glucose; return g<=6.1?{s:'normal',t:'正常'}:g<=7?{s:'warning',t:'偏高'}:{s:'danger',t:'过高'}; },
    main:   d => +d.glucose,
  },
  sleep: {
    name:'睡眠', emoji:'😴', color:'#B5D4EA',
    fields:[
      {key:'hours',   label:'时长',   unit:'h',       placeholder:'7.5', type:'number', step:'0.5'},
      {key:'quality', label:'质量',   unit:'分(1-10)', placeholder:'8',   type:'number'},
    ],
    format: d => `${d.hours}h`,
    eval:   d => +d.hours>=7?{s:'normal',t:'良好'}:{s:'warning',t:'不足'},
    main:   d => +d.hours,
  },
  steps: {
    name:'步数', emoji:'👟', color:'#B5EAD7',
    fields:[{key:'steps', label:'步数', unit:'步', placeholder:'8000', type:'number'}],
    format: d => `${(+d.steps).toLocaleString()}步`,
    eval:   d => +d.steps>=8000?{s:'normal',t:'达标'}:{s:'warning',t:'偏少'},
    main:   d => +d.steps,
  },
  water: {
    name:'饮水', emoji:'💧', color:'#D4B5EA',
    fields:[{key:'water', label:'饮水量', unit:'ml', placeholder:'1500', type:'number'}],
    format: d => `${d.water}ml`,
    eval:   d => +d.water>=1500?{s:'normal',t:'达标'}:{s:'warning',t:'不足'},
    main:   d => +d.water,
  },
};

const YEAR_COLORS = ['#FF9B6A','#FFE566','#B5EAD7','#B5D4EA','#FFB5C8','#D4B5EA'];
const REPORT_METRICS = ['血压(收缩压)','血糖(空腹)','总胆固醇','BMI','尿酸','血红蛋白'];

/* ════════════════════════════════════════
   存储
════════════════════════════════════════ */
const Store = {
  getRecords: type => JSON.parse(localStorage.getItem(`hr_${type}`) || '[]'),
  addRecord(type, date, data) {
    const list = this.getRecords(type);
    list.unshift({_id: Date.now().toString(), type, date, data});
    localStorage.setItem(`hr_${type}`, JSON.stringify(list.slice(0, 500)));
  },
  getReports: () => JSON.parse(localStorage.getItem('health_reports') || '[]'),
  saveReports: list => localStorage.setItem('health_reports', JSON.stringify(list)),
  getProfile: () => JSON.parse(localStorage.getItem('user_profile') || '{}'),
  saveProfile: p => localStorage.setItem('user_profile', JSON.stringify(p)),
};

/* ════════════════════════════════════════
   路由
════════════════════════════════════════ */
let currentPage = 'home';

function switchPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
  document.getElementById(`page-${name}`).classList.add('active');
  document.getElementById(`tab-${name}`).classList.add('active');
  currentPage = name;
  const handlers = {home: renderHome, record: renderRecord, trends: renderTrends, reports: renderReports, profile: renderProfile};
  handlers[name] && handlers[name]();
}

function goRecordType(type) {
  activeRecordType = type;
  switchPage('record');
}

/* ════════════════════════════════════════
   首页
════════════════════════════════════════ */
function renderHome() {
  const h = new Date().getHours();
  document.getElementById('greeting').textContent =
    h < 12 ? '早上好 ☀️' : h < 18 ? '下午好 🌤' : '晚上好 🌙';
  const now = new Date();
  document.getElementById('today-date').textContent =
    `${now.getFullYear()}年${now.getMonth()+1}月${now.getDate()}日`;

  let score = 100;
  const quickMap = {weight:'q-weight', steps:'q-steps', sleep:'q-sleep', water:'q-water'};
  Object.keys(quickMap).forEach(type => {
    const records = Store.getRecords(type);
    if (records.length) {
      const ev = TYPE_CONFIG[type].eval(records[0].data);
      if (ev.s === 'warning') score -= 8;
      if (ev.s === 'danger')  score -= 15;
      document.getElementById(quickMap[type]).textContent = TYPE_CONFIG[type].format(records[0].data);
    }
  });
  score = Math.max(0, Math.min(100, score));
  document.getElementById('health-score').textContent = score;
  document.getElementById('score-bar').style.width = score + '%';
  document.getElementById('score-tip').textContent =
    score >= 90 ? '状态很棒，继续保持 🌟' :
    score >= 75 ? '整体不错，注意部分指标 💪' : '有几项需要关注，多留意 🌱';

  const container = document.getElementById('recent-metrics');
  const types = ['weight','bp','glucose'];
  const colorMap = {weight:'#FFE566', bp:'#FFB5C8', glucose:'#FF9B6A'};
  const nameMap  = {weight:'体重', bp:'血压', glucose:'血糖'};
  const rows = types.map(type => {
    const r = Store.getRecords(type)[0];
    if (!r) return '';
    const ev = TYPE_CONFIG[type].eval(r.data);
    return `<div class="card metric-row">
      <div class="metric-left">
        <div class="metric-dot" style="background:${colorMap[type]}"></div>
        <div><div class="metric-name">${nameMap[type]}</div><div class="metric-date">${r.date}</div></div>
      </div>
      <div class="metric-right">
        <div class="metric-value">${TYPE_CONFIG[type].format(r.data)}</div>
        <span class="badge badge-${ev.s}">${ev.t}</span>
      </div>
    </div>`;
  }).join('');
  container.innerHTML = rows || '<div class="empty-hint">去记录页添加数据吧 🌱</div>';
}

/* ════════════════════════════════════════
   记录页
════════════════════════════════════════ */
let activeRecordType = 'weight';

function renderRecord() {
  // 类型标签
  const tabs = document.getElementById('type-tabs');
  tabs.innerHTML = Object.entries(TYPE_CONFIG).map(([type, c]) =>
    `<button class="type-chip ${type===activeRecordType?'active':''}"
      style="${type===activeRecordType?`background:${c.color};color:#2D2D2D`:''}"
      onclick="switchRecordType('${type}')">${c.emoji} ${c.name}</button>`
  ).join('');

  renderRecordForm();
  renderHistory();
}

function switchRecordType(type) {
  activeRecordType = type;
  renderRecord();
}

function renderRecordForm() {
  const c = TYPE_CONFIG[activeRecordType];
  document.getElementById('form-type-name').textContent = c.name + '记录';

  // 日期默认今天
  if (!document.getElementById('record-date').value) {
    document.getElementById('record-date').valueAsDate = new Date();
  }

  document.getElementById('form-fields').innerHTML = c.fields.map(f => `
    <div class="form-row" style="padding:6px 0">
      <span class="form-label">${f.label}</span>
      <div class="form-input-wrap">
        <input class="form-field-input" id="field-${f.key}"
          type="${f.type}" step="${f.step||1}"
          placeholder="${f.placeholder}">
        <span class="form-unit">${f.unit}</span>
      </div>
    </div>
    <div class="divider"></div>
  `).join('');
}

function saveRecord() {
  const c = TYPE_CONFIG[activeRecordType];
  const data = {};
  for (const f of c.fields) {
    const val = document.getElementById(`field-${f.key}`)?.value?.trim();
    if (!val) { alert(`请填写 ${f.label}`); return; }
    data[f.key] = val;
  }
  data.note = document.getElementById('record-note').value;
  const date = document.getElementById('record-date').value;
  Store.addRecord(activeRecordType, date, data);

  // 清空
  c.fields.forEach(f => { const el = document.getElementById(`field-${f.key}`); if(el) el.value=''; });
  document.getElementById('record-note').value = '';

  showToast('保存成功 🎉');
  renderHistory();
}

function renderHistory() {
  const type = activeRecordType;
  const records = Store.getRecords(type);
  const el = document.getElementById('history-list');
  if (!records.length) { el.innerHTML = '<div class="empty-hint">暂无记录，快来添加吧 🌱</div>'; return; }
  el.innerHTML = records.map(r => {
    const ev = TYPE_CONFIG[type].eval(r.data);
    const note = r.data.note ? `<br><span style="font-size:12px;color:#999">${r.data.note}</span>` : '';
    return `<div class="card metric-row">
      <div class="metric-left">
        <div class="metric-dot" style="background:${TYPE_CONFIG[type].color}"></div>
        <div><div class="metric-name">${r.date}</div>${note}</div>
      </div>
      <div class="metric-right">
        <div class="metric-value">${TYPE_CONFIG[type].format(r.data)}</div>
        <span class="badge badge-${ev.s}">${ev.t}</span>
      </div>
    </div>`;
  }).join('');
}

/* ════════════════════════════════════════
   趋势页
════════════════════════════════════════ */
let activeTrendType  = 'weight';
let activeTrendRange = '3m';

function renderTrends() {
  // 类型标签
  document.getElementById('trend-tabs').innerHTML = Object.entries(TYPE_CONFIG).map(([type, c]) =>
    `<button class="type-chip ${type===activeTrendType?'active':''}"
      style="${type===activeTrendType?`background:${c.color}`:''}"
      onclick="switchTrend('${type}')">${c.emoji} ${c.name}</button>`
  ).join('');

  // 时间范围
  const ranges = [{v:'1m',l:'近1月'},{v:'3m',l:'近3月'},{v:'6m',l:'近半年'},{v:'1y',l:'近1年'}];
  document.getElementById('range-tabs').innerHTML = ranges.map(r =>
    `<button class="range-btn ${r.v===activeTrendRange?'active':''}" onclick="switchRange('${r.v}')">${r.l}</button>`
  ).join('');
  document.getElementById('chart-range-label').textContent = ranges.find(r=>r.v===activeTrendRange).l;

  loadTrendData();
}

function switchTrend(type) { activeTrendType = type; renderTrends(); }
function switchRange(val)  { activeTrendRange = val;  renderTrends(); }

function getStartDate() {
  const d = new Date();
  const map = {'1m':1,'3m':3,'6m':6,'1y':12};
  d.setMonth(d.getMonth() - map[activeTrendRange]);
  return d.toISOString().slice(0,10);
}

function loadTrendData() {
  const type = activeTrendType;
  const start = getStartDate();
  const all = Store.getRecords(type);
  const records = all.filter(r => r.date >= start);

  const statsEl = document.getElementById('trend-stats');
  const listEl  = document.getElementById('trend-list');

  if (!records.length) {
    statsEl.innerHTML = '';
    listEl.innerHTML  = '<div class="empty-hint">暂无数据，去记录页添加吧 📊</div>';
    drawChart([], TYPE_CONFIG[type].color);
    document.getElementById('chart-labels').innerHTML = '';
    return;
  }

  const cfg  = TYPE_CONFIG[type];
  const vals = records.map(r => cfg.main(r.data)).filter(v => !isNaN(v));
  const min  = Math.min(...vals), max = Math.max(...vals);
  const avg  = (vals.reduce((a,b)=>a+b,0) / vals.length).toFixed(1);

  statsEl.innerHTML = [
    {label:'最高', value: max},
    {label:'平均', value: avg},
    {label:'最低', value: min},
  ].map(s => `<div class="card stat-card"><div class="stat-value">${s.value}</div><div class="stat-label">${s.label}</div></div>`).join('');

  // 图表（最近14条，时间升序）
  const recent = [...records].reverse().slice(-14);
  drawChart(recent.map(r => cfg.main(r.data)), cfg.color);
  document.getElementById('chart-labels').innerHTML =
    recent.map(r => `<span class="chart-label">${r.date.slice(5)}</span>`).join('');

  // 列表
  listEl.innerHTML = records.map(r => {
    const ev = cfg.eval(r.data);
    return `<div class="card metric-row">
      <div class="metric-left">
        <div class="metric-dot" style="background:${cfg.color}"></div>
        <div><div class="metric-name">${r.date}</div></div>
      </div>
      <div class="metric-right">
        <div class="metric-value">${cfg.format(r.data)}</div>
        <span class="badge badge-${ev.s}">${ev.t}</span>
      </div>
    </div>`;
  }).join('');
}

function drawChart(values, color) {
  const canvas = document.getElementById('trend-chart');
  const ctx    = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0,0,W,H);

  if (!values.length) return;

  const pad  = {top:20, right:16, bottom:16, left:16};
  const cW   = W - pad.left - pad.right;
  const cH   = H - pad.top  - pad.bottom;
  const min  = Math.min(...values) * 0.95;
  const max  = Math.max(...values) * 1.05 || 1;
  const n    = values.length;

  const px = i => pad.left + (i / (n-1 || 1)) * cW;
  const py = v => pad.top  + cH - ((v - min) / (max - min || 1)) * cH;

  // 渐变填充
  const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + cH);
  grad.addColorStop(0, color + 'AA');
  grad.addColorStop(1, color + '11');

  ctx.beginPath();
  values.forEach((v,i) => i===0 ? ctx.moveTo(px(i),py(v)) : ctx.lineTo(px(i),py(v)));
  ctx.lineTo(px(n-1), pad.top+cH);
  ctx.lineTo(px(0),   pad.top+cH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // 折线
  ctx.beginPath();
  values.forEach((v,i) => i===0 ? ctx.moveTo(px(i),py(v)) : ctx.lineTo(px(i),py(v)));
  ctx.strokeStyle = color;
  ctx.lineWidth   = 3;
  ctx.lineJoin    = 'round';
  ctx.stroke();

  // 数据点
  values.forEach((v,i) => {
    ctx.beginPath();
    ctx.arc(px(i), py(v), 5, 0, Math.PI*2);
    ctx.fillStyle   = '#fff';
    ctx.strokeStyle = color;
    ctx.lineWidth   = 2.5;
    ctx.fill();
    ctx.stroke();
  });
}

/* ════════════════════════════════════════
   报告页
════════════════════════════════════════ */
function renderReports() {
  const reports = Store.getReports();
  const years   = [...new Set(reports.map(r=>r.date?.slice(0,4)).filter(Boolean).map(Number))];
  const yearSpan = years.length>1 ? Math.max(...years)-Math.min(...years)+1 : years.length;
  const abnormal = reports.reduce((s,r)=>s+(r.abnormalItems?.length||0),0);

  document.getElementById('report-summary').innerHTML = [
    {num: reports.length, label:'体检报告'},
    {num: yearSpan+'年',  label:'健康记录'},
    {num: abnormal,       label:'异常指标'},
  ].map(s=>`<div class="card summary-card"><div class="summary-num">${s.num}</div><div class="summary-label">${s.label}</div></div>`).join('');

  const el = document.getElementById('report-list');
  if (!reports.length) {
    el.innerHTML = '<div class="empty-hint">📋<br>还没有报告，点上方录入第一份吧！</div>';
    return;
  }
  el.innerHTML = reports.map((r,i) => {
    const color  = YEAR_COLORS[i % YEAR_COLORS.length];
    const ab     = r.abnormalItems?.length || 0;
    const abHtml = ab > 0
      ? `<div class="report-alert"><span class="report-alert-num">${ab}</span><span class="report-alert-text">异常</span></div>`
      : `<span class="report-ok">✓ 正常</span>`;
    return `<div class="card report-item">
      <div class="report-left">
        <div class="report-badge" style="background:${color}">${(r.date||'').slice(0,4)}</div>
        <div>
          <div class="report-name">${r.title||'体检报告'}</div>
          <div class="report-meta">${r.date||''} · ${r.hospital||'未知医院'}</div>
        </div>
      </div>
      <div class="report-right">${abHtml}<span class="report-arrow">›</span></div>
    </div>`;
  }).join('');
}

function addReportManual() {
  // 构建指标输入字段
  document.getElementById('report-metric-fields').innerHTML =
    REPORT_METRICS.map(name =>
      `<div class="modal-field">
        <label>${name}</label>
        <input type="number" step="0.1" id="rm-${name.replace(/[()]/g,'')}" placeholder="数值">
      </div>`
    ).join('');
  document.getElementById('rp-date').valueAsDate = new Date();
  document.getElementById('rp-hospital').value = '';
  document.getElementById('rp-abnormal').value = '';
  document.getElementById('report-modal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('report-modal').style.display = 'none';
}

function saveReport() {
  const date     = document.getElementById('rp-date').value;
  const hospital = document.getElementById('rp-hospital').value.trim() || '未填写';
  const abnStr   = document.getElementById('rp-abnormal').value.trim();
  const abnormalItems = abnStr ? abnStr.split(/[,，]/).map(s=>s.trim()).filter(Boolean) : [];

  const metrics = {};
  REPORT_METRICS.forEach(name => {
    const val = document.getElementById(`rm-${name.replace(/[()]/g,'')}`)?.value;
    if (val) metrics[name] = parseFloat(val);
  });

  const list = Store.getReports();
  list.unshift({
    _id: Date.now().toString(),
    title: `${(date||'').slice(0,4)}年体检报告`,
    date, hospital, abnormalItems, metrics,
  });
  Store.saveReports(list);
  closeModal();
  showToast('报告已保存 🎉');
  renderReports();
}

/* ════════════════════════════════════════
   我的
════════════════════════════════════════ */
function renderProfile() {
  const p = Store.getProfile();
  document.getElementById('p-height').value = p.height || '';
  document.getElementById('p-birth').value  = p.birth  || '';
  document.getElementById('p-checkup').value = p.checkup || '';
  document.getElementById('g-male').classList.toggle('active',   p.gender==='male');
  document.getElementById('g-female').classList.toggle('active', p.gender==='female');
  window._gender = p.gender || '';
}

function setGender(val) {
  window._gender = val;
  document.getElementById('g-male').classList.toggle('active',   val==='male');
  document.getElementById('g-female').classList.toggle('active', val==='female');
}

function saveProfile() {
  Store.saveProfile({
    height:  document.getElementById('p-height').value,
    birth:   document.getElementById('p-birth').value,
    gender:  window._gender || '',
    checkup: document.getElementById('p-checkup').value,
  });
  showToast('已保存 ✓');
}

function exportData() {
  const data = {};
  Object.keys(TYPE_CONFIG).forEach(t => { data[t] = Store.getRecords(t); });
  data.reports = Store.getReports();
  data.profile = Store.getProfile();
  const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `健康数据_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
}

function clearConfirm() {
  if (confirm('确定要清除全部数据吗？此操作不可撤销。')) {
    Object.keys(TYPE_CONFIG).forEach(t => localStorage.removeItem(`hr_${t}`));
    localStorage.removeItem('health_reports');
    localStorage.removeItem('user_profile');
    showToast('已清除');
    renderProfile();
  }
}

/* ════════════════════════════════════════
   工具
════════════════════════════════════════ */
function showToast(msg) {
  let t = document.getElementById('toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast';
    t.style.cssText = 'position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#2D2D2D;color:#fff;padding:10px 22px;border-radius:100px;font-size:14px;z-index:999;transition:opacity .3s;white-space:nowrap;';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.opacity = '1';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.opacity = '0'; }, 2000);
}

/* ════════════════════════════════════════
   初始化
════════════════════════════════════════ */
renderHome();
