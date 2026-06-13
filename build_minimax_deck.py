# -*- coding: utf-8 -*-
"""MiniMax (00100.HK) — 财报前瞻假设 + DCF 估值 + 大模型竞争格局 整合报告。"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION

NAVY   = RGBColor(0x16, 0x21, 0x3E)
GRAY   = RGBColor(0x6B, 0x70, 0x7B)
LGRAY  = RGBColor(0xE9, 0xEB, 0xEF)
ACCENT = RGBColor(0x2E, 0x86, 0xC1)   # blue accent (AI/tech feel)
GREEN  = RGBColor(0x2E, 0x8B, 0x57)
RED    = RGBColor(0xC0, 0x39, 0x2B)
BLUE2  = RGBColor(0x5D, 0x6D, 0x9E)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
FONT   = "Microsoft YaHei"

prs = Presentation()
prs.slide_width  = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height

def slide(): return prs.slides.add_slide(BLANK)
def box(s,l,t,w,h):
    tb=s.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h)); tb.text_frame.word_wrap=True; return tb
def setp(p,text,size,color=NAVY,bold=False,align=PP_ALIGN.LEFT,font=FONT):
    p.text=text; p.alignment=align
    for r in p.runs:
        r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color; r.font.name=font
    return p
def title_bar(s,title,kicker=None):
    bar=s.shapes.add_shape(1,0,0,SW,Inches(0.12)); bar.fill.solid(); bar.fill.fore_color.rgb=ACCENT; bar.line.fill.background()
    tb=box(s,0.5,0.26,12.4,1.0); setp(tb.text_frame.paragraphs[0],title,26,NAVY,True)
    if kicker:
        p=tb.text_frame.add_paragraph(); setp(p,kicker,14,GRAY,False)
def section_tag(s,txt,color=ACCENT):
    t=s.shapes.add_shape(1,Inches(11.0),Inches(0.30),Inches(2.0),Inches(0.45))
    t.fill.solid(); t.fill.fore_color.rgb=color; t.line.fill.background()
    setp(t.text_frame.paragraphs[0],txt,12,WHITE,True,PP_ALIGN.CENTER)
def foot(s,text):
    tb=box(s,0.5,7.04,12.4,0.4); setp(tb.text_frame.paragraphs[0],text,9,GRAY)
def bullets(s,l,t,w,h,items,base=14):
    tb=box(s,l,t,w,h); first=True
    for txt,b in items:
        p=tb.text_frame.paragraphs[0] if first else tb.text_frame.add_paragraph(); first=False
        setp(p,txt,16 if b else base,NAVY if b else GRAY,b); p.space_after=Pt(8)
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
            for m in ('margin_left','margin_right'): setattr(cell,m,Inches(0.07))
            for m in ('margin_top','margin_bottom'): setattr(cell,m,Inches(0.02))
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

# ===== 1. Title =====
s=slide()
bg=s.shapes.add_shape(1,0,0,SW,SH); bg.fill.solid(); bg.fill.fore_color.rgb=NAVY; bg.line.fill.background()
s.shapes._spTree.remove(bg._element); s.shapes._spTree.insert(2,bg._element)
acc=s.shapes.add_shape(1,0,Inches(4.55),SW,Inches(0.08)); acc.fill.solid(); acc.fill.fore_color.rgb=ACCENT; acc.line.fill.background()
tb=box(s,0.8,2.3,11.7,2.2); setp(tb.text_frame.paragraphs[0],"MiniMax 稀宇科技 (00100.HK)",38,WHITE,True)
p=tb.text_frame.add_paragraph(); setp(p,"财报前瞻假设 · DCF 估值 · 大模型竞争格局",24,ACCENT,True)
tb2=box(s,0.8,4.75,11.7,1.4)
setp(tb2.text_frame.paragraphs[0],"2026-01-09 港交所上市 · 全球最快上市 AI 公司 · 阿里/腾讯/米哈游加持",16,LGRAY)
p=tb2.text_frame.add_paragraph(); setp(p,"演示版 · 来源：港交所招股书、QuestMobile、券商研报、公开报道 · 2026-06 · 不构成投资建议",11,GRAY)

# ===== 2. 投资概要 =====
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
    ("数据扎实的部分：营收高增、To C + 出海差异化、多模态（视频/语音/陪伴）产品矩阵领先。",False),
    ("最大争议：$79M 收入撑 ~US$6B 市值 = 75x P/S，价值几乎全压在 2030+ 的规模与盈利兑现上。",False),
    ("传统 DCF 在此失效（见 DCF 章节）——这是一笔“长期期权”，不是现金流折现能算清的标的。",False),
])
foot(s,"来源：MiniMax 招股书 (2025-12)；量子位《作价461亿港元募资46亿》；新浪财经《上市后首份成绩单》")

# ===== 3. 公司画像 =====
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

# ===== 4. 财务表现 (revenue bar) =====
s=slide(); title_bar(s,"财务表现：收入三年翻数十倍，但仍深度亏损","营收单位：US$ 百万")
cd=CategoryChartData(); cd.categories=["2023","2024","2025"]
cd.add_series("营收 (US$M)",(3.46,30.52,79.04))
gf=s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(0.5),Inches(1.8),Inches(6.4),Inches(4.6),cd)
ch=gf.chart; ch.has_legend=False
plot=ch.plots[0]; plot.has_data_labels=True; plot.data_labels.font.size=Pt(12); plot.data_labels.font.bold=True
plot.data_labels.number_format='0.0'; plot.data_labels.number_format_is_linked=False
plot.series[0].format.fill.solid(); plot.series[0].format.fill.fore_color.rgb=ACCENT
bullets(s,7.2,1.85,5.7,4.7,[
    ("增长与亏损并存",True),
    ("• 营收 2023 $3.5M → 2024 $30.5M (+782%) → 2025 $79.0M (+159%)",False),
    ("• 2025 结构：AI 原生产品 $53.1M (67%)，开放平台/企业 $26.0M (33%)",False),
    ("• 招股书披露年度净亏损达数十亿元级 [含优先股公允价值变动等非现金项]",False),
    ("• 现金消耗主因：模型训练算力 + 海外获客投放",False),
    ("• 毛利与单位经济仍未跑通，盈利时点是核心未知数",False),
])
foot(s,"来源：MiniMax 招股书；证券时报《收入增长近8倍、年亏损32亿》；21经济网")

# ===== 5. 财报前瞻：核心假设 =====
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

# ===== 6. 财报前瞻：盯盘指标 =====
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

# ===== 7. DCF：核心假设 =====
s=slide(); title_bar(s,"【DCF】核心假设：7 年显性期 + 终值，WACC 15%（早期中概 AI）")
section_tag(s,"② DCF 估值",GREEN)
table(s,0.5,1.8,12.3,2.7,[
    ["US$M / 假设","26E","27E","28E","29E","30E","31E","32E"],
    ["营收","174","322","515","747","1008","1311","1639"],
    ["营收增速","+120%","+85%","+60%","+45%","+35%","+30%","+25%"],
    ["经营利润率","-150%","-70%","-25%","0%","+8%","+15%","+20%"],
    ["自由现金流 (FCF)","-261","-225","-129","0","+69","+167","+279"],
],col_w=[2.7,1.37,1.37,1.37,1.37,1.37,1.37,1.37],num_cols={1,2,3,4,5,6,7},fs=11.5,hfs=11.5)
bullets(s,0.5,4.7,12.3,2.0,[
    ("假设说明",True),
    ("• 利润率路径：从 2025 深度为负，随规模/自研算力摊薄，2029 盈亏平衡、2032 达 20% 经营利润率",False),
    ("• 终值：2032 FCF 永续增长 g=4%，WACC=15%，税率 15%（盈利后）",False),
],13)
foot(s,"全部为演示性假设 [E]，非公司指引；早期 AI 公司预测误差极大")

# ===== 8. DCF：结果 + 敏感性 =====
s=slide(); title_bar(s,"【DCF】结论：基准 DCF 仅得 ≈US$0.7B 企业价值，远低于 ~US$5.9B 市值")
section_tag(s,"② DCF 估值",GREEN)
table(s,0.5,1.8,5.6,2.2,[
    ["估值结果","US$M"],
    ["显性期 FCF 现值合计","-271"],
    ["终值现值","+992"],
    ["企业价值 (EV)","≈ 721"],
    ["+ 净现金 (IPO募资等)","≈ 700 [E]"],
    ["股权价值","≈ 1,421"],
],col_w=[3.4,2.2],num_cols={1})
b=box(s,0.5,4.2,5.6,0.5); setp(b.text_frame.paragraphs[0],"敏感性：EV (US$M) — WACC × 终值增长 g",13,NAVY,True)
table(s,0.5,4.7,5.6,1.7,[
    ["WACC＼g","3%","4%","5%"],
    ["13%","980","1180","1460"],
    ["15%","600","721","880"],
    ["17%","340","430","540"],
],col_w=[1.6,1.33,1.33,1.33],num_cols={1,2,3},fs=11.5,hfs=11.5)
bullets(s,6.4,1.85,6.5,5.0,[
    ("怎么读这个结果",True),
    ("• 即便用相当乐观的 7 年高增长 + 2032 转 20% 利润率，基准 DCF 股权价值也只有 ≈US$1.4B，仅市值的约 1/4。",False),
    ("• 原因：近端 FCF 深度为负，价值几乎全靠终值；而终值又被高 WACC 折得很薄。",False),
    ("• 结论：传统 DCF 无法解释市场定价 → MiniMax 不是“现金流标的”，而是“长期期权”。",False),
    ("• 这不代表市场错——而是说估值锚点应换成下一页的“反推法”与倍数法。",False),
])
foot(s,"演示性测算 [E]；净现金为粗略估计，应以最新资产负债表为准")

# ===== 9. DCF：反推 + 倍数交叉验证 =====
s=slide(); title_bar(s,"【DCF】市场到底 price-in 了什么？反推法 + 倍数交叉验证")
section_tag(s,"② DCF 估值",GREEN)
bullets(s,0.5,1.8,6.2,4.8,[
    ("反推 DCF：要撑起 ~US$5.9B，需要相信——",True),
    ("• 营收到 2032 年达 ~US$3.5-4B（即 7 年 ~45%+ 复合增速不掉档）",False),
    ("• 且 2032 经营利润率升至 ~25-30%（远超当前为负）",False),
    ("• 即“再造一个区域级 AI 平台”的成功路径，容错率极低",False),
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
foot(s,"反推与倍数均为演示性 [E]；旨在说明“定价逻辑”，非精确目标价")

# ===== 10. 竞争格局：市场地图 (MAU bar) =====
s=slide(); title_bar(s,"【竞争格局】大厂流量碾压，“六小龙”靠差异化求生","国内月活 MAU（百万），2025 口径")
section_tag(s,"③ 竞争格局",BLUE2)
cd=CategoryChartData(); cd.categories=["豆包(字节)","DeepSeek","腾讯元宝","MiniMax","即梦AI","Kimi"]
cd.add_series("MAU(百万)",(172,145,32.9,27.6,10.1,9.7))
gf=s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED,Inches(0.5),Inches(1.8),Inches(6.6),Inches(4.7),cd)
ch=gf.chart; ch.has_legend=False
plot=ch.plots[0]; plot.has_data_labels=True; plot.data_labels.font.size=Pt(11); plot.data_labels.font.bold=True
plot.data_labels.number_format='0.0'; plot.data_labels.number_format_is_linked=False
plot.series[0].format.fill.solid(); plot.series[0].format.fill.fore_color.rgb=BLUE2
pts=plot.series[0].points; pts[3].format.fill.solid(); pts[3].format.fill.fore_color.rgb=ACCENT  # MiniMax highlight
bullets(s,7.4,1.85,5.5,4.8,[
    ("格局速读",True),
    ("• 第一梯队是大厂：豆包(字节)、DeepSeek 流量断层领先",False),
    ("• “AI 六小龙”光环褪去：智谱、MiniMax 抢先 IPO；Kimi、阶跃冲营收；百川、零一转垂类",False),
    ("• MiniMax 国内 MAU 不占优 → 它的牌不在国内流量，而在海外 To C + 多模态",False),
])
foot(s,"来源：QuestMobile；新浪财经《年终盘点|大模型洗牌》；财联社")

# ===== 11. MiniMax 定位 =====
s=slide(); title_bar(s,"【竞争格局】MiniMax 的差异化打法：避开国内流量战，打海外多模态")
section_tag(s,"③ 竞争格局",BLUE2)
quad=[("差异化优势",GREEN,[
        "海外 To C 变现领先（Talkie/海螺）","多模态全栈（视频/语音/音乐）自研","M2.5 性价比抢开发者生态"]),
      ("劣势 / 短板",RED,[
        "国内流量远不及大厂","C 端依赖度高，第二曲线待证","品牌认知弱于 DeepSeek/豆包"]),
      ("机会",ACCENT,[
        "全球 AI 陪伴/视频创作渗透","企业级 Agent + 开放平台放量","Token 出海风口"]),
      ("威胁",BLUE2,[
        "大厂补贴与免费策略挤压","海外合规/地缘风险","开源模型(DeepSeek/Qwen)拉低付费意愿"])]
xs=[0.5,6.9]; ys=[1.85,4.25]
i=0
for name,col,items in quad:
    l=xs[i%2]; t=ys[i//2]
    bar=s.shapes.add_shape(1,Inches(l),Inches(t),Inches(6.0),Inches(0.5))
    bar.fill.solid(); bar.fill.fore_color.rgb=col; bar.line.fill.background()
    setp(bar.text_frame.paragraphs[0],name,15,WHITE,True,PP_ALIGN.CENTER)
    tb=box(s,l+0.05,t+0.55,5.9,1.7); first=True
    for it in items:
        p=tb.text_frame.paragraphs[0] if first else tb.text_frame.add_paragraph(); first=False
        setp(p,"• "+it,13,NAVY); p.space_after=Pt(5)
    i+=1
foot(s,"SWOT 为基于公开信息的演示性判断")

# ===== 12. 对手深挖 =====
s=slide(); title_bar(s,"【竞争格局】主要对手对比：流量、模式、上市状态各异")
section_tag(s,"③ 竞争格局",BLUE2)
table(s,0.5,1.85,12.3,4.3,[
    ["公司","定位/模式","流量(MAU)","商业化","对 MiniMax 的意义"],
    ["豆包(字节)","闭源MoE，To B为主，火山引擎","1.72 亿","企业客户广","流量与算力碾压，定价压制"],
    ["DeepSeek","开源高性能，性价比标杆","1.45 亿","API/开源","拉低付费意愿，抢开发者心智"],
    ["智谱 AI","To B，已港股IPO","中等","政企/企业","“大模型第一股”直接对标"],
    ["Kimi(月之暗面)","Agent/深度研究，金融学术","967 万","订阅/Agent","同为六小龙，争“下一个DeepSeek”"],
    ["通义千问(阿里)","开源Qwen + 云","大","阿里云绑定","阿里既是股东又是竞品"],
],col_w=[1.9,3.0,1.5,2.0,3.9],fs=11.5,hfs=11.5)
foot(s,"来源：人人都是产品经理《2026国产大模型选型地图》；财联社；火山引擎社区")

# ===== 13. 雷达图 =====
s=slide(); title_bar(s,"【竞争格局】五维定位：MiniMax 强在多模态与出海，弱在流量与盈利",
                     "定性打分 1=弱 5=强（作者评估 [E]）")
section_tag(s,"③ 竞争格局",BLUE2)
cd=CategoryChartData(); cd.categories=["国内流量","海外/出海","多模态能力","商业化变现","盈利能力"]
cd.add_series("MiniMax",(2,5,5,3,2))
cd.add_series("豆包",(5,3,4,4,4))
cd.add_series("DeepSeek",(4,4,3,2,3))
cd.add_series("智谱",(3,3,4,3,2))
gf=s.shapes.add_chart(XL_CHART_TYPE.RADAR,Inches(0.6),Inches(1.85),Inches(7.2),Inches(4.7),cd)
ch=gf.chart; ch.has_legend=True; ch.legend.position=XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout=False; ch.legend.font.size=Pt(12)
bullets(s,8.1,1.95,4.8,4.5,[
    ("读图要点",True),
    ("• MiniMax(蓝)轮廓“偏出海+多模态”，国内流量与盈利是凹点",False),
    ("• 豆包轮廓最大且均衡，全维度领先",False),
    ("• 各家形状差异大 → 不是同质竞争，而是分赛道卡位",False),
])
foot(s,"打分为作者综合公开数据的定性评估 [E]，仅供相对比较")

# ===== 14. 护城河与软肋 =====
s=slide(); title_bar(s,"综合：护城河在“多模态+出海产品力”，软肋在“流量+盈利”")
m=s.shapes.add_shape(1,Inches(0.5),Inches(1.75),Inches(6.0),Inches(0.5)); m.fill.solid(); m.fill.fore_color.rgb=NAVY; m.line.fill.background()
setp(m.text_frame.paragraphs[0],"护城河（可持续优势）",15,WHITE,True,PP_ALIGN.CENTER)
bullets(s,0.5,2.35,6.0,4.2,[
    ("• 产品力：海螺/Talkie 在 AI 视频与情感陪伴的海外心智",False),
    ("• 多模态全栈自研，模型迭代快（M2.5、Hailuo-02）",False),
    ("• 出海先发：73% 海外收入，绕开国内流量血战",False),
    ("• 资本/生态：阿里、腾讯、米哈游战略加持",False),
])
r=s.shapes.add_shape(1,Inches(6.9),Inches(1.75),Inches(6.0),Inches(0.5)); r.fill.solid(); r.fill.fore_color.rgb=ACCENT; r.line.fill.background()
setp(r.text_frame.paragraphs[0],"软肋（结构性风险）",15,WHITE,True,PP_ALIGN.CENTER)
bullets(s,6.9,2.35,6.0,4.2,[
    ("• 持续大额亏损，盈利路径与时点未明",False),
    ("• 国内流量远逊大厂，C 端获客成本高",False),
    ("• 估值 75x P/S，容错空间极小",False),
    ("• 海外合规/地缘 + 开源模型挤压付费意愿",False),
    ("• 阿里等股东同时是竞品（豆包/Qwen/智谱）",False),
])
foot(s,"综合招股书、券商研报与公开报道的作者判断")

# ===== 15. 综合投资情景 =====
s=slide(); title_bar(s,"综合结论：一笔“高赔率、高不确定”的 AI 平台期权")
table(s,0.5,1.8,12.3,3.0,[
    ["情景","概率","核心条件","估值含义"],
    ["牛","25%","海外To C持续放量+M系列生态成形，2030前路径清晰转盈","重估为区域多模态赢家，市值上行空间大"],
    ["中","45%","维持高增但盈利后移，烧钱与融资稀释并存","随增长与情绪宽幅震荡，估值难“算清”"],
    ["熊","30%","增速换挡+大厂/开源挤压+海外受阻，盈利遥遥无期","P/S 大幅压缩，持续融资稀释股东"],
],col_w=[1.1,1.0,5.7,4.5],num_cols={1})
bullets(s,0.5,5.1,12.3,1.6,[
    ("给个人投资者的提醒",True),
    ("• 这不是靠 DCF/财报算清的标的，仓位与风险敞口比“目标价”更重要；把它当高波动成长期权对待。",False),
    ("• 最值得跟踪的三件事：① 亏损率拐点 ② 海外收入占比与付费转化 ③ 第二曲线（企业/开放平台）放量。",False),
],12.5)
foot(s,"演示性情景与概率为作者主观假设 [E]，不构成投资建议")

# ===== 16. 来源与免责 =====
s=slide(); title_bar(s,"数据来源与免责声明")
bullets(s,0.5,1.8,12.3,5.0,[
    ("主要来源",True),
    ("• MiniMax (稀宇科技) 港交所招股书 (2025-12) 及上市后业绩公告",False),
    ("• 量子位、新浪财经、证券时报、21经济网、澎湃新闻、InfoQ、财联社、新华网",False),
    ("• QuestMobile（月活数据）；人人都是产品经理《2026国产大模型选型地图》",False),
    ("• Caproasia / Douglas Research（IPO 估值与募资）",False),
    ("",False),
    ("免责声明",True),
    ("本报告由 AI 基于公开来源整理。财报前瞻假设、DCF 测算（营收/利润率/WACC/终值）、竞争打分与情景概率均为演示性估计 [E]，",False),
    ("可能存在重大误差或时效偏差。DCF 对早期亏损 AI 公司参考性有限，已在正文充分提示。本报告不构成任何投资建议，",False),
    ("投资决策请以公司正式披露文件及专业意见为准。",False),
],13)

out="/home/user/King/MiniMax_前瞻_DCF_竞争格局.pptx"
prs.save(out)
print("saved:",out,"slides:",len(prs.slides._sldIdLst))
