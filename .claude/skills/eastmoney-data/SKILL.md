---
name: eastmoney-data
description: 取东方财富（妙想）公开行情数据——A股/港股/美股实时报价、K线、个股资金流向、涨跌幅成交额榜单、代码搜索。Use when 用户要查股票行情、股价、K线、资金流、涨跌榜，或提到东方财富/妙想/eastmoney 行情数据。
---

# 东方财富行情数据 (eastmoney-data)

封装东方财富公开数据接口（`push2` / `push2his` / `searchapi`），稳定可靠、无需 API key。
所有取数走 `scripts/em.py`，纯 Python 标准库、零依赖。

> 注意：本 skill 取的是东方财富**公开行情数据**，不是「妙想」对话式 AI。
> 妙想（ai.eastmoney.com）无公开开发者 API，对话能力无法在此封装。

## 前置：网络可达

接口需要能访问 `*.eastmoney.com`。若运行环境网络白名单未放开，会得到
「Host not in allowlist / 网络请求失败」——这是环境限制，把 skill 放到能联网的环境再用即可。

## Quick start

```bash
cd .claude/skills/eastmoney-data/scripts

python3 em.py search 贵州茅台          # 关键词 -> 代码/secid
python3 em.py quote 600519 000001      # 实时行情，可一次多只
python3 em.py kline 600519 --period day --adjust qfq --limit 30
python3 em.py fundflow 300750 --limit 10   # 个股资金流向（每日）
python3 em.py rank --list a --by change --limit 20  # 沪深A股涨幅榜
```

输出默认是结构化 JSON。所有子命令支持 `--json`（同样输出 JSON，便于程序消费）。

## 子命令

| 命令 | 作用 | 关键参数 |
|------|------|----------|
| `search <关键词>` | 名称/拼音/代码模糊搜，拿 secid | `--count` |
| `quote <代码...>` | 实时报价（价/涨跌/量额/换手/PE/PB/市值） | 可传多只 |
| `kline <代码>` | K 线 | `--period`、`--adjust`、`--limit` |
| `fundflow <代码>` | 每日主力/超大单/大单等净流入 | `--limit` |
| `rank` | 榜单排序 | `--list`、`--by`、`--limit`、`--asc` |

- `--period`：`1m 5m 15m 30m 60m day week month quarter year`
- `--adjust`：`none`(不复权) `qfq`(前复权) `hfq`(后复权)
- `--list`：`a sh sz cyb kcb bj hk us`
- `--by`：`change amount volume turnover price pe mktcap`

## 代码 / secid 规则

- 直接给 6 位代码即可，脚本自动判市场：`6/9`→沪、`0/2/3`→深、`4/8`→北交所。
- 显式前缀：`sh600519` / `sz000001` / `bj430047`，或直接 secid `1.600519`。
- 指数务必带前缀避免歧义：上证指数 `sh000001`、深证成指 `sz399001`。
- 港股/美股代码先用 `search` 拿 secid，再喂给 `quote`。

## 工作流：用户问某只股票

1. 不确定代码 → `search`，取第一个 `secid`。
2. 要现价/涨跌 → `quote`；要走势 → `kline`；要主力动向 → `fundflow`。
3. 给用户回答时换算单位：成交额/市值是「元」，成交量是「手」，
   涨跌幅/换手率/振幅是「%」。可自行折算成「亿元」更易读。

## 字段含义 / 缩放规则

接口返回的整数常带缩放（如价格 ×100）。脚本已自动还原成真实数值。
完整字段映射、缩放因子、各接口原始参数见 [REFERENCE.md](REFERENCE.md)。
加 `--json` 看脚本已解析好的结构；要原始字段调试时参考 REFERENCE。
