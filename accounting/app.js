/* ─── 数据模型 & 本地存储 ─────────────────────────────────── */

const STORAGE_KEY = 'yousu_assets';
const CAT_KEY     = 'yousu_categories';

const DEFAULT_CATEGORIES = ['吃饭家伙', '创作辅助', '代步工具', '居家工作室', '数码产品', '运动健康'];

const EMOJIS = [
  '📱','💻','🖥','⌨️','🖱','🎮','📷','🎧',
  '🚗','🚲','🛵','✈️','🚢','🏠','🛋','🪑',
  '👔','👟','🧳','⌚️','💍','👓','🎒','🛍',
  '📚','🎸','🎹','🎨','🖊','📐','🔧','🔨',
  '🍳','☕️','🍷','🧸','🌿','💡','📦','🎁',
];

function loadAssets() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
  catch { return []; }
}

function saveAssets(list) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function loadCategories() {
  try {
    const saved = JSON.parse(localStorage.getItem(CAT_KEY));
    return saved && saved.length ? saved : [...DEFAULT_CATEGORIES];
  } catch { return [...DEFAULT_CATEGORIES]; }
}

function saveCategories(list) {
  localStorage.setItem(CAT_KEY, JSON.stringify(list));
}

function genId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

/* ─── 工具函数 & 计算 ─────────────────────────────────────── */

function daysSince(dateStr) {
  const start = new Date(dateStr);
  start.setHours(0, 0, 0, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.max(1, Math.floor((today - start) / 86400000));
}

function calcAsset(a) {
  const daysUsed    = daysSince(a.purchaseDate);
  const dailyCost   = a.purchasePrice / daysUsed;
  const daysLeft    = Math.max(0, a.expectedLifespanDays - daysUsed);
  const progress    = Math.min(100, (daysUsed / a.expectedLifespanDays) * 100);
  return { daysUsed, dailyCost, daysLeft, progress };
}

function fmtMoney(n) {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtNum(n) {
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
}

function statusLabel(s) {
  return { active: '服役中', retired: '已退役', sold: '已卖出' }[s] || s;
}

function statusBadgeClass(s) {
  return { active: 'badge-active', retired: 'badge-retired', sold: 'badge-sold' }[s] || '';
}

function showToast(msg) {
  let t = document.querySelector('.toast');
  if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 2000);
}

/* ─── 全局状态 ───────────────────────────────────────────── */

const state = {
  assets:      loadAssets(),
  categories:  loadCategories(),
  activeTab:   'all',       // category tab
  statusFilter:'all',       // all | active | retired | sold
  sortBy:      'date_desc', // date_desc | date_asc | cost_desc | cost_asc | price_desc
  searchQuery: '',
  currentView: 'home',      // home | stats | settings
  editingId:   null,        // asset id being edited, null = add new
  detailId:    null,        // asset id shown in detail sheet
};

/* ─── 主页渲染 ───────────────────────────────────────────── */

function getSummary() {
  const active  = state.assets.filter(a => a.status === 'active');
  const retired = state.assets.filter(a => a.status === 'retired');
  const sold    = state.assets.filter(a => a.status === 'sold');
  const total   = state.assets.length;
  const totalValue   = state.assets.reduce((s, a) => s + a.purchasePrice, 0);
  const totalDaily   = active.reduce((s, a) => s + calcAsset(a).dailyCost, 0);
  return { active: active.length, retired: retired.length, sold: sold.length, total, totalValue, totalDaily };
}

function getFilteredAssets() {
  let list = [...state.assets];
  if (state.activeTab !== 'all')     list = list.filter(a => a.category === state.activeTab);
  if (state.statusFilter !== 'all')  list = list.filter(a => a.status === state.statusFilter);
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    list = list.filter(a => a.name.toLowerCase().includes(q) || a.category.toLowerCase().includes(q));
  }
  switch (state.sortBy) {
    case 'date_asc':   list.sort((a,b) => a.purchaseDate.localeCompare(b.purchaseDate)); break;
    case 'cost_desc':  list.sort((a,b) => calcAsset(b).dailyCost - calcAsset(a).dailyCost); break;
    case 'cost_asc':   list.sort((a,b) => calcAsset(a).dailyCost - calcAsset(b).dailyCost); break;
    case 'price_desc': list.sort((a,b) => b.purchasePrice - a.purchasePrice); break;
    default:           list.sort((a,b) => b.purchaseDate.localeCompare(a.purchaseDate));
  }
  return list;
}

function renderHome() {
  const sum = getSummary();
  const filtered = getFilteredAssets();
  const cats = ['all', ...state.categories];

  const tabsHtml = cats.map(c =>
    `<div class="tab${state.activeTab === c ? ' active' : ''}" data-tab="${c}">${c === 'all' ? '全部' : c}</div>`
  ).join('');

  const pillsHtml = [
    ['all','全部'],['active','服役中'],['retired','已退役'],['sold','已卖出']
  ].map(([v,l]) =>
    `<div class="pill${state.statusFilter === v ? ' active' : ''}" data-status="${v}">${l}</div>`
  ).join('');

  const sortLabels = {
    date_desc:'最新购入', date_asc:'最早购入', cost_desc:'日均最高', cost_asc:'日均最低', price_desc:'价格最高'
  };

  const totalCount   = sum.total || 1;

  const cardsHtml = filtered.length === 0
    ? `<div class="empty-state"><div class="empty-icon">📭</div><p>暂无资产<br>点击右下角 + 添加第一件</p></div>`
    : filtered.map(a => {
        const { daysUsed, dailyCost, daysLeft, progress } = calcAsset(a);
        return `
        <div class="asset-card" data-id="${a.id}">
          <span class="card-status-badge ${statusBadgeClass(a.status)}">${statusLabel(a.status)}</span>
          <span class="card-emoji">${a.emoji || '📦'}</span>
          <div class="card-name">${a.name}</div>
          <div class="card-meta">¥${fmtMoney(a.purchasePrice)} | 已使用 ${daysUsed} 天</div>
          <div class="card-daily">¥${fmtNum(dailyCost)}<span>/天</span></div>
          <div class="card-progress-wrap">
            <div class="card-progress"><div class="card-progress-fill" style="width:${progress}%"></div></div>
            <div class="card-days-left">${daysLeft > 0 ? daysLeft + ' 天 left' : '已超出预期'}</div>
          </div>
        </div>`;
      }).join('');

  const activeCount  = sum.active;
  const retiredCount = sum.retired;
  const soldCount    = sum.sold;

  return `
  <div class="view active" id="view-home">
    <div class="header">
      <div class="header-row">
        <div class="header-title">有数</div>
        <div class="header-icon" id="btn-search-toggle">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
      </div>
    </div>
    <div class="summary-card">
      <div class="summary-title">资产总览<span class="summary-badge">${sum.total}/${sum.total}</span></div>
      <div class="summary-row">
        <div class="summary-col"><div class="summary-label">总资产</div><div class="summary-value"><span>¥</span>${fmtMoney(sum.totalValue)}</div></div>
        <div class="summary-col"><div class="summary-label">日均成本</div><div class="summary-value"><span>¥</span>${fmtNum(sum.totalDaily)}</div></div>
      </div>
      <div class="status-row">
        <div class="status-item"><div class="status-label">服役中 ${activeCount}</div><div class="status-bar"><div class="status-bar-fill bar-active" style="width:${activeCount/totalCount*100}%"></div></div></div>
        <div class="status-item"><div class="status-label">已退役 ${retiredCount}</div><div class="status-bar"><div class="status-bar-fill bar-retired" style="width:${retiredCount/totalCount*100}%"></div></div></div>
        <div class="status-item"><div class="status-label">已卖出 ${soldCount}</div><div class="status-bar"><div class="status-bar-fill bar-sold" style="width:${soldCount/totalCount*100}%"></div></div></div>
      </div>
    </div>
    <div class="tabs-wrap"><div class="tabs" id="category-tabs">${tabsHtml}</div></div>
    <div id="search-bar-container"></div>
    <div class="filter-row">
      ${pillsHtml}
      <div class="filter-actions">
        <div class="filter-btn" id="btn-sort">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="6" y1="12" x2="18" y2="12"/><line x1="9" y1="18" x2="15" y2="18"/></svg>
        </div>
      </div>
    </div>
    <div class="asset-grid" id="asset-grid">${cardsHtml}</div>
  </div>`;
}

/* ─── 统计页渲染 ─────────────────────────────────────────── */

function renderStats() {
  const active = state.assets.filter(a => a.status === 'active');
  const totalValue = state.assets.reduce((s,a) => s + a.purchasePrice, 0);
  const totalDaily = active.reduce((s,a) => s + calcAsset(a).dailyCost, 0);

  // 按分类统计
  const catMap = {};
  state.assets.forEach(a => {
    if (!catMap[a.category]) catMap[a.category] = { count: 0, value: 0, daily: 0 };
    catMap[a.category].count++;
    catMap[a.category].value += a.purchasePrice;
    if (a.status === 'active') catMap[a.category].daily += calcAsset(a).dailyCost;
  });
  const catRows = Object.entries(catMap)
    .sort((a,b) => b[1].value - a[1].value)
    .map(([cat, d]) => `
      <div class="cat-row">
        <span class="cat-icon">📂</span>
        <div class="cat-info">
          <div class="cat-name">${cat}</div>
          <div class="cat-sub">${d.count} 件 · 日均 ¥${fmtNum(d.daily)}</div>
        </div>
        <div class="cat-value">¥${fmtMoney(d.value)}</div>
      </div>`).join('');

  // 日均成本 Top5
  const top5 = active
    .map(a => ({ ...a, daily: calcAsset(a).dailyCost }))
    .sort((a,b) => b.daily - a.daily)
    .slice(0, 5);
  const rankClass = ['gold','silver','bronze'];
  const topRows = top5.map((a, i) => `
    <div class="top-row">
      <div class="top-rank ${rankClass[i] || ''}">${i+1}</div>
      <div class="top-info">
        <div class="top-name">${a.emoji || '📦'} ${a.name}</div>
        <div class="top-meta">¥${fmtMoney(a.purchasePrice)} · ${daysSince(a.purchaseDate)} 天</div>
      </div>
      <div class="top-cost">¥${fmtNum(a.daily)}/天</div>
    </div>`).join('');

  return `
  <div class="view active" id="view-stats">
    <div class="stats-header"><h1>数据统计</h1></div>
    <div class="stats-body">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
        <div class="stats-big-card">
          <div class="stats-big-num">¥${fmtMoney(totalValue)}</div>
          <div class="stats-big-label">总资产价值</div>
        </div>
        <div class="stats-big-card">
          <div class="stats-big-num">¥${fmtNum(totalDaily)}</div>
          <div class="stats-big-label">每日总成本</div>
        </div>
        <div class="stats-big-card">
          <div class="stats-big-num">${state.assets.length}</div>
          <div class="stats-big-label">资产总数</div>
        </div>
        <div class="stats-big-card">
          <div class="stats-big-num">${state.categories.length}</div>
          <div class="stats-big-label">分类数</div>
        </div>
      </div>
      <div>
        <div class="stats-section-title">按分类</div>
        <div class="cat-list">${catRows || '<div style="padding:20px;text-align:center;color:#aaa">暂无数据</div>'}</div>
      </div>
      <div>
        <div class="stats-section-title">日均成本 Top 5</div>
        <div class="top-cost-list">${topRows || '<div style="padding:20px;text-align:center;color:#aaa">暂无服役中资产</div>'}</div>
      </div>
    </div>
  </div>`;
}

/* ─── 设置页渲染 ─────────────────────────────────────────── */

function renderSettings() {
  const catItems = state.categories.map(c => `
    <div class="cat-manage-row">
      <span>${c}</span>
      <button class="cat-manage-del" data-del-cat="${c}">×</button>
    </div>`).join('');

  return `
  <div class="view active" id="view-settings">
    <div class="settings-header"><h1>设置</h1></div>
    <div class="settings-body">
      <div class="settings-section">
        <div class="settings-section-header">分类管理</div>
        <div class="cat-manage-list">${catItems}</div>
        <div class="add-cat-row">
          <input class="add-cat-input" id="new-cat-input" placeholder="新分类名称" maxlength="10">
          <button class="add-cat-btn" id="btn-add-cat">添加</button>
        </div>
      </div>
      <div class="settings-section">
        <div class="settings-section-header">数据</div>
        <div class="settings-row danger" id="btn-clear-all">
          <span class="settings-row-icon">🗑</span>
          <div class="settings-row-text">
            <div class="settings-row-label">清空所有数据</div>
            <div class="settings-row-sub">删除全部资产记录，不可恢复</div>
          </div>
          <span class="settings-row-arrow">›</span>
        </div>
      </div>
      <div style="text-align:center;color:#bbb;font-size:12px;padding:8px">有数 · 让每件物品都值得</div>
    </div>
  </div>`;
}

/* ─── 表单弹窗 ───────────────────────────────────────────── */

function openFormSheet(assetId) {
  state.editingId = assetId || null;
  const a = assetId ? state.assets.find(x => x.id === assetId) : null;
  const catOptions = state.categories.map(c =>
    `<option value="${c}" ${a && a.category === c ? 'selected' : ''}>${c}</option>`
  ).join('');
  const emojiGrid = EMOJIS.map(e =>
    `<div class="emoji-opt${a && a.emoji === e ? ' selected' : ''}" data-emoji="${e}">${e}</div>`
  ).join('');

  const overlay = document.getElementById('sheet-overlay');
  overlay.innerHTML = `
    <div class="sheet" id="form-sheet">
      <div class="sheet-handle"></div>
      <div class="sheet-header">
        <div class="sheet-title">${a ? '编辑资产' : '添加资产'}</div>
        <div class="sheet-close" id="close-form">×</div>
      </div>
      <div class="form">
        <div class="form-group">
          <div class="form-label">选择图标</div>
          <div class="emoji-grid" id="emoji-grid">${emojiGrid}</div>
          <input type="hidden" id="f-emoji" value="${a ? a.emoji : '📦'}">
        </div>
        <div class="form-group">
          <div class="form-label">资产名称</div>
          <input class="form-input" id="f-name" placeholder="例：iPhone 15 Pro" maxlength="30" value="${a ? a.name : ''}">
        </div>
        <div class="form-group">
          <div class="form-label">分类</div>
          <select class="form-select" id="f-cat">
            ${catOptions}
          </select>
        </div>
        <div class="form-row">
          <div class="form-group">
            <div class="form-label">购入价格（¥）</div>
            <input class="form-input" id="f-price" type="number" min="0" step="0.01" placeholder="0.00" value="${a ? a.purchasePrice : ''}">
          </div>
          <div class="form-group">
            <div class="form-label">购入日期</div>
            <input class="form-input" id="f-date" type="date" value="${a ? a.purchaseDate : new Date().toISOString().slice(0,10)}">
          </div>
        </div>
        <div class="form-group">
          <div class="form-label">预计使用寿命（天）</div>
          <input class="form-input" id="f-life" type="number" min="1" placeholder="例：1825（5年）" value="${a ? a.expectedLifespanDays : ''}">
        </div>
        <div class="form-group">
          <div class="form-label">状态</div>
          <select class="form-select" id="f-status">
            <option value="active" ${!a || a.status==='active' ? 'selected' : ''}>服役中</option>
            <option value="retired" ${a && a.status==='retired' ? 'selected' : ''}>已退役</option>
            <option value="sold" ${a && a.status==='sold' ? 'selected' : ''}>已卖出</option>
          </select>
        </div>
        <div class="form-group">
          <div class="form-label">备注（可选）</div>
          <textarea class="form-textarea" id="f-notes" placeholder="颜色、型号、购买渠道…">${a ? (a.notes || '') : ''}</textarea>
        </div>
        <button class="form-btn btn-primary" id="btn-save-asset">${a ? '保存修改' : '添加资产'}</button>
        ${a ? `<div class="btn-gap"></div><button class="form-btn btn-danger" id="btn-delete-asset">删除此资产</button>` : ''}
      </div>
    </div>`;
  overlay.classList.add('open');

  // emoji picker
  overlay.querySelectorAll('.emoji-opt').forEach(el => {
    el.addEventListener('click', () => {
      overlay.querySelectorAll('.emoji-opt').forEach(e => e.classList.remove('selected'));
      el.classList.add('selected');
      document.getElementById('f-emoji').value = el.dataset.emoji;
    });
  });

  document.getElementById('close-form').onclick = closeSheet;
  document.getElementById('btn-save-asset').onclick = saveAsset;
  const delBtn = document.getElementById('btn-delete-asset');
  if (delBtn) delBtn.onclick = deleteAsset;
}

function openDetailSheet(assetId) {
  state.detailId = assetId;
  const a = state.assets.find(x => x.id === assetId);
  if (!a) return;
  const { daysUsed, dailyCost, daysLeft, progress } = calcAsset(a);

  const overlay = document.getElementById('sheet-overlay');
  overlay.innerHTML = `
    <div class="sheet" id="detail-sheet">
      <div class="sheet-handle"></div>
      <div class="sheet-header">
        <div class="sheet-title"></div>
        <div class="sheet-close" id="close-detail">×</div>
      </div>
      <div class="detail-hero">
        <div class="detail-emoji">${a.emoji || '📦'}</div>
        <div class="detail-name">${a.name}</div>
        <div class="detail-cat">${a.category} · <span class="${statusBadgeClass(a.status)}" style="padding:2px 8px;border-radius:10px;font-size:12px">${statusLabel(a.status)}</span></div>
      </div>
      <div class="detail-stats">
        <div class="stat-card"><div class="stat-label">购入价格</div><div class="stat-value">¥${fmtMoney(a.purchasePrice)}</div></div>
        <div class="stat-card"><div class="stat-label">日均成本</div><div class="stat-value green">¥${fmtNum(dailyCost)}</div></div>
        <div class="stat-card"><div class="stat-label">已使用</div><div class="stat-value">${daysUsed} 天</div></div>
        <div class="stat-card"><div class="stat-label">剩余寿命</div><div class="stat-value">${daysLeft > 0 ? daysLeft + ' 天' : '已超出'}</div></div>
      </div>
      <div class="detail-progress">
        <div class="detail-progress-bar"><div class="detail-progress-fill" style="width:${progress}%"></div></div>
        <div class="detail-progress-labels"><span>购入 ${a.purchaseDate}</span><span>${progress.toFixed(1)}%</span></div>
      </div>
      ${a.notes ? `<div class="detail-notes"><p>${a.notes}</p></div>` : ''}
      <div class="detail-actions">
        <button class="form-btn btn-primary" id="btn-edit-from-detail">编辑</button>
      </div>
    </div>`;
  overlay.classList.add('open');
  document.getElementById('close-detail').onclick = closeSheet;
  document.getElementById('btn-edit-from-detail').onclick = () => { closeSheet(); openFormSheet(assetId); };
}

function openSortSheet() {
  const options = [
    ['date_desc','最新购入'],['date_asc','最早购入'],
    ['cost_desc','日均最高'],['cost_asc','日均最低'],['price_desc','价格最高'],
  ];
  const overlay = document.getElementById('sheet-overlay');
  overlay.innerHTML = `
    <div class="sheet">
      <div class="sheet-handle"></div>
      <div class="sheet-header"><div class="sheet-title">排序方式</div><div class="sheet-close" id="close-sort">×</div></div>
      <div class="sort-list">
        ${options.map(([v,l]) => `
          <div class="sort-opt${state.sortBy === v ? ' active' : ''}" data-sort="${v}">
            ${l}${state.sortBy === v ? '<span class="sort-check">✓</span>' : ''}
          </div>`).join('')}
      </div>
    </div>`;
  overlay.classList.add('open');
  document.getElementById('close-sort').onclick = closeSheet;
  overlay.querySelectorAll('.sort-opt').forEach(el => {
    el.addEventListener('click', () => {
      state.sortBy = el.dataset.sort;
      closeSheet();
      renderApp();
    });
  });
}

function closeSheet() {
  const overlay = document.getElementById('sheet-overlay');
  overlay.classList.remove('open');
}

/* ─── 数据操作 ───────────────────────────────────────────── */

function saveAsset() {
  const name  = document.getElementById('f-name').value.trim();
  const price = parseFloat(document.getElementById('f-price').value);
  const date  = document.getElementById('f-date').value;
  const life  = parseInt(document.getElementById('f-life').value);
  const cat   = document.getElementById('f-cat').value;
  const emoji = document.getElementById('f-emoji').value;
  const status= document.getElementById('f-status').value;
  const notes = document.getElementById('f-notes').value.trim();

  if (!name)          { showToast('请填写资产名称'); return; }
  if (!price || price <= 0) { showToast('请填写有效价格'); return; }
  if (!date)          { showToast('请选择购入日期'); return; }
  if (!life || life < 1)   { showToast('请填写预计使用寿命'); return; }

  if (state.editingId) {
    const idx = state.assets.findIndex(a => a.id === state.editingId);
    if (idx !== -1) {
      state.assets[idx] = { ...state.assets[idx], name, purchasePrice: price, purchaseDate: date, expectedLifespanDays: life, category: cat, emoji, status, notes };
    }
    showToast('已更新');
  } else {
    state.assets.unshift({ id: genId(), name, purchasePrice: price, purchaseDate: date, expectedLifespanDays: life, category: cat, emoji, status, notes });
    showToast('已添加');
  }
  saveAssets(state.assets);
  closeSheet();
  renderApp();
}

function deleteAsset() {
  if (!confirm('确认删除这件资产？')) return;
  state.assets = state.assets.filter(a => a.id !== state.editingId);
  saveAssets(state.assets);
  closeSheet();
  showToast('已删除');
  renderApp();
}

/* ─── 事件绑定 ───────────────────────────────────────────── */

function bindHomeEvents() {
  // 分类 tab
  document.querySelectorAll('.tab').forEach(el => {
    el.addEventListener('click', () => { state.activeTab = el.dataset.tab; renderApp(); });
  });
  // 状态筛选
  document.querySelectorAll('.pill').forEach(el => {
    el.addEventListener('click', () => { state.statusFilter = el.dataset.status; renderApp(); });
  });
  // 资产卡片
  document.querySelectorAll('.asset-card').forEach(el => {
    el.addEventListener('click', () => openDetailSheet(el.dataset.id));
  });
  // 搜索按钮
  const searchToggle = document.getElementById('btn-search-toggle');
  if (searchToggle) searchToggle.addEventListener('click', toggleSearch);
  // 排序
  const sortBtn = document.getElementById('btn-sort');
  if (sortBtn) sortBtn.addEventListener('click', openSortSheet);
}

function bindSettingsEvents() {
  // 删除分类
  document.querySelectorAll('[data-del-cat]').forEach(el => {
    el.addEventListener('click', () => {
      const cat = el.dataset.delCat;
      if (state.assets.some(a => a.category === cat)) { showToast('该分类下有资产，无法删除'); return; }
      state.categories = state.categories.filter(c => c !== cat);
      saveCategories(state.categories);
      renderApp();
    });
  });
  // 添加分类
  const addBtn = document.getElementById('btn-add-cat');
  if (addBtn) addBtn.addEventListener('click', () => {
    const input = document.getElementById('new-cat-input');
    const val = input.value.trim();
    if (!val) { showToast('请输入分类名称'); return; }
    if (state.categories.includes(val)) { showToast('分类已存在'); return; }
    state.categories.push(val);
    saveCategories(state.categories);
    input.value = '';
    renderApp();
  });
  // 清空数据
  const clearBtn = document.getElementById('btn-clear-all');
  if (clearBtn) clearBtn.addEventListener('click', () => {
    if (!confirm('确认清空所有资产数据？此操作不可恢复！')) return;
    state.assets = [];
    saveAssets([]);
    showToast('已清空');
    renderApp();
  });
}

let searchVisible = false;
function toggleSearch() {
  searchVisible = !searchVisible;
  const container = document.getElementById('search-bar-container');
  if (!container) return;
  if (searchVisible) {
    container.innerHTML = `
      <div class="search-bar-wrap">
        <div class="search-bar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input id="search-input" placeholder="搜索资产名称或分类" value="${state.searchQuery}">
          <span class="search-clear" id="search-clear">×</span>
        </div>
      </div>`;
    const input = document.getElementById('search-input');
    input.focus();
    input.addEventListener('input', () => { state.searchQuery = input.value; renderGridOnly(); });
    document.getElementById('search-clear').addEventListener('click', () => {
      state.searchQuery = ''; input.value = ''; renderGridOnly();
    });
  } else {
    state.searchQuery = '';
    container.innerHTML = '';
    renderGridOnly();
  }
}

function renderGridOnly() {
  const grid = document.getElementById('asset-grid');
  if (!grid) return;
  const filtered = getFilteredAssets();
  grid.innerHTML = filtered.length === 0
    ? `<div class="empty-state"><div class="empty-icon">📭</div><p>暂无匹配资产</p></div>`
    : filtered.map(a => {
        const { daysUsed, dailyCost, daysLeft, progress } = calcAsset(a);
        return `
        <div class="asset-card" data-id="${a.id}">
          <span class="card-status-badge ${statusBadgeClass(a.status)}">${statusLabel(a.status)}</span>
          <span class="card-emoji">${a.emoji || '📦'}</span>
          <div class="card-name">${a.name}</div>
          <div class="card-meta">¥${fmtMoney(a.purchasePrice)} | 已使用 ${daysUsed} 天</div>
          <div class="card-daily">¥${fmtNum(dailyCost)}<span>/天</span></div>
          <div class="card-progress-wrap">
            <div class="card-progress"><div class="card-progress-fill" style="width:${progress}%"></div></div>
            <div class="card-days-left">${daysLeft > 0 ? daysLeft + ' 天 left' : '已超出预期'}</div>
          </div>
        </div>`;
      }).join('');
  grid.querySelectorAll('.asset-card').forEach(el => {
    el.addEventListener('click', () => openDetailSheet(el.dataset.id));
  });
}

/* ─── 主渲染 & 初始化 ────────────────────────────────────── */

function renderApp() {
  const app = document.getElementById('app');
  let viewHtml = '';
  if (state.currentView === 'home')     viewHtml = renderHome();
  else if (state.currentView === 'stats')    viewHtml = renderStats();
  else if (state.currentView === 'settings') viewHtml = renderSettings();

  app.innerHTML = `
    ${viewHtml}
    <div id="sheet-overlay" class="overlay"></div>
    <nav class="bottom-nav">
      <div class="nav-item${state.currentView==='home'?' active':''}" data-nav="home">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>首页</span>
      </div>
      <div class="nav-item${state.currentView==='stats'?' active':''}" data-nav="stats">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        <span>统计</span>
      </div>
      <div class="nav-add" id="btn-add">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      </div>
      <div class="nav-item${state.currentView==='settings'?' active':''}" data-nav="settings">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        <span>设置</span>
      </div>
    </nav>`;

  // 底部导航
  document.querySelectorAll('[data-nav]').forEach(el => {
    el.addEventListener('click', () => {
      state.currentView = el.dataset.nav;
      searchVisible = false;
      state.searchQuery = '';
      renderApp();
    });
  });

  // 添加按钮
  document.getElementById('btn-add').addEventListener('click', () => openFormSheet(null));

  // 点击遮罩关闭
  document.getElementById('sheet-overlay').addEventListener('click', e => {
    if (e.target.id === 'sheet-overlay') closeSheet();
  });

  // 页面特定事件
  if (state.currentView === 'home')     bindHomeEvents();
  if (state.currentView === 'settings') bindSettingsEvents();
}

// 启动
renderApp();
