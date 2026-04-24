const db = wx.cloud ? wx.cloud.database() : null;

const YEAR_COLORS = ['#FF9B6A', '#FFE566', '#B5EAD7', '#B5D4EA', '#FFB5C8', '#D4B5EA'];

Page({
  data: {
    reportCount: 0,
    yearSpan: 0,
    abnormalCount: 0,
    reports: [],
    keyMetrics: [],
  },

  onLoad() {
    this.loadReports();
  },

  onShow() {
    this.loadReports();
  },

  loadReports() {
    if (!db) {
      const local = wx.getStorageSync('health_reports') || [];
      this.processReports(local);
      return;
    }
    db.collection('health_reports')
      .orderBy('date', 'desc')
      .get()
      .then(res => this.processReports(res.data))
      .catch(() => {});
  },

  processReports(data) {
    const reports = data.map((r, i) => ({
      ...r,
      year: r.date ? r.date.slice(0, 4) : '未知',
      color: YEAR_COLORS[i % YEAR_COLORS.length],
      abnormal: r.abnormalItems ? r.abnormalItems.length : 0,
    }));

    const years = [...new Set(reports.map(r => r.year))];
    const yearSpan = years.length > 1 ? (Math.max(...years.map(Number)) - Math.min(...years.map(Number)) + 1) : years.length;
    const abnormalCount = reports.reduce((s, r) => s + r.abnormal, 0);

    this.setData({
      reports,
      reportCount: reports.length,
      yearSpan,
      abnormalCount,
    });

    this.buildKeyMetrics(data);
  },

  buildKeyMetrics(data) {
    // 构建跨年度关键指标对比（血压、血糖、总胆固醇、BMI）
    const metricsMap = {
      '血压(收缩压)': { color: '#FFB5C8', unit: 'mmHg' },
      '血糖(空腹)':   { color: '#FF9B6A', unit: 'mmol/L' },
      '总胆固醇':     { color: '#FFE566', unit: 'mmol/L' },
      'BMI':          { color: '#B5EAD7', unit: '' },
    };

    const keyMetrics = [];
    for (const [name, config] of Object.entries(metricsMap)) {
      const values = data
        .filter(r => r.metrics && r.metrics[name] != null)
        .map(r => ({ year: r.date.slice(0, 4), value: r.metrics[name] }))
        .sort((a, b) => a.year.localeCompare(b.year));

      if (values.length < 2) continue;

      const nums = values.map(v => +v.value);
      const maxVal = Math.max(...nums);
      const first = nums[0], last = nums[nums.length - 1];
      const trend = last > first * 1.05 ? 'up' : last < first * 0.95 ? 'down' : 'stable';

      keyMetrics.push({
        name,
        color: config.color,
        trend,
        values: values.map(v => ({
          year: v.year,
          value: `${v.value}${config.unit}`,
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
        wx.showLoading({ title: '上传中...' });
        if (!wx.cloud) {
          wx.hideLoading();
          wx.showToast({ title: '云开发未配置', icon: 'none' });
          return;
        }
        wx.cloud.uploadFile({
          cloudPath: `reports/${Date.now()}_${file.name}`,
          filePath: file.path,
          success: (r) => {
            wx.hideLoading();
            this.saveReportRecord(file.name, r.fileID);
          },
          fail: () => {
            wx.hideLoading();
            wx.showToast({ title: '上传失败', icon: 'none' });
          },
        });
      },
    });
  },

  saveReportRecord(name, fileID) {
    const today = new Date().toISOString().slice(0, 10);
    const record = {
      title: name.replace('.pdf', ''),
      date: today,
      fileID,
      hospital: '待填写',
      abnormalItems: [],
      metrics: {},
      createdAt: db ? db.serverDate() : new Date().toISOString(),
    };

    if (!db) {
      const local = wx.getStorageSync('health_reports') || [];
      local.unshift({ ...record, _id: Date.now().toString() });
      wx.setStorageSync('health_reports', local);
      wx.showToast({ title: '已保存', icon: 'success' });
      this.loadReports();
      return;
    }

    db.collection('health_reports').add({ data: record }).then(() => {
      wx.showToast({ title: '上传成功 🎉', icon: 'success' });
      this.loadReports();
    });
  },

  viewReport(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/reports/detail?id=${id}` });
  },
});
