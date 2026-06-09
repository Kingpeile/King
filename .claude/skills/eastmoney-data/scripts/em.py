#!/usr/bin/env python3
"""东方财富公开行情数据 CLI（仅用 Python 标准库，无需任何依赖）。

子命令：
  search   关键词 -> 证券代码 / secid
  quote    实时行情（支持一次查多只）
  kline    K 线（日/周/月/分钟，可前复权/后复权）
  fundflow 个股资金流向（每日主力/超大单/大单等净流入）
  rank     榜单（涨跌幅/成交额等排序，沪深A/科创/创业/港股/美股）

用法示例：
  python3 em.py search 贵州茅台
  python3 em.py quote 600519 000001 sh000001
  python3 em.py kline 600519 --period day --adjust qfq --limit 30
  python3 em.py fundflow 300750 --limit 10
  python3 em.py rank --list a --by change --limit 20

加 --raw 输出接口原始 JSON；加 --json 输出已解析的结构化 JSON（便于喂给程序）。
不加则输出人类可读的表格。
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"}
SEARCH_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"  # 公开搜索 token


def http_get(url, params=None, timeout=15):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def get_json(url, params=None, timeout=15):
    return json.loads(http_get(url, params, timeout))


# --------------------------------------------------------------------------
# secid 解析：把用户输入的代码转成 "market.code"（沪 1 / 深 0）
# --------------------------------------------------------------------------
def guess_secid(code):
    """把 600519 / sh600519 / 1.600519 等统一成 secid。"""
    code = str(code).strip()
    if "." in code:                       # 已经是 secid
        return code
    low = code.lower()
    if low.startswith("sh"):
        return "1." + code[2:]
    if low.startswith("sz") or low.startswith("bj"):
        return "0." + code[2:]
    if low.startswith(("us", "hk")):      # 交给上层用 search 解析
        return None
    digits = code
    if not digits.isdigit():
        return None
    head = digits[0]
    # 上交所：6 开头主板/科创(688)，9 开头 B 股，000/999 指数走 sh
    if head in ("6", "9"):
        return "1." + digits
    if head in ("0", "3", "2"):           # 深市主板/创业/B 股
        return "0." + digits
    if head in ("4", "8"):                # 北交所
        return "0." + digits
    if head == "1" or head == "5":        # 深市基金/沪市基金需上下文，默认深
        return "0." + digits
    return "0." + digits


def resolve(code):
    """先尝试本地猜测，失败再调搜索接口拿第一个结果。"""
    secid = guess_secid(code)
    if secid:
        return secid
    hits = do_search(code, count=1, _return=True)
    if hits:
        return hits[0]["secid"]
    raise SystemExit(f"无法解析代码：{code}（试试先用 search）")


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------
def do_search(keyword, count=10, _return=False):
    data = get_json(
        "https://searchapi.eastmoney.com/api/suggest/get",
        {"input": keyword, "type": "14", "token": SEARCH_TOKEN,
         "markettype": "", "mktnum": "", "jys": "", "classify": "",
         "securitytype": "", "count": str(count)},
    )
    table = (data.get("QuotationCodeTable") or {}).get("Data") or []
    rows = []
    for it in table:
        rows.append({
            "secid": it.get("QuoteID"),         # 形如 "1.600519"
            "code": it.get("Code"),
            "name": it.get("Name"),
            "market": it.get("MarketType"),
            "type": it.get("SecurityTypeName"),
        })
    if _return:
        return rows
    return rows


# --------------------------------------------------------------------------
# quote 实时行情
# --------------------------------------------------------------------------
# 字段含义与缩放：price=按小数位缩放(/10^f59)，pct=/100，raw=原值
QUOTE_FIELDS = "f43,f44,f45,f46,f47,f48,f50,f57,f58,f59,f60,f107,f116,f117,f162,f167,f168,f169,f170,f171,f84,f85,f51,f52"


def _scale(v, factor):
    if v in (None, "-", ""):
        return None
    try:
        return round(float(v) / factor, 4)
    except (TypeError, ValueError):
        return v


def do_quote(code):
    secid = resolve(code)
    data = get_json("https://push2.eastmoney.com/api/qt/stock/get",
                    {"secid": secid, "fields": QUOTE_FIELDS})
    d = data.get("data")
    if not d:
        return None
    dec = d.get("f59") or 2
    pf = 10 ** int(dec) if str(dec).isdigit() else 100  # 价格缩放因子
    return {
        "secid": secid,
        "code": d.get("f57"),
        "name": d.get("f58"),
        "price": _scale(d.get("f43"), pf),
        "change": _scale(d.get("f169"), pf),     # 涨跌额
        "change_pct": _scale(d.get("f170"), 100),  # 涨跌幅 %
        "open": _scale(d.get("f46"), pf),
        "high": _scale(d.get("f44"), pf),
        "low": _scale(d.get("f45"), pf),
        "prev_close": _scale(d.get("f60"), pf),
        "amplitude_pct": _scale(d.get("f171"), 100),
        "turnover_pct": _scale(d.get("f168"), 100),   # 换手率 %
        "volume_ratio": _scale(d.get("f50"), 100),    # 量比
        "volume_hand": d.get("f47"),                  # 成交量(手)
        "amount_yuan": d.get("f48"),                  # 成交额(元)
        "pe_ttm": _scale(d.get("f162"), 100),         # 市盈率(动)
        "pb": _scale(d.get("f167"), 100),             # 市净率
        "total_mktcap": d.get("f116"),                # 总市值(元)
        "float_mktcap": d.get("f117"),                # 流通市值(元)
        "limit_up": _scale(d.get("f51"), pf),
        "limit_down": _scale(d.get("f52"), pf),
    }


# --------------------------------------------------------------------------
# kline K 线
# --------------------------------------------------------------------------
PERIODS = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "60m": "60",
           "day": "101", "week": "102", "month": "103",
           "quarter": "104", "year": "106"}
ADJUST = {"none": "0", "qfq": "1", "hfq": "2"}  # 不复权/前复权/后复权


def do_kline(code, period="day", adjust="qfq", limit=120):
    secid = resolve(code)
    data = get_json("https://push2his.eastmoney.com/api/qt/stock/kline/get", {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": PERIODS.get(period, "101"),
        "fqt": ADJUST.get(adjust, "1"),
        "beg": "0", "end": "20500101", "lmt": str(limit),
    })
    d = data.get("data") or {}
    out = {"code": d.get("code"), "name": d.get("name"), "klines": []}
    for line in d.get("klines", []):
        p = line.split(",")
        out["klines"].append({
            "date": p[0], "open": float(p[1]), "close": float(p[2]),
            "high": float(p[3]), "low": float(p[4]),
            "volume_hand": float(p[5]), "amount_yuan": float(p[6]),
            "amplitude_pct": float(p[7]), "change_pct": float(p[8]),
            "change": float(p[9]), "turnover_pct": float(p[10]),
        })
    return out


# --------------------------------------------------------------------------
# fundflow 资金流向（每日）
# --------------------------------------------------------------------------
def do_fundflow(code, limit=30):
    secid = resolve(code)
    data = get_json(
        "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get", {
            "secid": secid, "klt": "101",
            "fields1": "f1,f2,f3,f7",
            "fields2": ("f51,f52,f53,f54,f55,f56,f57,f58,f59,"
                        "f60,f61,f62,f63,f64,f65"),
            "lmt": str(limit),
        })
    d = data.get("data") or {}
    out = {"code": d.get("code"), "name": d.get("name"), "days": []}
    for line in d.get("klines", []):
        p = line.split(",")
        out["days"].append({
            "date": p[0],
            "main_net": float(p[1]),       # 主力净流入(元)
            "small_net": float(p[2]),      # 小单
            "medium_net": float(p[3]),     # 中单
            "large_net": float(p[4]),      # 大单
            "super_net": float(p[5]),      # 超大单
            "main_net_pct": float(p[6]),   # 主力净占比 %
        })
    return out


# --------------------------------------------------------------------------
# rank 榜单
# --------------------------------------------------------------------------
LISTS = {
    # 沪深 A 股
    "a": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
    "sh": "m:1+t:2,m:1+t:23",
    "sz": "m:0+t:6,m:0+t:80",
    "cyb": "m:0+t:80",          # 创业板
    "kcb": "m:1+t:23",          # 科创板
    "bj": "m:0+t:81+s:2048",    # 北交所
    "hk": "m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2",  # 港股
    "us": "m:105,m:106,m:107",  # 美股
}
SORT_FIDS = {"change": "f3", "amount": "f6", "volume": "f5",
             "turnover": "f8", "price": "f2", "pe": "f9", "mktcap": "f20"}


def do_rank(which="a", by="change", limit=30, asc=False):
    data = get_json("https://push2.eastmoney.com/api/qt/clist/get", {
        "pn": "1", "pz": str(limit), "po": "0" if asc else "1", "np": "1",
        "fid": SORT_FIDS.get(by, "f3"),
        "fs": LISTS.get(which, LISTS["a"]),
        "fields": "f12,f14,f2,f3,f4,f5,f6,f8",
    })
    diff = ((data.get("data") or {}).get("diff")) or []
    if isinstance(diff, dict):          # 某些返回是 {idx: row}
        diff = list(diff.values())
    rows = []
    for it in diff:
        rows.append({
            "code": it.get("f12"), "name": it.get("f14"),
            "price": _scale(it.get("f2"), 100),
            "change_pct": _scale(it.get("f3"), 100),
            "change": _scale(it.get("f4"), 100),
            "volume_hand": it.get("f5"),
            "amount_yuan": it.get("f6"),
            "turnover_pct": _scale(it.get("f8"), 100),
        })
    return rows


# --------------------------------------------------------------------------
# 输出
# --------------------------------------------------------------------------
def emit(obj, as_json):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description="东方财富公开行情数据 CLI")
    ap.add_argument("--json", action="store_true", help="结构化 JSON 输出")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="关键词->代码")
    s.add_argument("keyword")
    s.add_argument("--count", type=int, default=10)

    q = sub.add_parser("quote", help="实时行情（可多只）")
    q.add_argument("codes", nargs="+")

    k = sub.add_parser("kline", help="K 线")
    k.add_argument("code")
    k.add_argument("--period", default="day", choices=list(PERIODS))
    k.add_argument("--adjust", default="qfq", choices=list(ADJUST))
    k.add_argument("--limit", type=int, default=120)

    f = sub.add_parser("fundflow", help="资金流向")
    f.add_argument("code")
    f.add_argument("--limit", type=int, default=30)

    r = sub.add_parser("rank", help="榜单")
    r.add_argument("--list", dest="which", default="a", choices=list(LISTS))
    r.add_argument("--by", default="change", choices=list(SORT_FIDS))
    r.add_argument("--limit", type=int, default=30)
    r.add_argument("--asc", action="store_true")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "search":
            emit(do_search(args.keyword, args.count), args.json)
        elif args.cmd == "quote":
            out = [do_quote(c) for c in args.codes]
            emit([x for x in out if x], args.json)
        elif args.cmd == "kline":
            emit(do_kline(args.code, args.period, args.adjust, args.limit),
                 args.json)
        elif args.cmd == "fundflow":
            emit(do_fundflow(args.code, args.limit), args.json)
        elif args.cmd == "rank":
            emit(do_rank(args.which, args.by, args.limit, args.asc), args.json)
    except urllib.error.URLError as e:
        sys.exit(f"网络请求失败：{e}（确认环境可访问 eastmoney.com）")


if __name__ == "__main__":
    main()
