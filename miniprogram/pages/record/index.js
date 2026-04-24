const storage = require('../../utils/storage');

const TYPE_CONFIG = storage.TYPE_CONFIG;

Page({
  data: {
    typeList: Object.entries(TYPE_CONFIG).map(([type, c]) => ({ type, ...c })),
    activeType: 'weight',
    currentType: null,
    recordDate: '',
    formData: {},
    historyList: [],
  },

  onLoad(options) {
    const today = new Date();
    const date = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
    const type = options.type || 'weight';
    this.setData({
      recordDate: date,
      activeType: type,
      currentType: { ...TYPE_CONFIG[type], type },
    });
    this.loadHistory(type);
  },

  switchType(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ activeType: type, currentType: { ...TYPE_CONFIG[type], type }, formData: {} });
    this.loadHistory(type);
  },

  onDateChange(e) { this.setData({ recordDate: e.detail.value }); },
  onInput(e) { this.setData({ [`formData.${e.currentTarget.dataset.key}`]: e.detail.value }); },
  onNoteInput(e) { this.setData({ 'formData.note': e.detail.value }); },

  loadHistory(type) {
    const records = storage.getRecords(type);
    const historyList = records.map(r => ({
      ...r,
      displayValue: storage.formatValue(type, r.data),
      ...storage.evaluate(type, r.data),
    }));
    this.setData({ historyList });
  },

  saveRecord() {
    const { activeType, recordDate, formData } = this.data;
    const config = TYPE_CONFIG[activeType];
    for (const f of config.fields) {
      if (!formData[f.key]) {
        wx.showToast({ title: `请填写${f.label}`, icon: 'none' });
        return;
      }
    }
    storage.addRecord(activeType, recordDate, { ...formData });
    wx.showToast({ title: '保存成功 🎉', icon: 'success' });
    this.setData({ formData: {} });
    this.loadHistory(activeType);
  },
});
