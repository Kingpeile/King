# REFERENCE — 东方财富接口与字段映射

脚本 `scripts/em.py` 已封装下列接口并做好缩放还原。本文件供调试 / 扩展时查阅。

## 通用

- 请求头：带 `User-Agent` 与 `Referer: https://quote.eastmoney.com/`，否则易 403。
- `secid` 格式：`market.code`，沪市 `1.`，深市/北交所 `0.`，港股 `116.`/`128.`，美股 `105/106/107.`。
- 不传 `cb`(jsonp) 参数时接口直接返回 JSON。

## 1. 搜索 searchapi

`GET https://searchapi.eastmoney.com/api/suggest/get`

| 参数 | 值 |
|------|----|
| input | 关键词 |
| type | 14 |
| token | D43BF722C8E33BDC906FB84D85E326E8（公开） |
| count | 条数 |

返回 `QuotationCodeTable.Data[]`：`Code`、`Name`、`QuoteID`(=secid)、`MarketType`、`SecurityTypeName`。

## 2. 实时行情 push2 stock/get

`GET https://push2.eastmoney.com/api/qt/stock/get?secid=...&fields=...`

| 字段 | 含义 | 缩放 |
|------|------|------|
| f57 / f58 | 代码 / 名称 | — |
| f59 | 价格小数位数 | 价格 ÷ 10^f59 |
| f43 | 现价 | ÷10^f59 |
| f44 / f45 / f46 | 最高 / 最低 / 今开 | ÷10^f59 |
| f60 | 昨收 | ÷10^f59 |
| f169 / f170 | 涨跌额 / 涨跌幅% | f169 ÷10^f59；f170 ÷100 |
| f171 | 振幅% | ÷100 |
| f168 | 换手率% | ÷100 |
| f50 | 量比 | ÷100 |
| f47 / f48 | 成交量(手) / 成交额(元) | 原值 |
| f162 / f167 | 市盈率(动) / 市净率 | ÷100 |
| f116 / f117 | 总市值 / 流通市值(元) | 原值 |
| f84 / f85 | 总股本 / 流通股 | 原值 |
| f51 / f52 | 涨停 / 跌停价 | ÷10^f59 |

## 3. K 线 push2his kline/get

`GET https://push2his.eastmoney.com/api/qt/stock/kline/get`

| 参数 | 说明 |
|------|------|
| klt | 1/5/15/30/60=分钟；101=日；102=周；103=月；104=季；106=年 |
| fqt | 0 不复权；1 前复权；2 后复权 |
| fields2 | `f51..f61` |
| lmt | 返回根数 |

`data.klines[]` 每行逗号分隔（已是真实单位）：
`日期, 开, 收, 高, 低, 成交量(手), 成交额(元), 振幅%, 涨跌幅%, 涨跌额, 换手率%`

## 4. 资金流向 push2his fflow/daykline/get

`GET https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?klt=101`

`data.klines[]` 每行：
`日期, 主力净额, 小单净额, 中单净额, 大单净额, 超大单净额, 主力净占比%, ...`（单位：元 / %）

口径：超大单+大单=主力。正值净流入、负值净流出。

## 5. 榜单 push2 clist/get

`GET https://push2.eastmoney.com/api/qt/clist/get`

| 参数 | 说明 |
|------|------|
| pn / pz | 页码 / 每页条数 |
| po | 1 降序、0 升序 |
| fid | 排序字段：f3 涨跌幅、f6 成交额、f5 量、f8 换手、f2 价、f9 PE、f20 市值 |
| fs | 板块过滤（见下） |
| fields | f12 代码、f14 名称、f2 价、f3 涨跌幅、f4 涨跌额、f5 量、f6 额、f8 换手 |

`fs` 板块串：
- 沪深A：`m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048`
- 创业板：`m:0+t:80`；科创板：`m:1+t:23`；北交所：`m:0+t:81+s:2048`
- 港股：`m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2`
- 美股：`m:105,m:106,m:107`

`clist` 的 f2/f3/f4/f8 等普遍 ÷100。

## 免责声明

数据来自东方财富公开接口，仅供研究/参考，非投资建议；接口为非官方文档约定，
东方财富可能随时调整字段或风控，失效时按本文件对照排查。
