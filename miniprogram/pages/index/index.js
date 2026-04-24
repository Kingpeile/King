const db = wx.cloud ? wx.cloud.database() : null;

Page({
  data: {
    userInfo: {},
    greeting: '',
    today: '',
    healthScore: 82,
    scoreTip: '状态不错，继续保持 💪',
    nextCheckup: { days: 45 },
    quickItems: [
      { id: 1, type: 'weight',   name: '体重',  emoji: '⚖️', color: '#FFE566', value: '68kg' },
      { id: 2, type: 'steps',    name: '步数',  emoji: '👟', color: '#B5EAD7', value: '6,240' },
      { id: 3, type: 'sleep',    name: '睡眠',  emoji: '😴', color: '#B5D4EA', value: '7.5h' },
      { id: 4, type: 'water',    name: '饮水',  emoji: '💧', color: '#D4B5EA', value: '1.2L' },
    ],
    recentMetrics: [
      { id: 1, name: '血压',   date: '2024-03-15', value: '118/76', unit: 'mmHg', color: '#FF9B6A', status: 'normal',  statusText: '正常' },
      { id: 2, name: '血糖',   date: '2024-03-15', value: '5.2',    unit: 'mmol/L', color: '#FFB5C8', status: 'normal', statusText: '正常' },
      { id: 3, name: '总胆固醇', date: '2024-03-01', value: '5.8',  unit: 'mmol/L', color: '#FFE566', status: 'warning', statusText: '偏高' },
      { id: 4, name: '体重',   date: '2024-04-20', value: '68.5',  unit: 'kg',    color: '#B5EAD7', status: 'normal',  statusText: '正常' },
    ],
  },

  onLoad() {
    this.setGreeting();
    this.loadUserInfo();
    this.loadLatestMetrics();
  },

  onShow() {
    this.loadLatestMetrics();
  },

  setGreeting() {
    const hour = new Date().getHours();
    const now = new Date();
    const greetings = { morning: '早上好 ☀️', afternoon: '下午好 🌤', evening: '晚上好 🌙' };
    const greeting = hour < 12 ? greetings.morning : hour < 18 ? greetings.afternoon : greetings.evening;
    const today = `${now.getFullYear()}年${now.getMonth()+1}月${now.getDate()}日`;
    this.setData({ greeting, today });
  },

  loadUserInfo() {
    wx.getUserProfile({
      desc: '用于展示个人信息',
      success: (res) => this.setData({ userInfo: res.userInfo }),
      fail: () => {},
    });
  },

  loadLatestMetrics() {
    if (!db) return;
    db.collection('health_records')
      .orderBy('date', 'desc')
      .limit(10)
      .get()
      .then(res => {
        if (res.data.length > 0) {
          // 处理最近数据
          console.log('loaded metrics', res.data.length);
        }
      })
      .catch(err => console.error('load metrics error', err));
  },

  goRecord(e) {
    const { type } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/record/index?type=${type}` });
  },
});
