App({
  globalData: {
    userInfo: null,
  },
  onLaunch() {
    this.globalData.systemInfo = wx.getSystemInfoSync();
  },
});
