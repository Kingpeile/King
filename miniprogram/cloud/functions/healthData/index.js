const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();

exports.main = async (event, context) => {
  const { action, data } = event;
  const { OPENID } = cloud.getWXContext();

  switch (action) {
    case 'addRecord':
      return db.collection('health_records').add({ data: { ...data, openid: OPENID } });

    case 'getRecords':
      return db.collection('health_records')
        .where({ openid: OPENID, type: data.type })
        .orderBy('date', 'desc')
        .limit(data.limit || 50)
        .get();

    case 'addReport':
      return db.collection('health_reports').add({ data: { ...data, openid: OPENID } });

    case 'getReports':
      return db.collection('health_reports')
        .where({ openid: OPENID })
        .orderBy('date', 'desc')
        .get();

    default:
      return { error: 'unknown action' };
  }
};
