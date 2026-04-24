Page({
  data: {
    userInfo: {},
    profile: { height: '', birthYear: '', gender: '' },
  },

  onLoad() {
    const profile = wx.getStorageSync('user_profile') || {};
    this.setData({ profile });
    wx.getUserProfile({
      desc: '展示个人信息',
      success: (res) => this.setData({ userInfo: res.userInfo }),
      fail: () => {},
    });
  },

  onHeightInput(e) { this.setData({ 'profile.height': e.detail.value }); },
  onBirthChange(e) { this.setData({ 'profile.birthYear': e.detail.value.slice(0, 4) }); },
  setGender(e) { this.setData({ 'profile.gender': e.currentTarget.dataset.val }); },

  saveProfile() {
    wx.setStorageSync('user_profile', this.data.profile);
    wx.showToast({ title: '已保存 ✓', icon: 'success' });
  },

  goPage(e) {
    wx.navigateTo({ url: e.currentTarget.dataset.url });
  },

  exportData() {
    wx.showToast({ title: '导出功能开发中', icon: 'none' });
  },

  setReminder() {
    wx.showToast({ title: '提醒设置开发中', icon: 'none' });
  },
});
