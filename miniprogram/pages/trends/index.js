const db = wx.cloud ? wx.cloud.database() : null;

const COLORS = {
  weight: '#FFE566', bp: '#FFB5C8', glucose: '#FF9B6A',
  sleep: '#B5D4EA', steps: '#B5EAD7', water: '#D4B5EA',
};

Page({
  data: {
    metricTabs: [
      { type: 'weight',  name: '体重', emoji: '⚖️', color: '#FFE566' },
      { type: 'bp',      name: '血压', emoji: '💗', color: '#FFB5C8' },
      { type: 'glucose', name: '血糖', emoji: '🩸', color: '#FF9B6A' },
      { type: 'sleep',   name: '睡眠', emoji: '😴', color: '#B5D4EA' },
      { type: 'steps',   name: '步数', emoji: '👟', color: '#B5EAD7' },
    ],
    ranges: [
      { val: '1m', label: '近1月' },
      { val: '3m', label: '近3月' },
      { val: '6m', label: '近半年' },
      { val: '1y', label: '近1年' },
    ],
    activeMetric: 'weight',
    activeRange: '3m',
    activeRangeLabel: '近3月',
    activeColor: '#FFE566',
    stats: [],
    chartBars: [],
    chartLabels: [],
    dataList: [],
  },

  onLoad() {
    this.loadData();
  },

  switchMetric(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ activeMetric: type, activeColor: COLORS[type] });
    this.loadData();
  },

  switchRange(e) {
    const val = e.currentTarget.dataset.val;
    const label = this.data.ranges.find(r => r.val === val).label;
    this.setData({ activeRange: val, activeRangeLabel: label });
    this.loadData();
  },

  getStartDate() {
    const d = new Date();
    const map = { '1m': 1, '3m': 3, '6m': 6, '1y': 12 };
    d.setMonth(d.getMonth() - (map[this.data.activeRange] || 3));
    return d.toISOString().slice(0, 10);
  },

  loadData() {
    const { activeMetric } = this.data;
    const startDate = this.getStartDate();

    if (!db) {
      const key = `health_${activeMetric}`;
      const local = wx.getStorageSync(key) || [];
      this.processData(local.filter(r => r.date >= startDate));
      return;
    }

    db.collection('health_records')
      .where({ type: activeMetric })
      .orderBy('date', 'desc')
      .limit(100)
      .get()
      .then(res => {
        const filtered = res.data.filter(r => r.date >= startDate);
        this.processData(filtered);
      })
      .catch(() => {});
  },

  processData(records) {
    if (!records.length) {
      this.setData({ dataList: [], stats: [], chartBars: [], chartLabels: [] });
      return;
    }

    const type = this.data.activeMetric;
    const values = records.map(r => this.getMainValue(type, r.data)).filter(v => !isNaN(v));
    const min = Math.min(...values), max = Math.max(...values);
    const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1);

    const stats = [
      { label: '最高', value: `${max}` },
      { label: '平均', value: `${avg}` },
      { label: '最低', value: `${min}` },
    ];

    // 图表数据（最近12条）
    const recent = [...records].reverse().slice(-12);
    const chartValues = recent.map(r => this.getMainValue(type, r.data));
    const chartMax = Math.max(...chartValues) || 1;
    const color = COLORS[type];
    const chartBars = chartValues.map((v, i) => ({
      h: Math.max(16, Math.round((v / chartMax) * 200)),
      color,
      opacity: 0.4 + 0.6 * (i / chartValues.length),
    }));
    const chartLabels = recent.map(r => r.date.slice(5));

    const dataList = records.map(r => ({
      ...r,
      displayValue: this.formatValue(type, r.data),
      ...this.evaluate(type, r.data),
    }));

    this.setData({ stats, chartBars, chartLabels, dataList });
  },

  getMainValue(type, data) {
    const map = { weight: 'weight', bp: 'systolic', glucose: 'glucose', sleep: 'hours', steps: 'steps', water: 'water' };
    return parseFloat(data[map[type]]);
  },

  formatValue(type, data) {
    const fmt = {
      weight: d => `${d.weight}kg`,
      bp: d => `${d.systolic}/${d.diastolic}`,
      glucose: d => `${d.glucose} mmol/L`,
      sleep: d => `${d.hours}h`,
      steps: d => `${(+d.steps).toLocaleString()}步`,
      water: d => `${d.water}ml`,
    };
    return fmt[type] ? fmt[type](data) : '-';
  },

  evaluate(type, data) {
    const evals = {
      weight: d => { const v = +d.weight; return v < 50 ? { status:'warning', statusText:'偏轻' } : v < 80 ? { status:'normal', statusText:'正常' } : { status:'warning', statusText:'偏重' }; },
      bp: d => { const s = +d.systolic; return s <= 120 ? { status:'normal', statusText:'正常' } : s <= 139 ? { status:'warning', statusText:'偏高' } : { status:'danger', statusText:'高' }; },
      glucose: d => { const g = +d.glucose; return g <= 6.1 ? { status:'normal', statusText:'正常' } : g <= 7 ? { status:'warning', statusText:'偏高' } : { status:'danger', statusText:'过高' }; },
      sleep: d => { const h = +d.hours; return h >= 7 ? { status:'normal', statusText:'良好' } : { status:'warning', statusText:'不足' }; },
      steps: d => +d.steps >= 8000 ? { status:'normal', statusText:'达标' } : { status:'warning', statusText:'偏少' },
      water: d => +d.water >= 1500 ? { status:'normal', statusText:'达标' } : { status:'warning', statusText:'不足' },
    };
    return evals[type] ? evals[type](data) : { status: 'normal', statusText: '-' };
  },
});
