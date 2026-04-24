const db = wx.cloud ? wx.cloud.database() : null;

const TYPE_CONFIG = {
  weight: {
    name: '体重', emoji: '⚖️', color: '#FFE566',
    fields: [
      { key: 'weight', label: '体重', unit: 'kg', placeholder: '0.0', inputType: 'digit' },
    ],
    evaluate(d) {
      const bmi = d.weight / ((d.height || 170) / 100) ** 2;
      if (bmi < 18.5) return { status: 'warning', statusText: '偏瘦' };
      if (bmi < 24) return { status: 'normal', statusText: '正常' };
      if (bmi < 28) return { status: 'warning', statusText: '超重' };
      return { status: 'danger', statusText: '肥胖' };
    },
    display: d => `${d.weight}kg`,
  },
  bp: {
    name: '血压', emoji: '💗', color: '#FFB5C8',
    fields: [
      { key: 'systolic',  label: '收缩压', unit: 'mmHg', placeholder: '120', inputType: 'number' },
      { key: 'diastolic', label: '舒张压', unit: 'mmHg', placeholder: '80',  inputType: 'number' },
    ],
    evaluate(d) {
      const s = +d.systolic, di = +d.diastolic;
      if (s < 90 || di < 60) return { status: 'warning', statusText: '偏低' };
      if (s <= 120 && di <= 80) return { status: 'normal', statusText: '正常' };
      if (s <= 139 || di <= 89) return { status: 'warning', statusText: '偏高' };
      return { status: 'danger', statusText: '高血压' };
    },
    display: d => `${d.systolic}/${d.diastolic} mmHg`,
  },
  glucose: {
    name: '血糖', emoji: '🩸', color: '#FFB5C8',
    fields: [
      { key: 'glucose', label: '血糖值', unit: 'mmol/L', placeholder: '5.6', inputType: 'digit' },
      { key: 'timing',  label: '检测时间', unit: '', placeholder: '空腹/餐后2h', inputType: 'text' },
    ],
    evaluate(d) {
      const g = +d.glucose;
      if (g < 3.9) return { status: 'warning', statusText: '偏低' };
      if (g <= 6.1) return { status: 'normal', statusText: '正常' };
      if (g <= 7.0) return { status: 'warning', statusText: '偏高' };
      return { status: 'danger', statusText: '过高' };
    },
    display: d => `${d.glucose} mmol/L`,
  },
  sleep: {
    name: '睡眠', emoji: '😴', color: '#B5D4EA',
    fields: [
      { key: 'hours',   label: '睡眠时长', unit: '小时', placeholder: '7.5', inputType: 'digit' },
      { key: 'quality', label: '睡眠质量', unit: '分(1-10)', placeholder: '8', inputType: 'number' },
    ],
    evaluate(d) {
      const h = +d.hours;
      if (h >= 7 && h <= 9) return { status: 'normal', statusText: '良好' };
      if (h >= 6) return { status: 'warning', statusText: '偏少' };
      return { status: 'danger', statusText: '不足' };
    },
    display: d => `${d.hours}h`,
  },
  steps: {
    name: '步数', emoji: '👟', color: '#B5EAD7',
    fields: [
      { key: 'steps', label: '步数', unit: '步', placeholder: '8000', inputType: 'number' },
    ],
    evaluate(d) {
      const s = +d.steps;
      if (s >= 10000) return { status: 'normal', statusText: '优秀' };
      if (s >= 6000) return { status: 'normal', statusText: '良好' };
      return { status: 'warning', statusText: '偏少' };
    },
    display: d => `${(+d.steps).toLocaleString()}步`,
  },
  water: {
    name: '饮水', emoji: '💧', color: '#D4B5EA',
    fields: [
      { key: 'water', label: '饮水量', unit: 'ml', placeholder: '1500', inputType: 'number' },
    ],
    evaluate(d) {
      const w = +d.water;
      if (w >= 1500) return { status: 'normal', statusText: '达标' };
      return { status: 'warning', statusText: '不足' };
    },
    display: d => `${d.water}ml`,
  },
};

Page({
  data: {
    typeList: Object.entries(TYPE_CONFIG).map(([type, c]) => ({ type, ...c })),
    activeType: 'weight',
    currentType: { ...TYPE_CONFIG.weight, type: 'weight' },
    recordDate: '',
    formData: {},
    historyList: [],
  },

  onLoad(options) {
    const today = new Date();
    const date = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
    const type = options.type || 'weight';
    this.setData({ recordDate: date, activeType: type, currentType: { ...TYPE_CONFIG[type], type } });
    this.loadHistory(type);
  },

  switchType(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({
      activeType: type,
      currentType: { ...TYPE_CONFIG[type], type },
      formData: {},
    });
    this.loadHistory(type);
  },

  onDateChange(e) {
    this.setData({ recordDate: e.detail.value });
  },

  onInput(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ [`formData.${key}`]: e.detail.value });
  },

  onNoteInput(e) {
    this.setData({ 'formData.note': e.detail.value });
  },

  loadHistory(type) {
    if (!db) return;
    db.collection('health_records')
      .where({ type })
      .orderBy('date', 'desc')
      .limit(20)
      .get()
      .then(res => {
        const config = TYPE_CONFIG[type];
        const historyList = res.data.map(r => ({
          ...r,
          displayValue: config.display(r.data),
          ...config.evaluate(r.data),
        }));
        this.setData({ historyList });
      })
      .catch(() => {});
  },

  saveRecord() {
    const { activeType, recordDate, formData } = this.data;
    const config = TYPE_CONFIG[activeType];
    const fields = config.fields.map(f => f.key);
    for (const key of fields) {
      if (!formData[key]) {
        wx.showToast({ title: `请填写${config.fields.find(f => f.key === key).label}`, icon: 'none' });
        return;
      }
    }

    const record = {
      type: activeType,
      date: recordDate,
      data: { ...formData },
      note: formData.note || '',
      createdAt: db ? db.serverDate() : new Date().toISOString(),
    };

    if (!db) {
      // 本地缓存降级
      const key = `health_${activeType}`;
      const local = wx.getStorageSync(key) || [];
      local.unshift({ ...record, _id: Date.now().toString() });
      wx.setStorageSync(key, local.slice(0, 100));
      wx.showToast({ title: '已保存到本地', icon: 'success' });
      this.setData({ formData: {} });
      this.loadHistory(activeType);
      return;
    }

    db.collection('health_records').add({ data: record }).then(() => {
      wx.showToast({ title: '保存成功 🎉', icon: 'success' });
      this.setData({ formData: {} });
      this.loadHistory(activeType);
    }).catch(() => {
      wx.showToast({ title: '保存失败，请重试', icon: 'none' });
    });
  },
});
