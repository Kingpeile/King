const YEAR_COLORS = ['#FF9B6A', '#FFE566', '#B5EAD7', '#B5D4EA', '#FFB5C8', '#D4B5EA'];

Page({
  data: {
    reportCount: 0,
    yearSpan: 0,
    abnormalCount: 0,
    reports: [],
    keyMetrics: [],
  },

  onLoad() { this.loadReports(); },
  onShow() { this.loadReports(); },

  loadReports() {
    const data = wx.getStorageSync('health_reports') || [];
    const reports = data.map((r, i) => ({
      ...r,
      year: (r.date || '').slice(0, 4),
      color: YEAR_COLORS[i % YEAR_COLORS.length],
      abnormal: (r.abnormalItems || []).length,
    }));
    const years = [...new Set(reports.map(r => r.year).filter(Boolean).map(Number))];
    const yearSpan = years.length > 1 ? Math.max(...years) - Math.min(...years) + 1 : years.length;
    const abnormalCount = reports.reduce((s, r) => s + r.abnormal, 0);
    this.setData({ reports, reportCount: reports.length, yearSpan, abnormalCount });
    this.buildKeyMetrics(data);
  },

  buildKeyMetrics(data) {
    const defs = [
      { name: '血压(收缩压)', color: '#FFB5C8', unit: 'mmHg' },
      { name: '血糖(空腹)',   color: '#FF9B6A', unit: 'mmol/L' },
      { name: '总胆固醇',     color: '#FFE566', unit: 'mmol/L' },
      { name: 'BMI',          color: '#B5EAD7', unit: '' },
    ];
    const keyMetrics = [];
    for (const def of defs) {
      const values = data
        .filter(r => r.metrics && r.metrics[def.name] != null)
        .map(r => ({ year: (r.date || '').slice(0, 4), value: r.metrics[def.name] }))
        .sort((a, b) => a.year.localeCompare(b.year));
      if (values.length < 2) continue;
      const nums = values.map(v => +v.value);
      const maxVal = Math.max(...nums);
      const trend = nums[nums.length-1] > nums[0]*1.05 ? 'up' : nums[nums.length-1] < nums[0]*0.95 ? 'down' : 'stable';
      keyMetrics.push({
        name: def.name, color: def.color, trend,
        values: values.map(v => ({
          year: v.year,
          value: `${v.value}${def.unit}`,
          pct: Math.round((+v.value / maxVal) * 100),
        })),
      });
    }
    this.setData({ keyMetrics });
  },

  uploadReport() {
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['pdf'],
      success: (res) => {
        const file = res.tempFiles[0];
        const record = {
          _id: Date.now().toString(),
          title: file.name.replace('.pdf', ''),
          date: new Date().toISOString().slice(0, 10),
          hospital: '待填写',
          abnormalItems: [],
          metrics: {},
          filePath: file.path,
        };
        const list = wx.getStorageSync('health_reports') || [];
        list.unshift(record);
        wx.setStorageSync('health_reports', list);
        wx.showToast({ title: '已添加 🎉', icon: 'success' });
        this.loadReports();
      },
    });
  },

  viewReport(e) {
    wx.navigateTo({ url: `/pages/reports/detail?id=${e.currentTarget.dataset.id}` });
  },
});
