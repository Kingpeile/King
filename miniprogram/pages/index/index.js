const storage = require('../../utils/storage');

Page({
  data: {
    userInfo: {},
    greeting: '',
    today: '',
    healthScore: 0,
    scoreTip: '',
    nextCheckup: null,
    quickItems: [
      { id: 1, type: 'weight',  name: '体重', emoji: '⚖️', color: '#FFE566', value: '--' },
      { id: 2, type: 'steps',   name: '步数', emoji: '👟', color: '#B5EAD7', value: '--' },
      { id: 3, type: 'sleep',   name: '睡眠', emoji: '😴', color: '#B5D4EA', value: '--' },
      { id: 4, type: 'water',   name: '饮水', emoji: '💧', color: '#D4B5EA', value: '--' },
    ],
    recentMetrics: [],
  },

  onLoad() {
    this.setGreeting();
  },

  onShow() {
    this.loadData();
  },

  setGreeting() {
    const hour = new Date().getHours();
    const now = new Date();
    const greeting = hour < 12 ? '早上好 ☀️' : hour < 18 ? '下午好 🌤' : '晚上好 🌙';
    const today = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`;
    this.setData({ greeting, today });
  },

  loadData() {
    const types = ['weight', 'bp', 'glucose', 'sleep', 'steps', 'water'];
    const recentMetrics = [];
    const quickItems = [...this.data.quickItems];
    let totalScore = 100;

    types.forEach(type => {
      const records = storage.getRecords(type);
      if (!records.length) return;
      const latest = records[0];
      const info = storage.evaluate(type, latest.data);

      if (info.status === 'warning') totalScore -= 8;
      if (info.status === 'danger')  totalScore -= 15;

      const qi = quickItems.find(q => q.type === type);
      if (qi) qi.value = storage.formatValue(type, latest.data);

      if (['weight', 'bp', 'glucose'].includes(type)) {
        recentMetrics.push({
          id: type,
          name: { weight:'体重', bp:'血压', glucose:'血糖' }[type],
          date: latest.date,
          value: storage.formatValue(type, latest.data),
          unit: '',
          color: { weight:'#FFE566', bp:'#FFB5C8', glucose:'#FF9B6A' }[type],
          ...info,
        });
      }
    });

    const healthScore = Math.max(0, Math.min(100, totalScore));
    const scoreTip = healthScore >= 90 ? '状态很棒，继续保持 🌟'
      : healthScore >= 75 ? '整体不错，注意部分指标 💪'
      : '有几项需要关注，多留意 🌱';

    const reminder = wx.getStorageSync('checkup_reminder');
    let nextCheckup = null;
    if (reminder) {
      const diff = Math.ceil((new Date(reminder) - new Date()) / 86400000);
      if (diff > 0) nextCheckup = { days: diff };
    }

    this.setData({ quickItems, recentMetrics, healthScore, scoreTip, nextCheckup });
  },

  goRecord(e) {
    wx.navigateTo({ url: `/pages/record/index?type=${e.currentTarget.dataset.type}` });
  },
});
