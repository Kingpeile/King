# -*- coding: utf-8 -*-
"""Competitive landscape deck — 曹操出行 (02643.HK) vs China ride-hailing peers."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION

# ---- palette ----
NAVY   = RGBColor(0x1F, 0x2D, 0x4D)
GRAY   = RGBColor(0x6B, 0x70, 0x7B)
LGRAY  = RGBColor(0xE8, 0xEA, 0xED)
ACCENT = RGBColor(0xE2, 0x6A, 0x2C)   # orange
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
FONT   = "Microsoft YaHei"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height

def slide():
    return prs.slides.add_slide(BLANK)

def box(s, l, t, w, h):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    return tb

def setpara(p, text, size, color=NAVY, bold=False, align=PP_ALIGN.LEFT, font=FONT):
    p.text = text
    p.alignment = align
    for r in p.runs:
        r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color; r.font.name = font
    return p

def title_bar(s, title, kicker=None):
    bar = s.shapes.add_shape(1, 0, 0, SW, Inches(0.12))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
    tb = box(s, 0.5, 0.28, 12.3, 1.0)
    setpara(tb.text_frame.paragraphs[0], title, 28, NAVY, True)
    if kicker:
        p = tb.text_frame.add_paragraph()
        setpara(p, kicker, 14, GRAY, False)

def footnote(s, text):
    tb = box(s, 0.5, 7.02, 12.3, 0.4)
    setpara(tb.text_frame.paragraphs[0], text, 9, GRAY)

def add_table(s, l, t, w, h, data, col_w=None, header=True, num_cols=None):
    rows, cols = len(data), len(data[0])
    g = s.shapes.add_table(rows, cols, Inches(l), Inches(t), Inches(w), Inches(h)).table
    if col_w:
        for i, cw in enumerate(col_w):
            g.columns[i].width = Inches(cw)
    num_cols = num_cols or set()
    for r in range(rows):
        for c in range(cols):
            cell = g.cell(r, c)
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = str(data[r][c])
            is_head = header and r == 0
            for run in p.runs:
                run.font.size = Pt(13 if not is_head else 13)
                run.font.bold = is_head
                run.font.name = FONT
                run.font.color.rgb = WHITE if is_head else NAVY
            if is_head:
                cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
                p.alignment = PP_ALIGN.LEFT
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if r % 2 else LGRAY
                p.alignment = PP_ALIGN.RIGHT if c in num_cols else PP_ALIGN.LEFT
    return g

# ============ Slide 1 — Title ============
s = slide()
bg = s.shapes.add_shape(1, 0, 0, SW, SH)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
s.shapes._spTree.remove(bg._element); s.shapes._spTree.insert(2, bg._element)
acc = s.shapes.add_shape(1, 0, Inches(4.6), SW, Inches(0.08))
acc.fill.solid(); acc.fill.fore_color.rgb = ACCENT; acc.line.fill.background()
tb = box(s, 0.8, 2.5, 11.7, 2.0)
setpara(tb.text_frame.paragraphs[0], "曹操出行 (02643.HK)", 40, WHITE, True)
p = tb.text_frame.add_paragraph()
setpara(p, "中国网约车竞争格局分析", 26, ACCENT, True)
tb2 = box(s, 0.8, 4.8, 11.7, 1.2)
setpara(tb2.text_frame.paragraphs[0],
        "对标 滴滴 · T3出行 · 如祺出行 · 享道出行 · 高德聚合 · 萝卜快跑", 16, LGRAY)
p = tb2.text_frame.add_paragraph()
setpara(p, "演示版 · 数据来源：港交所招股书/年报、弗若斯特沙利文、券商研报、公开新闻 · 2026-06", 12, GRAY)

# ============ Slide 2 — 行业格局 (pie) ============
s = slide()
title_bar(s, "一超多强：滴滴一家独大，曹操稳居第二梯队",
          "2024 年按 GTV 计，CR5 = 86%，格局高度集中")
cd = CategoryChartData()
cd.categories = ["滴滴 70.4%", "曹操出行 5.4%", "T3出行 5.3%", "其他 (含中长尾) 18.9%"]
cd.add_series("市占率", (70.4, 5.4, 5.3, 18.9))
gf = s.shapes.add_chart(XL_CHART_TYPE.PIE, Inches(0.4), Inches(1.7),
                        Inches(6.2), Inches(4.8), cd)
chart = gf.chart
chart.has_legend = True; chart.legend.position = XL_LEGEND_POSITION.RIGHT
chart.legend.include_in_layout = False; chart.legend.font.size = Pt(12)
plot = chart.plots[0]; plot.has_data_labels = True
dl = plot.data_labels; dl.show_percentage = True; dl.number_format = '0.0"%"'
dl.number_format_is_linked = False; dl.font.size = Pt(11); dl.font.bold = True
dl.position = XL_LABEL_POSITION.OUTSIDE_END
pts = plot.series[0].points
for pt, col in zip(pts, [ACCENT, NAVY, RGBColor(0x4A,0x6B,0xA8), GRAY]):
    pt.format.fill.solid(); pt.format.fill.fore_color.rgb = col
tb = box(s, 7.0, 1.8, 5.9, 4.6)
for txt, b in [
    ("市场关键数字", True),
    ("• 共享出行服务市场规模约 3,444 亿元，网约车占约 90%", False),
    ("• 行业 2024 订单量突破 100 亿单", False),
    ("• 滴滴 GTV 3,927 亿元 (+16.2%)，市占 70.4%", False),
    ("• 第二梯队：曹操 (5.4%) 与 T3 (5.3%) 贴身竞争", False),
    ("• 聚合平台 (高德/百度) 占行业订单 25.9% 并持续上升", False),
    ("• 中长尾：如祺、享道、首汽、万顺、萝卜快跑", False),
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 16 if b else 14, NAVY if b else GRAY, b)
    p.space_after = Pt(8)
footnote(s, "来源：弗若斯特沙利文；中国城市公共交通协会《2024 全国网约车市场年报》；曹操出行招股书 (2025)")

# ============ Slide 3 — 赛道经济学 ============
s = slide()
title_bar(s, "赛道经济学：聚合平台崛起重塑非头部玩家的利润结构",
          "自营重资产 vs 聚合轻流量——曹操的增长越来越依赖买流量")
data = [
    ["曹操 GTV 中来自聚合平台的占比", "2022", "2023", "2024"],
    ["聚合平台占比", "49.9%", "73.2%", "85.4%"],
]
add_table(s, 0.5, 1.8, 7.2, 0.9, data, col_w=[3.6,1.2,1.2,1.2],
          num_cols={1,2,3})
tb = box(s, 0.5, 3.0, 12.3, 3.6)
for txt, b in [
    ("价值链怎么分钱", True),
    ("• 自营模式（曹操、T3、如祺）：自建/定制车队 + 自有司机，重资产、重运营，但单均掌控力强、数据自有", False),
    ("• 聚合模式（高德、百度）：不持有运力，向中小平台导流抽佣，轻资产、高毛利，卡住流量入口", False),
    ("• 结构性矛盾：非头部自营平台为冲规模，被迫上聚合买单量 → 曹操聚合占比 3 年从 50% 升到 85%", False),
    ("• 后果：流量成本被高德/百度拿捏，自营运力的成本优势被导流抽佣侵蚀，是当前持续亏损的核心症结之一", False),
    ("• 曹操的破局尝试：定制车（降 TCO）+ 自动驾驶（去司机成本），但兑现需时间", False),
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 16 if b else 14, NAVY if b else GRAY, b)
    p.space_after = Pt(10)
footnote(s, "来源：曹操出行招股书 (2025)；36氪《网约车老二将上市，还被高德和百度拿捏了》")

# ============ Slide 4 — 公司画像 ============
s = slide()
title_bar(s, "曹操出行公司画像：增长稳、亏损收窄，但仍未盈利",
          "吉利系网约车平台 · 2025 年 6 月港交所上市，市值约 190 亿港元")
data = [
    ["指标", "2024 数值", "同比 / 备注"],
    ["营业收入", "¥146.6 亿", "+37.4% YoY"],
    ["GTV (总交易额)", "¥170 亿", "+38.8% YoY"],
    ["订单量", "6.0 亿单", "+33.6% YoY"],
    ["毛利率", "8.1%", "2022/23: -4.4% / 5.8%"],
    ["调整后净亏损", "¥7.24 亿", "2022 为 ¥16.5 亿，收窄 56%"],
    ["市场份额 (GTV)", "5.4%", "行业第二，仅次于滴滴"],
    ["聚合平台占 GTV", "85.4%", "高度依赖第三方导流"],
    ["定制车队", "3.4 万辆 / 31 城", "占订单 GTV 25.1%"],
]
add_table(s, 0.5, 1.8, 7.4, 4.6, data, col_w=[2.9,2.3,2.2], num_cols={1})
tb = box(s, 8.2, 1.9, 4.7, 4.6)
for txt, b in [
    ("一句话画像", True),
    ("增长确定性强、亏损持续收窄的「出行稀缺标的」，差异化在定制车生态 + 吉利供应链，最大隐患是聚合依赖与盈利时点未明。", False),
    ("", False),
    ("差异化抓手", True),
    ("• 吉利体系定制车（枫叶80V、曹操60）压低整车与运营成本", False),
    ("• 2026 起押注 Robotaxi（「曹操智行」苏州/杭州示范）", False),
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 16 if b else 13, NAVY if b else GRAY, b)
    p.space_after = Pt(8)
footnote(s, "来源：曹操出行招股书及 2024 年报；东吴证券/东方财富证券深度报告 (2025-08/09)")

# ============ Slide 5 — 竞争对手分组 (tier) ============
s = slide()
title_bar(s, "竞争对手分组：四个战略群组，曹操卡位「自营第二梯队」",
          "按市场地位与商业模式划分")
tiers = [
    ("一超", "滴滴出行", "GTV 3,927 亿 · 市占 70.4% · 网络效应最强", ACCENT),
    ("第二梯队（自营）", "曹操出行 · T3出行", "各约 5% 份额 · 重资产自营 · 贴身竞争", NAVY),
    ("中长尾（自营）", "如祺出行 · 享道出行 · 首汽约车 · 万顺叫车", "区域/股东资源驱动 · 规模偏小", RGBColor(0x4A,0x6B,0xA8)),
    ("新物种", "高德聚合 · 百度 · 萝卜快跑(Robotaxi)", "聚合卡流量入口 / 自动驾驶颠覆运力", GRAY),
]
y = 1.85
for name, members, note, col in tiers:
    bar = s.shapes.add_shape(1, Inches(0.5), Inches(y), Inches(2.9), Inches(1.05))
    bar.fill.solid(); bar.fill.fore_color.rgb = col; bar.line.fill.background()
    tf = bar.text_frame; tf.word_wrap = True
    setpara(tf.paragraphs[0], name, 16, WHITE, True, PP_ALIGN.CENTER)
    bx = box(s, 3.6, y+0.02, 9.2, 1.0)
    setpara(bx.text_frame.paragraphs[0], members, 17, NAVY, True)
    p = bx.text_frame.add_paragraph(); setpara(p, note, 13, GRAY)
    y += 1.22
footnote(s, "来源：证券时报《网约车「一超多强」格局稳定》；36氪；公司公告")

# ============ Slide 6 — 雷达图 ============
s = slide()
title_bar(s, "定位雷达图：曹操强在自营与自动驾驶布局，弱在规模与盈利",
          "五维定性打分 (1=弱, 5=强)，作者基于公开数据评估")
cd = CategoryChartData()
cd.categories = ["规模(GTV)", "增长", "盈利能力", "自营化程度", "自动驾驶布局"]
cd.add_series("滴滴",     (5, 3, 4, 2, 4))
cd.add_series("曹操出行", (3, 4, 2, 5, 4))
cd.add_series("T3出行",   (3, 3, 2, 4, 3))
cd.add_series("如祺出行", (2, 3, 2, 3, 4))
gf = s.shapes.add_chart(XL_CHART_TYPE.RADAR, Inches(0.6), Inches(1.7),
                        Inches(7.4), Inches(4.9), cd)
chart = gf.chart
chart.has_legend = True; chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False; chart.legend.font.size = Pt(13)
tb = box(s, 8.3, 1.9, 4.6, 4.6)
for txt, b in [
    ("读图要点", True),
    ("• 曹操（橙）轮廓「偏右」：自营化 + 自动驾驶布局领先，但规模、盈利明显短板", False),
    ("• 滴滴轮廓最大且均衡，规模与盈利碾压", False),
    ("• 曹操 vs T3 高度重叠 → 第二梯队同质化竞争激烈", False),
    ("• 如祺整体内收，规模最小", False),
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 16 if b else 14, NAVY if b else GRAY, b)
    p.space_after = Pt(9)
footnote(s, "打分为作者综合公开数据的定性评估 [E]，非精确量化，仅供相对比较")

# ============ Slide 7 — 对手深挖 滴滴 / T3 ============
s = slide()
title_bar(s, "对手深挖（一）：滴滴 = 规模护城河；T3 = 曹操的镜像对手")
# 滴滴
b1 = box(s, 0.5, 1.7, 6.0, 0.5)
setpara(b1.text_frame.paragraphs[0], "滴滴出行", 18, ACCENT, True)
add_table(s, 0.5, 2.2, 6.0, 1.5, [
    ["指标", "数值"],
    ["GTV / 市占", "¥3,927 亿 / 70.4%"],
    ["GTV 增速", "+16.2% YoY"],
    ["地位", "全国一超，网络效应最强"],
], col_w=[2.6,3.4], num_cols={1})
add_table(s, 0.5, 3.9, 6.0, 2.6, [
    ["维度", "评估"],
    ["优势", "规模/网络效应/数据壁垒；已实现核心业务盈利"],
    ["劣势", "增速放缓；监管与合规历史包袱"],
    ["战略", "守份额、出海、国际化与自动驾驶投入"],
], col_w=[1.6,4.4])
# T3
b2 = box(s, 6.8, 1.7, 6.0, 0.5)
setpara(b2.text_frame.paragraphs[0], "T3出行", 18, NAVY, True)
add_table(s, 6.8, 2.2, 6.0, 1.5, [
    ["指标", "数值"],
    ["市占 (GTV)", "5.3%"],
    ["GTV (估)", "约 ¥165 亿 [E]"],
    ["背景", "一汽/东风/长安 + 腾讯/阿里系"],
], col_w=[2.6,3.4], num_cols={1})
add_table(s, 6.8, 3.9, 6.0, 2.6, [
    ["维度", "评估"],
    ["优势", "央企车厂背书；自营运力与合规优先"],
    ["劣势", "同样依赖聚合；盈利未明，与曹操高度同质"],
    ["战略", "扩城、车路协同与自动驾驶卡位"],
], col_w=[1.6,4.4])
footnote(s, "来源：各公司公告与招股书；T3 GTV 为按 5.3% 份额估算 [E]")

# ============ Slide 8 — 对手深挖 如祺 / 曹操自评 ============
s = slide()
title_bar(s, "对手深挖（二）：如祺规模小但增长稳；曹操凭定制车差异化")
b1 = box(s, 0.5, 1.7, 6.0, 0.5)
setpara(b1.text_frame.paragraphs[0], "如祺出行 (09680.HK)", 18, RGBColor(0x4A,0x6B,0xA8), True)
add_table(s, 0.5, 2.2, 6.0, 1.5, [
    ["指标", "数值"],
    ["GTV", "¥29.79 亿 (+8.7%)"],
    ["订单量", "1.13 亿单 (+15.7%)"],
    ["出行服务收入", "¥21.99 亿 (+21.2%)"],
], col_w=[2.8,3.2], num_cols={1})
add_table(s, 0.5, 3.9, 6.0, 2.6, [
    ["维度", "评估"],
    ["优势", "广汽背书 + 文远知行 Robotaxi 协同；增长稳"],
    ["劣势", "规模最小，盈利压力大"],
    ["战略", "Robotaxi 运营 + 出海"],
], col_w=[1.6,4.4])
b2 = box(s, 6.8, 1.7, 6.0, 0.5)
setpara(b2.text_frame.paragraphs[0], "曹操出行（本体）", 18, ACCENT, True)
add_table(s, 6.8, 2.2, 6.0, 1.5, [
    ["指标", "数值"],
    ["GTV / 订单", "¥170 亿 / 6.0 亿单"],
    ["毛利率", "8.1% (持续改善)"],
    ["调整后净亏损", "¥7.24 亿 (收窄 56%)"],
], col_w=[2.8,3.2], num_cols={1})
add_table(s, 6.8, 3.9, 6.0, 2.6, [
    ["维度", "评估"],
    ["优势", "吉利定制车降本；规模第二；亏损收窄"],
    ["劣势", "聚合依赖 85%；高负债；尚未盈利"],
    ["战略", "定制车 + Robotaxi（2026 起）双押注"],
], col_w=[1.6,4.4])
footnote(s, "来源：如祺出行 2024 年报（证券时报）；曹操出行招股书及年报")

# ============ Slide 9 — 横向打分 ============
s = slide()
title_bar(s, "横向打分对比：曹操规模领先同梯队，但盈利与流量自主性垫底",
          "●●● 强 / ●●○ 中 / ●○○ 弱")
add_table(s, 0.5, 1.9, 12.3, 4.4, [
    ["维度", "滴滴", "曹操出行", "T3出行", "如祺出行"],
    ["规模 (GTV)", "●●● 3,927亿", "●●○ 170亿", "●●○ ~165亿[E]", "●○○ 30亿"],
    ["增长", "●●○ +16%", "●●● +39%", "●●○ 中", "●●○ +9%"],
    ["盈利能力", "●●● 已盈利", "●○○ 仍亏损", "●○○ 仍亏损", "●○○ 仍亏损"],
    ["自营化程度", "●○○ 偏聚合/混合", "●●● 定制车", "●●○ 自营", "●●○ 自营"],
    ["流量自主性", "●●● 自有入口", "●○○ 聚合85%", "●○○ 依赖聚合", "●●○ 股东导流"],
    ["自动驾驶布局", "●●○ 自研", "●●○ 2026落地", "●●○ 卡位", "●●○ 文远协同"],
], col_w=[2.5,2.45,2.45,2.45,2.45])
footnote(s, "评分为相对定性比较 [E]；规模为 2024 GTV，T3 为份额估算")

# ============ Slide 10 — 护城河与软肋 ============
s = slide()
title_bar(s, "护城河与软肋：差异化在「车」，风险在「流量」与「盈利」")
# moat
m = s.shapes.add_shape(1, Inches(0.5), Inches(1.8), Inches(6.0), Inches(0.55))
m.fill.solid(); m.fill.fore_color.rgb = NAVY; m.line.fill.background()
setpara(m.text_frame.paragraphs[0], "护城河（可持续优势）", 16, WHITE, True, PP_ALIGN.CENTER)
tb = box(s, 0.5, 2.45, 6.0, 4.0)
for txt in [
    "• 规模经济：定制车 3.4万辆 + 吉利供应链，整车与维保 TCO 显著低于采购社会运力",
    "• 无形资产：吉利集团背书、自有运营数据、网约车牌照资质",
    "• 切换成本（弱）：司机/乘客忠诚度有限，主要靠补贴与定制车绑定司机",
    "• 前瞻布局：Robotaxi「曹操智行」卡位，长期有去司机成本的期权价值",
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 14, NAVY); p.space_after = Pt(10)
# risk
r = s.shapes.add_shape(1, Inches(6.9), Inches(1.8), Inches(6.0), Inches(0.55))
r.fill.solid(); r.fill.fore_color.rgb = ACCENT; r.line.fill.background()
setpara(r.text_frame.paragraphs[0], "软肋（结构性脆弱点）", 16, WHITE, True, PP_ALIGN.CENTER)
tb = box(s, 6.9, 2.45, 6.0, 4.0)
for txt in [
    "• 聚合依赖：85.4% GTV 来自高德/百度，流量成本被卡，议价权弱",
    "• 尚未盈利：调整后仍亏 7.24 亿，盈利时点未明",
    "• 高负债：上市前财务杠杆偏高，现金流承压",
    "• 同质竞争：与 T3 高度重叠，第二梯队缺乏决定性差距",
    "• Robotaxi 不确定性：投入大、监管与商业化兑现需时间",
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 14, NAVY); p.space_after = Pt(10)
footnote(s, "来源：综合招股书、券商研报与公开报道的作者判断")

# ============ Slide 11 — 投资情景 ============
s = slide()
title_bar(s, "投资情景：核心变量是「能否降低聚合依赖 + 兑现盈利」",
          "牛 / 中 / 熊三情景（演示性判断，非投资建议）")
add_table(s, 0.5, 1.9, 12.3, 3.0, [
    ["情景", "概率", "关键驱动", "结果含义"],
    ["牛市", "25%", "定制车+自营单量上量、聚合占比回落，2026E 接近盈亏平衡，Robotaxi 兑现", "市占向 7%+，估值重估为「盈利成长股」"],
    ["中性", "50%", "维持 +30%+ 增长、亏损继续收窄，但聚合依赖与流量成本难根治", "稳坐第二，盈利时点后移，估值随增长波动"],
    ["熊市", "25%", "补贴战重燃 / 聚合抽佣上升 / Robotaxi 投入拖累，盈利遥遥无期", "份额被 T3、聚合侵蚀，持续融资稀释"],
], col_w=[1.3,1.0,5.5,4.5], num_cols={1})
tb = box(s, 0.5, 5.2, 12.3, 1.4)
setpara(tb.text_frame.paragraphs[0], "盯盘信号（量化）", 16, NAVY, True)
for txt in [
    "✓ 每季「聚合平台 GTV 占比」是否下降（>85% 恶化 / <80% 改善）   ✓ 调整后净亏损率是否持续收窄   ✓ 定制车占订单 GTV 是否上升   ✓ Robotaxi 落地城市数与单量",
]:
    p = tb.text_frame.add_paragraph(); setpara(p, txt, 13, GRAY)
footnote(s, "本页为演示性情景分析，不构成投资建议。概率为作者主观假设 [E]")

# ============ Slide 12 — sources ============
s = slide()
title_bar(s, "数据来源与免责声明")
tb = box(s, 0.5, 1.8, 12.3, 4.8)
for txt, b in [
    ("主要来源", True),
    ("• 曹操出行招股书 (2025) 及 2024 年报", False),
    ("• 弗若斯特沙利文 (Frost & Sullivan) 行业数据", False),
    ("• 中国城市公共交通协会《2024 全国网约车市场年报》", False),
    ("• 东吴证券、东方财富证券曹操出行深度报告 (2025-08/09)", False),
    ("• 证券时报、36氪、IT之家、澎湃新闻等公开报道", False),
    ("• 如祺出行 (09680.HK) 2024 年报", False),
    ("", False),
    ("免责声明", True),
    ("本演示文稿由 AI 基于公开来源整理，部分指标为估算 [E] 或定性判断，可能存在误差或时效偏差；不构成任何投资建议。投资决策请以公司正式披露文件为准。", False),
]:
    p = tb.text_frame.add_paragraph() if tb.text_frame.paragraphs[0].text else tb.text_frame.paragraphs[0]
    setpara(p, txt, 16 if b else 13, NAVY if b else GRAY, b); p.space_after = Pt(6)

out = "/home/user/King/曹操出行_竞争格局分析.pptx"
prs.save(out)
print("saved:", out, "slides:", len(prs.slides._sldIdLst))
