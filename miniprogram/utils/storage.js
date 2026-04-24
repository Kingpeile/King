const TYPE_CONFIG = {
  weight: {
    name: '体重', emoji: '⚖️', color: '#FFE566',
    fields: [{ key: 'weight', label: '体重', unit: 'kg', placeholder: '68.0', inputType: 'digit' }],
  },
  bp: {
    name: '血压', emoji: '💗', color: '#FFB5C8',
    fields: [
      { key: 'systolic',  label: '收缩压', unit: 'mmHg', placeholder: '120', inputType: 'number' },
      { key: 'diastolic', label: '舒张压', unit: 'mmHg', placeholder: '80',  inputType: 'number' },
    ],
  },
  glucose: {
    name: '血糖', emoji: '🩸', color: '#FF9B6A',
    fields: [
      { key: 'glucose', label: '血糖值', unit: 'mmol/L', placeholder: '5.6', inputType: 'digit' },
      { key: 'timing',  label: '检测时间', unit: '', placeholder: '空腹/餐后2h', inputType: 'text' },
    ],
  },
  sleep: {
    name: '睡眠', emoji: '😴', color: '#B5D4EA',
    fields: [
      { key: 'hours',   label: '时长', unit: 'h', placeholder: '7.5', inputType: 'digit' },
      { key: 'quality', label: '质量', unit: '分(1-10)', placeholder: '8', inputType: 'number' },
    ],
  },
  steps: {
    name: '步数', emoji: '👟', color: '#B5EAD7',
    fields: [{ key: 'steps', label: '步数', unit: '步', placeholder: '8000', inputType: 'number' }],
  },
  water: {
    name: '饮水', emoji: '💧', color: '#D4B5EA',
    fields: [{ key: 'water', label: '饮水量', unit: 'ml', placeholder: '1500', inputType: 'number' }],
  },
};

function getRecords(type) {
  return wx.getStorageSync(`hr_${type}`) || [];
}

function addRecord(type, date, data) {
  const list = getRecords(type);
  list.unshift({ _id: Date.now().toString(), type, date, data });
  wx.setStorageSync(`hr_${type}`, list.slice(0, 500));
}

function formatValue(type, data) {
  const fmt = {
    weight:  d => `${d.weight}kg`,
    bp:      d => `${d.systolic}/${d.diastolic}`,
    glucose: d => `${d.glucose} mmol/L`,
    sleep:   d => `${d.hours}h`,
    steps:   d => `${(+d.steps).toLocaleString()}步`,
    water:   d => `${d.water}ml`,
  };
  return fmt[type] ? fmt[type](data) : '-';
}

function evaluate(type, data) {
  const evals = {
    weight:  d => { const v = +d.weight; return v < 45 || v > 100 ? { status:'warning', statusText:'注意' } : { status:'normal', statusText:'正常' }; },
    bp:      d => { const s = +d.systolic; return s <= 120 ? { status:'normal', statusText:'正常' } : s <= 139 ? { status:'warning', statusText:'偏高' } : { status:'danger', statusText:'高' }; },
    glucose: d => { const g = +d.glucose; return g <= 6.1 ? { status:'normal', statusText:'正常' } : g <= 7 ? { status:'warning', statusText:'偏高' } : { status:'danger', statusText:'过高' }; },
    sleep:   d => +d.hours >= 7 ? { status:'normal', statusText:'良好' } : { status:'warning', statusText:'不足' },
    steps:   d => +d.steps >= 8000 ? { status:'normal', statusText:'达标' } : { status:'warning', statusText:'偏少' },
    water:   d => +d.water >= 1500 ? { status:'normal', statusText:'达标' } : { status:'warning', statusText:'不足' },
  };
  return evals[type] ? evals[type](data) : { status: 'normal', statusText: '-' };
}

module.exports = { TYPE_CONFIG, getRecords, addRecord, formatValue, evaluate };
