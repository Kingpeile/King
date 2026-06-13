# -*- coding: utf-8 -*-
"""MiniMax (00100.HK) — 财报前瞻 + 10年DCF + 大模型(六小龙)竞争格局 整合报告。"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

# ---------------- DCF computation (10-year explicit) ----------------
YEARS   = list(range(2026, 2036))                                   # 2026..2035
REV     = [174,322,515,747,1008,1311,1639,2049,2459,2950]           # US$M
GROWTH  = ["+120%","+85%","+60%","+45%","+35%","+30%","+25%","+25%","+20%","+20%"]
MARGIN  = [-1.50,-0.70,-0.25,0.0,0.08,0.15,0.20,0.23,0.25,0.26]
TAX     = 0.15
def fcf_series(rev, margin):
    out=[]
    for r,m in zip(rev,margin):
        ebit=r*m
        out.append(ebit if ebit<0 else ebit*(1-TAX))
    return out
FCF=[round(x) for x in fcf_series(REV,MARGIN)]
def dcf_ev(wacc, g, fcf=FCF):
    pv=sum(f/((1+wacc)**(i+1)) for i,f in enumerate(fcf))
    tv=fcf[-1]*(1+g)/(wacc-g)
    pv_tv=tv/((1+wacc)**len(fcf))
    return pv, pv_tv, pv+pv_tv
PV_EXP, PV_TV, EV_BASE = dcf_ev(0.15,0.04)
NET_CASH=700
EQUITY_BASE = EV_BASE+NET_CASH
SENS={}
for w in (0.13,0.15,0.17):
    for g in (0.03,0.04,0.05):
        SENS[(w,g)]=dcf_ev(w,g)[2]

# ---------------- styling ----------------
NAVY=RGBColor(0x16,0x21,0x3E); GRAY=RGBColor(0x6B,0x70,0x7B); LGRAY=RGBColor(0xE9,0xEB,0xEF)
ACCENT=RGBColor(0x2E,0x86,0xC1); GREEN=RGBColor(0x2E,0x8B,0x57); RED=RGBColor(0xC0,0x39,0x2B)
BLUE2=RGBColor(0x5D,0x6D,0x9E); GOLD=RGBColor(0xB8,0x86,0x0B); WHITE=RGBColor(0xFF,0xFF,0xFF)
FONT="Microsoft YaHei"

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
BLANK=prs.slide_layouts[6]; SW,SH=prs.slide_width,prs.slide_height
def slide(): return prs.slides.add_slide(BLANK)
def box(s,l,t,w,h):
    tb=s.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h)); tb.text_frame.word_wrap=True; return tb
def setp(p,text,size,color=NAVY,bold=False,align=PP_ALIGN.LEFT):
    p.text=text; p.alignment=align
    for r in p.runs:
        r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name=FONT
    return p
def title_bar(s,title,kicker=None):
    bar=s.shapes.add_shape(1,0,0,SW,Inches(0.12)); bar.fill.solid(); bar.fill.fore_color.rgb=ACCENT; bar.line.fill.background()
    tb=box(s,0.5,0.24,12.4,1.0); setp(tb.text_frame.paragraphs[0],title,25,NAVY,True)
    if kicker:
        setp(tb.text_frame.add_paragraph(),kicker,13.5,GRAY)
def section_tag(s,txt,color=ACCENT):
    t=s.shapes.add_shape(1,Inches(11.05),Inches(0.30),Inches(1.95),Inches(0.42))
    t.fill.solid(); t.fill.fore_color.rgb=color; t.line.fill.background()
    setp(t.text_frame.paragraphs[0],txt,12,WHITE,True,PP_ALIGN.CENTER)
def foot(s,text):
    setp(box(s,0.5,7.06,12.4,0.4).text_frame.paragraphs[0],text,9,GRAY)
def bullets(s,l,t,w,h,items,base=14):
    tb=box(s,l,t,w,h); first=True
    for txt,b in items:
        p=tb.text_frame.paragraphs[0] if first else tb.text_frame.add_paragraph(); first=False
        setp(p,txt,16 if b else base,NAVY if b else GRAY,b); p.space_after=Pt(7)
    return tb
def table(s,l,t,w,h,data,col_w=None,num_cols=None,fs=12.5,hfs=12.5):
    rows,cols=len(data),len(data[0])
    g=s.shapes.add_table(rows,cols,Inches(l),Inches(t),Inches(w),Inches(h)).table
    if col_w:
        for i,cw in enumerate(col_w): g.columns[i].width=Inches(cw)
    num_cols=num_cols or set()
    for r in range(rows):
        for c in range(cols):
            cell=g.cell(r,c)
            cell.margin_left=Inches(0.06); cell.margin_right=Inches(0.06)
            cell.margin_top=Inches(0.02); cell.margin_bottom=Inches(0.02)
            cell.vertical_anchor=MSO_ANCHOR.MIDDLE
            p=cell.text_frame.paragraphs[0]; cell.text_frame.word_wrap=True; p.text=str(data[r][c])
            head=(r==0)
            for run in p.runs:
                run.font.size=Pt(hfs if head else fs); run.font.bold=head; run.font.name=FONT
                run.font.color.rgb=WHITE if head else NAVY
            if head:
                cell.fill.solid(); cell.fill.fore_color.rgb=NAVY; p.alignment=PP_ALIGN.LEFT
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb=WHITE if r%2 else LGRAY
                p.alignment=PP_ALIGN.RIGHT if c in num_cols else PP_ALIGN.LEFT
    return g

# ===== 1 Title =====
s=slide()
bg=s.shapes.add_shape(1,0,0,SW,SH); bg.fill.solid(); bg.fill.fore_color.rgb=NAVY; bg.line.fill.background()
s.shapes._spTree.remove(bg._element); s.shapes._spTree.insert(2,bg._element)
acc=s.shapes.add_shape(1,0,Inches(4.55),SW,Inches(0.08)); acc.fill.solid(); acc.fill.fore_color.rgb=ACCENT; acc.line.fill.background()
tb=box(s,0.8,2.2,11.7,2.3); setp(tb.text_frame.paragraphs[0],"MiniMax 稀宇科技 (00100.HK)",38,WHITE,True)
setp(tb.text_frame.add_paragraph(),"财报前瞻 · 10 年 DCF 估值 · 大模型“六小龙”竞争格局",23,ACCENT,True)
tb2=box(s,0.8,4.75,11.7,1.4)
setp(tb2.text_frame.paragraphs[0],"2026-01-09 港交所上市 · 含 智谱 / Kimi / 阶跃星辰 横评",16,LGRAY)
setp(tb2.text_frame.add_paragraph(),"演示版 · 来源：各家招股书、QuestMobile、券商研报、公开报道 · 2026-06 · 不构成投资建议",11,GRAY)

# ===== 2 投资概要 =====
s=slide(); title_bar(s,"投资概要：高增长 To C 出海故事，估值押注的是未来而非当下")
table(s,0.5,1.7,7.0,3.0,[
    ["关键数字","数值"],
    ["上市市值","≈ 461 亿港元 (US$5.9B)"],
    ["2025 营收","US$79.0M (+159% YoY)"],
    ["三年营收 CAGR","≈ 378% (2023-25)"],
    ["海外收入占比","≈ 73%"],
    ["盈利状态","持续大额亏损，未盈利"],
    ["EV/Sales (TTM)","≈ 75x（极高）"],
],col_w=[2.8,4.2],num_cols={1})
bullets(s,7.8,1.75,5.1,4.8,[
    ("一句话判断",True),
    ("数据扎实：营收高增、To C + 出海差异化、多模态（视频/语音/陪伴）产品矩阵领先。",False),
    ("最大争议：$79M 收入撑 ~US$6B 市值 = 75x P/S，价值几乎全压在 2030+ 的规模与盈利兑现上。",False),
    ("即便把 DCF 显性期拉到 10 年（见后），估值仍只到市值约 40%——这是一笔“长期期权”。",False),
])
foot(s,"来源：MiniMax 招股书 (2025-12)；量子位《作价461亿港元募资46亿》；新浪财经《上市后首份成绩单》")

# ===== 3 公司画像 =====
s=slide(); title_bar(s,"公司画像：385 人的“最快 IPO”，研发投入仅 OpenAI 的约 1%",
                     "2022 年由前商汤副总裁闫俊杰创立，多模态全栈自研")
table(s,0.5,1.85,7.2,4.4,[
    ["维度","内容"],
    ["代码 / 上市","00100.HK / 2026-01-09"],
    ["核心产品","海螺AI(视频/语音)、Talkie·星野(AI陪伴)、MiniMax Agent、开放平台 API"],
    ["旗舰模型","MiniMax M1/M2.5、Hailuo-02、Speech-02、Music-01"],
    ["用户规模","2.36 亿个人用户 / 21.4 万企业客户 / 200+ 国家"],
    ["国内月活","≈ 2,760 万 (9M2025 均值)"],
    ["团队","385 人，平均 29 岁，研发占 ≈74%"],
    ["主要股东","阿里 13.66% / 米哈游 6.4% / 腾讯 2.58% / 红杉·IDG·高瓴"],
],col_w=[1.9,5.3])
bullets(s,7.9,1.9,5.0,4.6,[
    ("定位关键词",True),
    ("• To C 为主：约七成收入来自消费级 AI 产品（区别于智谱的 To B）",False),
    ("• 出海优先：海螺/Talkie 主攻海外，美国+新加坡为最大单一市场",False),
    ("• 多模态领先：文本/语音/图像/视频/音乐全覆盖",False),
    ("• 性价比打法：M2.5 以低 API 价格+快响应抢开发者",False),
])
foot(s,"来源：InfoQ《385人、平均95后…研发成本仅为OpenAI的1%》；招股书；澎湃新闻")

# ===== 4 财务表现 =====
s=slide(); title_bar(s,"财务表现：收入三年翻数十倍，但仍深度亏损","营收单位：US$ 百万")
cd=CategoryChartData(); cd.categories=["2023","2024","2025"]; cd.add_series("营收 (US$M)",(3.46,30.52,79.04))
gf=s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(0.5),Inches(1.8),Inches(6.4),Inches(4.6),cd)
ch=gf.chart; ch.has_legend=False; pl=ch.plots[0]; pl.has_data_labels=True
pl.data_labels.font.size=Pt(12); pl.data_labels.font.bold=True
pl.data_labels.number_format='0.0'; pl.data_labels.number_format_is_linked=False
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb=ACCENT
bullets(s,7.2,1.85,5.7,4.7,[
    ("增长与亏损并存",True),
    ("• 营收 2023 $3.5M → 2024 $30.5M (+782%) → 2025 $79.0M (+159%)",False),
    ("• 2025 结构：AI 原生产品 $53.1M (67%)，开放平台/企业 $26.0M (33%)",False),
    ("• 招股书披露年度净亏损达数十亿元级 [含优先股公允价值变动等非现金项]",False),
    ("• 现金消耗主因：模型训练算力 + 海外获客投放",False),
    ("• 毛利与单位经济仍未跑通，盈利时点是核心未知数",False),
])
foot(s,"来源：MiniMax 招股书；证券时报《收入增长近8倍、年亏损32亿》；21经济网")

# ===== 5 财报前瞻假设 =====
s=slide(); title_bar(s,"【财报前瞻】下一财报核心假设：增速换挡 + 亏损率收窄是关键看点")
section_tag(s,"① 财报前瞻",ACCENT)
table(s,0.5,1.85,12.3,2.4,[
    ["假设项","熊 (悲观)","中性 (基准)","牛 (乐观)"],
    ["2026E 营收增速","+70%","+120%","+170%"],
    ["2026E 营收 (US$M)","134","174","213"],
    ["海外收入占比","持平 ~73%","升至 ~76%","升至 ~80%"],
    ["毛利率趋势","承压","小幅改善","明显改善"],
    ["经营亏损率","基本持平","收窄 20-30pct","大幅收窄"],
],col_w=[2.7,3.2,3.2,3.2],num_cols={1,2,3})
bullets(s,0.5,4.5,12.3,2.2,[
    ("前瞻逻辑",True),
    ("• 增长来源：海螺AI 视频付费转化、Talkie 海外月活变现、MiniMax Agent 企业渗透、开放平台 token 调用量",False),
    ("• 最该盯的不是收入（高增已被 price-in），而是亏损率与毛利率拐点——决定市场愿不愿意继续给高 P/S",False),
],13)
foot(s,"假设为演示性 [E]，非公司指引。基准以 9M2025 增速 +170% 自然换挡外推")

# ===== 6 财报前瞻盯盘 =====
s=slide(); title_bar(s,"【财报前瞻】盯盘信号清单：用季度数据验证多空逻辑")
section_tag(s,"① 财报前瞻",ACCENT)
table(s,0.5,1.85,12.3,3.6,[
    ["指标","看多信号 (逻辑兑现)","看空信号 (逻辑证伪)"],
    ["营收增速","维持 ≥100% YoY","跌破 70%，增长失速"],
    ["经营亏损率","逐季收窄","持平或扩大（烧钱换增长）"],
    ["海外收入占比","稳定上升","回落（出海受阻/合规风险）"],
    ["付费用户 & ARPU","Talkie/海螺付费数与单价齐升","付费转化停滞"],
    ["毛利率","随规模与自研算力改善","被算力成本侵蚀"],
    ["企业/开放平台收入","占比提升，第二曲线成形","停留在 C 端单一依赖"],
],col_w=[2.7,4.8,4.8])
foot(s,"演示性框架；实际以公司正式财报披露口径为准")

# ===== 7 DCF 假设 (10yr) =====
s=slide(); title_bar(s,"【DCF】10 年显性期假设：营收 10 年 ~38x，2029 盈亏平衡、2035 转 26% 利润率")
section_tag(s,"② DCF 估值",GREEN)
hdr=["US$M / 假设"]+[str(y)[2:]+"E" for y in YEARS]
rows=[hdr,
      ["营收"]+[str(x) for x in REV],
      ["增速"]+GROWTH,
      ["经营利润率"]+[("%d%%"%round(m*100)) for m in MARGIN],
      ["自由现金流"]+[("%+d"%f) for f in FCF]]
cw=[2.2]+[1.01]*10
table(s,0.4,1.85,12.5,2.6,rows,col_w=cw,num_cols=set(range(1,11)),fs=10,hfs=10)
bullets(s,0.5,4.7,12.3,2.0,[
    ("假设说明",True),
    ("• 利润率路径：2026 深度为负 → 2029 盈亏平衡 → 2035 达 26% 经营利润率（对标成熟平台型软件）",False),
    ("• 终值：以 2035 FCF 永续增长 g=4%、WACC=15%、盈利后税率 15% 计算",False),
],13)
foot(s,"全部为演示性假设 [E]；早期 AI 公司 10 年预测误差极大，仅用于展示估值框架")

# ===== 8 DCF 结果 + 敏感性 (10yr) =====
s=slide(); title_bar(s,"【DCF】结论：10 年 DCF 股权价值 ≈US$%.1fB，仍只到 ~US$5.9B 市值的约 40%%"%(EQUITY_BASE/1000))
section_tag(s,"② DCF 估值",GREEN)
table(s,0.5,1.8,5.6,2.3,[
    ["估值结果","US$M"],
    ["显性期 FCF 现值合计","%+d"%round(PV_EXP)],
    ["终值现值","%+d"%round(PV_TV)],
    ["企业价值 (EV)","≈ %d"%round(EV_BASE)],
    ["+ 净现金 [E]","≈ %d"%NET_CASH],
    ["股权价值","≈ %d"%round(EQUITY_BASE)],
],col_w=[3.4,2.2],num_cols={1})
setp(box(s,0.5,4.25,5.6,0.4).text_frame.paragraphs[0],"敏感性：EV (US$M) — WACC × 终值增长 g",12.5,NAVY,True)
table(s,0.5,4.7,5.6,1.7,[
    ["WACC＼g","3%","4%","5%"],
    ["13%","%d"%round(SENS[(0.13,0.03)]),"%d"%round(SENS[(0.13,0.04)]),"%d"%round(SENS[(0.13,0.05)])],
    ["15%","%d"%round(SENS[(0.15,0.03)]),"%d"%round(SENS[(0.15,0.04)]),"%d"%round(SENS[(0.15,0.05)])],
    ["17%","%d"%round(SENS[(0.17,0.03)]),"%d"%round(SENS[(0.17,0.04)]),"%d"%round(SENS[(0.17,0.05)])],
],col_w=[1.6,1.33,1.33,1.33],num_cols={1,2,3},fs=11,hfs=11)
bullets(s,6.4,1.85,6.5,5.0,[
    ("把显性期从 7 年拉到 10 年后",True),
    ("• 企业价值从 ~$0.7B 升到 ≈$%.1fB，股权价值 ≈$%.1fB——确实更接近，但仍只有市值约 40%%。"%(EV_BASE/1000,EQUITY_BASE/1000),False),
    ("• 多出来的价值几乎全来自 2030 年后的盈利年份与更高终值，前 4 年 FCF 依旧为负。",False),
    ("• 即便最乐观格 (WACC 13%% × g 5%%) 也才 ~$%.1fB EV，仍低于市值。"%(SENS[(0.13,0.05)]/1000),False),
    ("• 结论不变：现金流折现解释不了市场定价，MiniMax 是“长期期权”而非“现金流标的”。",False),
])
foot(s,"演示性测算 [E]；净现金为粗略估计，应以最新资产负债表为准")

# ===== 9 反推 + 倍数 =====
s=slide(); title_bar(s,"【DCF】市场到底 price-in 了什么？反推法 + 倍数交叉验证")
section_tag(s,"② DCF 估值",GREEN)
bullets(s,0.5,1.8,6.2,4.8,[
    ("反推 DCF：要撑起 ~US$5.9B，需要相信——",True),
    ("• 营收到 2035 远超本模型的 ~$3B（需更陡的长尾增长）",False),
    ("• 或终值利润率升到 30%+、WACC 降到 ~12%",False),
    ("• 即“再造一个区域级多模态 AI 平台”，容错率极低",False),
    ("",False),
    ("换言之：当前价格 = 对“中国版多模态 AI 赢家”的看涨期权",True),
])
table(s,6.9,1.95,6.0,3.2,[
    ["倍数交叉验证","数值"],
    ["EV/Sales (2025A)","≈ 75x"],
    ["EV/Sales (2026E 基准)","≈ 34x"],
    ["对比：成熟 SaaS","5-15x"],
    ["对比：高增 AI 私募轮","20-40x"],
    ["隐含定价","顶格高增长预期"],
],col_w=[3.6,2.4],num_cols={1})
bullets(s,6.9,5.3,6.0,1.3,[
    ("• 75x TTM P/S 已计入“完美执行”，留给意外的安全边际很小",False),
],13)
foot(s,"反推与倍数均为演示性 [E]；旨在说明定价逻辑，非精确目标价")

# ===== 10 市场地图 =====
s=slide(); title_bar(s,"【竞争格局】大厂流量碾压，“六小龙”靠差异化求生","国内月活 MAU（百万），2025 口径")
section_tag(s,"③ 竞争格局",BLUE2)
cd=CategoryChartData(); cd.categories=["豆包(字节)","DeepSeek","腾讯元宝","MiniMax","即梦AI","Kimi"]
cd.add_series("MAU(百万)",(172,145,32.9,27.6,10.1,9.7))
gf=s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED,Inches(0.5),Inches(1.8),Inches(6.6),Inches(4.7),cd)
ch=gf.chart; ch.has_legend=False; pl=ch.plots[0]; pl.has_data_labels=True
pl.data_labels.font.size=Pt(11); pl.data_labels.font.bold=True
pl.data_labels.number_format='0.0'; pl.data_labels.number_format_is_linked=False
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb=BLUE2
pts=pl.series[0].points; pts[3].format.fill.solid(); pts[3].format.fill.fore_color.rgb=ACCENT
bullets(s,7.4,1.85,5.5,4.8,[
    ("格局速读",True),
    ("• 第一梯队是大厂：豆包(字节)、DeepSeek 流量断层领先",False),
    ("• “AI 六小龙”光环褪去：智谱、MiniMax 抢先 IPO；Kimi、阶跃冲营收；百川、零一转垂类",False),
    ("• MiniMax 国内 MAU 不占优 → 牌不在国内流量，而在海外 To C + 多模态",False),
])
foot(s,"来源：QuestMobile；新浪财经《年终盘点|大模型洗牌》；财联社")

# ===== 11 MiniMax SWOT =====
s=slide(); title_bar(s,"【竞争格局】MiniMax 差异化打法：避开国内流量战，打海外多模态")
section_tag(s,"③ 竞争格局",BLUE2)
quad=[("差异化优势",GREEN,["海外 To C 变现领先（Talkie/海螺）","多模态全栈（视频/语音/音乐）自研","M2.5 性价比抢开发者生态"]),
      ("劣势 / 短板",RED,["国内流量远不及大厂","C 端依赖度高，第二曲线待证","品牌认知弱于 DeepSeek/豆包"]),
      ("机会",ACCENT,["全球 AI 陪伴/视频创作渗透","企业级 Agent + 开放平台放量","Token 出海风口"]),
      ("威胁",BLUE2,["大厂补贴与免费策略挤压","海外合规/地缘风险","开源模型(DeepSeek/Qwen)拉低付费意愿"])]
xs=[0.5,6.9]; ys=[1.8,4.2]
for i,(name,col,items) in enumerate(quad):
    l=xs[i%2]; t=ys[i//2]
    bar=s.shapes.add_shape(1,Inches(l),Inches(t),Inches(6.0),Inches(0.48)); bar.fill.solid(); bar.fill.fore_color.rgb=col; bar.line.fill.background()
    setp(bar.text_frame.paragraphs[0],name,15,WHITE,True,PP_ALIGN.CENTER)
    tb=box(s,l+0.05,t+0.52,5.9,1.7); first=True
    for it in items:
        p=tb.text_frame.paragraphs[0] if first else tb.text_frame.add_paragraph(); first=False
        setp(p,"• "+it,13,NAVY); p.space_after=Pt(4)
foot(s,"SWOT 为基于公开信息的演示性判断")

# ===== 12 主要对手对比 (含阶跃) =====
s=slide(); title_bar(s,"【竞争格局】主要对手对比：大厂 + 六小龙，模式与上市路径各异")
section_tag(s,"③ 竞争格局",BLUE2)
table(s,0.5,1.85,12.3,4.5,[
    ["公司","定位/模式","流量(MAU)","上市状态","对 MiniMax 的意义"],
    ["豆包(字节)","闭源MoE，To B，火山引擎","1.72 亿","大厂自有","流量与算力碾压，定价压制"],
    ["DeepSeek","开源高性能，性价比标杆","1.45 亿","未上市","拉低付费意愿，抢开发者心智"],
    ["智谱 AI","To B 本地化部署(84%)","中等","通过聆讯,冲第一股","“大模型第一股”直接对标"],
    ["月之暗面(Kimi)","C端+Agent/深度研究","967 万","未上市(估值飙升)","争“下一个DeepSeek”，Agent 卡位"],
    ["阶跃星辰","多模态 + AI 终端","偏 B/终端","计划年内港股","多模态正面对手，吉利系资本"],
    ["通义千问(阿里)","开源Qwen + 云","大","大厂自有","阿里既是股东又是竞品"],
],col_w=[1.9,3.2,1.45,2.15,3.6],fs=11,hfs=11)
foot(s,"来源：各家招股书/融资公告；人人都是产品经理《2026国产大模型选型地图》；财联社")

# ===== 13 雷达图 =====
s=slide(); title_bar(s,"【竞争格局】五维定位：MiniMax 强在多模态与出海，弱在流量与盈利",
                     "定性打分 1=弱 5=强（作者评估 [E]）")
section_tag(s,"③ 竞争格局",BLUE2)
cd=CategoryChartData(); cd.categories=["国内流量","海外/出海","多模态能力","商业化变现","盈利能力"]
cd.add_series("MiniMax",(2,5,5,3,2)); cd.add_series("豆包",(5,3,4,4,4))
cd.add_series("DeepSeek",(4,4,3,2,3)); cd.add_series("智谱",(3,2,4,3,2))
gf=s.shapes.add_chart(XL_CHART_TYPE.RADAR,Inches(0.6),Inches(1.85),Inches(7.2),Inches(4.7),cd)
ch=gf.chart; ch.has_legend=True; ch.legend.position=XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout=False; ch.legend.font.size=Pt(12)
bullets(s,8.1,1.95,4.8,4.5,[
    ("读图要点",True),
    ("• MiniMax(蓝)轮廓“偏出海+多模态”，国内流量与盈利是凹点",False),
    ("• 豆包轮廓最大且均衡，全维度领先",False),
    ("• 智谱内收，强在多模态/技术、弱在出海与盈利",False),
    ("• 各家形状差异大 → 分赛道卡位，而非同质竞争",False),
])
foot(s,"打分为作者综合公开数据的定性评估 [E]，仅供相对比较")

# ===== 14 六小龙横评 (新) =====
s=slide(); title_bar(s,"【竞争格局】“六小龙”横评：营收、估值、模式与 IPO 路径")
section_tag(s,"③ 竞争格局",BLUE2)
table(s,0.4,1.8,12.55,3.7,[
    ["公司","模式","营收","最新估值","IPO 状态","差异化标签"],
    ["智谱 AI","To B 本地化(84%)","¥3.12亿 (24A)","≈¥244亿 (~$3.4B)","通过聆讯,冲第一股","中国版OpenAI/政企"],
    ["MiniMax","To C 出海(海外73%)","$79M (~¥5.7亿,25A)","≈US$5.9B","已上市 2026-01","多模态/海螺/Talkie"],
    ["月之暗面(Kimi)","C端 + 通用Agent",">¥5亿 (25); 26E>¥20亿","~US$18-30B [报道]","未上市","长文本→Agent/深度研究"],
    ["阶跃星辰","多模态 + AI终端","~¥5亿 (25); 26E~¥12亿","~US$3-4B (B+轮后)","计划 2026 港股","Step系/万亿参数/吉利系"],
],col_w=[2.0,2.7,2.7,2.45,2.0,2.7],fs=10.5,hfs=10.5)
bullets(s,0.4,5.7,12.55,1.3,[
    ("一句话",True),
    ("• 智谱(To B)与 MiniMax(To C)率先 IPO；Kimi 靠 Agent 估值狂飙但未上市；阶跃押多模态+终端、吉利系加持。",False),
],12.5)
foot(s,"来源：各家招股书/融资报道（智谱·量子位；Kimi·新浪/投资界；阶跃·财经网）。估值含 RMB/USD 混合及部分未证实报道 [E]")

# ===== 14b 营收规模对齐 (USD, 新) =====
s=slide(); title_bar(s,"【竞争格局】营收规模对齐（统一折算 US$M）：四家体量接近，差距在增速与估值",
                     "2025 营收，按 ¥7.2/US$ 折算")
section_tag(s,"③ 竞争格局",BLUE2)
cd=CategoryChartData(); cd.categories=["智谱 (25E)","MiniMax (25A)","Kimi (25)","阶跃 (25)"]
cd.add_series("2025 营收 (US$M)",(97,79,69,69))
gf=s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(0.5),Inches(1.85),Inches(6.6),Inches(4.6),cd)
ch=gf.chart; ch.has_legend=False; pl=ch.plots[0]; pl.has_data_labels=True
pl.data_labels.font.size=Pt(12); pl.data_labels.font.bold=True
pl.data_labels.number_format='0'; pl.data_labels.number_format_is_linked=False
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb=BLUE2
pts=pl.series[0].points; pts[1].format.fill.solid(); pts[1].format.fill.fore_color.rgb=ACCENT
bullets(s,7.4,1.9,5.5,4.7,[
    ("读图要点",True),
    ("• 2025 营收四家都在 ~$70-100M 区间，绝对体量其实接近（智谱略高、MiniMax 次之）",False),
    ("• 口径差异大：MiniMax/Kimi/阶跃偏 C 端规模，智谱偏 To B 项目制收入",False),
    ("• 2026E 增速分化：Kimi >¥20亿(~$278M)、阶跃 ~¥12亿(~$167M)、MiniMax 基准 ~$174M → Kimi 提速最猛",False),
    ("• 估值与营收倒挂：Kimi 估值($18-30B 报道)远超营收体量 → 市场押的是 Agent 故事",False),
])
foot(s,"折算率 ¥7.2/US$。MiniMax 为 2025 实际；智谱按 ~130% 增速外推 [E]；Kimi/阶跃为公司/报道口径。跨家口径不完全可比")

# ===== 15 MiniMax vs 智谱 (新) =====
s=slide(); title_bar(s,"两条 IPO 路线对照：MiniMax 的 To C 出海 vs 智谱的 To B 政企")
table(s,0.5,1.85,12.3,4.6,[
    ["维度","MiniMax (00100.HK)","智谱 AI"],
    ["客户结构","To C 为主 (~70% 消费级)","To B 为主 (84% 本地化部署)"],
    ["市场重心","海外优先 (73% 海外收入)","国内政企 / 国资体系"],
    ["营收 (2024)","$30.5M (~¥2.2亿)","¥3.12 亿"],
    ["营收增速","2025 +159%","三年 CAGR ~130%"],
    ["估值","≈ US$5.9B (上市市值)","≈ ¥244 亿 (~$3.4B)"],
    ["上市进度","已上市 2026-01-09","通过聆讯，冲“第一股”"],
    ["代表模型","多模态(海螺视频/语音)","GLM 系(通用+推理)"],
    ["核心风险","C端获客成本 / 海外合规","项目制毛利 / 回款 / G端依赖"],
],col_w=[2.3,5.0,5.0])
foot(s,"来源：MiniMax 招股书；智谱招股书（量子位/智东西解读）。两者口径与币种不同，仅作模式对照")

# ===== 16 护城河与软肋 =====
s=slide(); title_bar(s,"综合：护城河在“多模态+出海产品力”，软肋在“流量+盈利”")
m=s.shapes.add_shape(1,Inches(0.5),Inches(1.75),Inches(6.0),Inches(0.48)); m.fill.solid(); m.fill.fore_color.rgb=NAVY; m.line.fill.background()
setp(m.text_frame.paragraphs[0],"护城河（可持续优势）",15,WHITE,True,PP_ALIGN.CENTER)
bullets(s,0.5,2.3,6.0,4.2,[
    ("• 产品力：海螺/Talkie 在 AI 视频与情感陪伴的海外心智",False),
    ("• 多模态全栈自研，模型迭代快（M2.5、Hailuo-02）",False),
    ("• 出海先发：73% 海外收入，绕开国内流量血战",False),
    ("• 资本/生态：阿里、腾讯、米哈游战略加持",False),
])
r=s.shapes.add_shape(1,Inches(6.9),Inches(1.75),Inches(6.0),Inches(0.48)); r.fill.solid(); r.fill.fore_color.rgb=ACCENT; r.line.fill.background()
setp(r.text_frame.paragraphs[0],"软肋（结构性风险）",15,WHITE,True,PP_ALIGN.CENTER)
bullets(s,6.9,2.3,6.0,4.2,[
    ("• 持续大额亏损，盈利路径与时点未明",False),
    ("• 国内流量远逊大厂，C 端获客成本高",False),
    ("• 估值 75x P/S，容错空间极小",False),
    ("• 海外合规/地缘 + 开源模型挤压付费意愿",False),
    ("• 阿里等股东同时是竞品（豆包/Qwen/智谱）",False),
])
foot(s,"综合招股书、券商研报与公开报道的作者判断")

# ===== 17 综合情景 =====
s=slide(); title_bar(s,"综合结论：一笔“高赔率、高不确定”的 AI 平台期权")
table(s,0.5,1.8,12.3,3.0,[
    ["情景","概率","核心条件","估值含义"],
    ["牛","25%","海外To C放量+M系列生态成形，2030前路径清晰转盈","重估为区域多模态赢家，上行空间大"],
    ["中","45%","维持高增但盈利后移，烧钱与融资稀释并存","随增长与情绪宽幅震荡，估值难算清"],
    ["熊","30%","增速换挡+大厂/开源挤压+海外受阻，盈利遥遥无期","P/S 大幅压缩，持续融资稀释股东"],
],col_w=[1.1,1.0,5.7,4.5],num_cols={1})
bullets(s,0.5,5.1,12.3,1.6,[
    ("给个人投资者的提醒",True),
    ("• 这不是靠 DCF/财报算清的标的，仓位与风险敞口比“目标价”更重要；把它当高波动成长期权对待。",False),
    ("• 最值得跟踪三件事：① 亏损率拐点 ② 海外收入占比与付费转化 ③ 第二曲线（企业/开放平台）放量。",False),
],12.5)
foot(s,"演示性情景与概率为作者主观假设 [E]，不构成投资建议")

# ===== 18 来源与免责 =====
s=slide(); title_bar(s,"数据来源与免责声明")
bullets(s,0.5,1.8,12.3,5.0,[
    ("主要来源",True),
    ("• MiniMax / 智谱 / 阶跃星辰 港交所招股书及融资公告；月之暗面历轮融资报道",False),
    ("• 量子位、新浪财经、证券时报、21经济网、澎湃新闻、InfoQ、财联社、智东西、投资界、财经网",False),
    ("• QuestMobile（月活）；人人都是产品经理《2026国产大模型选型地图》；Caproasia / Douglas Research",False),
    ("",False),
    ("免责声明",True),
    ("本报告由 AI 基于公开来源整理。财报前瞻、DCF（营收/利润率/WACC/终值）、竞争打分、情景概率及部分同业估值均为",False),
    ("演示性估计或未证实报道 [E]，可能存在重大误差或时效偏差。DCF 对早期亏损 AI 公司参考性有限，已在正文充分提示。",False),
    ("本报告不构成任何投资建议，投资决策请以公司正式披露文件及专业意见为准。",False),
],13)

out="/home/user/King/MiniMax_前瞻_DCF_竞争格局.pptx"
prs.save(out)
print("EV_BASE=%.0f  EQUITY=%.0f  PV_EXP=%.0f  PV_TV=%.0f"%(EV_BASE,EQUITY_BASE,PV_EXP,PV_TV))
print("FCF:",FCF)
print("SENS:",{k:round(v) for k,v in SENS.items()})
print("saved:",out,"slides:",len(prs.slides._sldIdLst))
