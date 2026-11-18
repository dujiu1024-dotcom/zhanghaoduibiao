from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = "/Users/longyi/project/账号对标/01-执行包/02-price-sheet.xlsx"

FONT = "PingFang SC"
INK = "1F2937"
MUTED = "6B7280"
HEADER_FILL = PatternFill("solid", fgColor="334155")
SUB_FILL = PatternFill("solid", fgColor="EAF2FF")
INPUT_FILL = PatternFill("solid", fgColor="FFF7D6")
ZEBRA = [PatternFill("solid", fgColor="FFFFFF"), PatternFill("solid", fgColor="F7F9FC")]
THIN = Side(style="thin", color="D9DEE7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
TOP_LINE = Border(left=THIN, right=THIN, top=Side(style="medium", color="AAB4C5"), bottom=THIN)
MONEY = '¥#,##0;[Red]-¥#,##0;"-"'
PCT = '0.0%'


def title(ws, text, last_col):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    c = ws.cell(1, 1, text)
    c.font = Font(name=FONT, size=16, bold=True, color=INK)
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 36


def header_row(ws, row, values, height=30):
    for i, v in enumerate(values, 1):
        c = ws.cell(row, i, v)
        c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        c.fill = HEADER_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = height


def section(ws, row, text, last_col):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    c = ws.cell(row, 1, text)
    c.font = Font(name=FONT, size=11, bold=True, color=INK)
    c.fill = SUB_FILL
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[row].height = 24


def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w


def body(cell, fmt=None, bold=False, align="left", wrap=False, size=10):
    cell.font = Font(name=FONT, size=size, color=INK, bold=bold)
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
    cell.border = BORDER
    if fmt:
        cell.number_format = fmt


def input_cell(cell, fmt=None, align="center"):
    body(cell, fmt=fmt, align=align)
    cell.fill = INPUT_FILL
    cell.font = Font(name=FONT, size=10, color="0000FF", bold=False)


wb = Workbook()

# ---------------- Sheet 1 报价单 ----------------
ws = wb.active
ws.title = "01 报价单"
ws.sheet_view.showGridLines = False
widths(ws, {"A": 7, "B": 24, "C": 44, "D": 13, "E": 15, "F": 15})
title(ws, "技术服务报价单", 6)

labels = [("A3", "报价方："), ("D3", "报价日期："), ("A4", "客户："), ("D4", "项目：")]
for ref, text in labels:
    c = ws[ref]
    c.value = text
    c.font = Font(name=FONT, size=10, bold=True, color=MUTED)
    c.alignment = Alignment(horizontal="right", vertical="center")

for ref in ["B3", "E3", "B4", "E4"]:
    c = ws[ref]
    c.fill = INPUT_FILL
    c.border = BORDER
    c.font = Font(name=FONT, size=10, color="0000FF")
    c.alignment = Alignment(vertical="center")
ws.merge_cells("B3:C3")
ws.merge_cells("E3:F3")
ws.merge_cells("B4:C4")
ws.merge_cells("E4:F4")
ws["E3"] = "2026-11-14"

header_row(ws, 6, ["序号", "项目 / 模块", "交付内容（写到可验收）", "数量\n(人天)", "单价\n(元/人天)", "金额(元)"])

for r in range(7, 15):
    body(ws.cell(r, 1, r - 6), align="center")
    for col in (2, 3):
        body(ws.cell(r, col), wrap=True)
    input_cell(ws.cell(r, 4), fmt="0.0")
    input_cell(ws.cell(r, 5), fmt=MONEY)
    c = ws.cell(r, 6, f'=IF(OR(D{r}="",E{r}=""),"",ROUND(D{r}*E{r},0))')
    body(c, fmt=MONEY, align="right")
    ws.row_dimensions[r].height = 26

# 小计
ws.merge_cells("A15:E15")
c = ws["A15"]
c.value = "小计"
body(c, bold=True, align="right")
c = ws["F15"]
c.value = "=SUM(F7:F14)"
body(c, fmt=MONEY, bold=True, align="right")
for col in range(1, 7):
    ws.cell(15, col).border = TOP_LINE

rows = [
    (16, "折扣率（0%–100%，用价格换案例/转介绍时填）", "B16", PCT, "=ROUND(-F15*B16,0)"),
    (17, "加急费（0%–30%，工期压缩 30% 以上时填）", "B17", PCT, "=ROUND((F15+F16)*B17,0)"),
]
for r, label, ref, fmt, formula in rows:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    body(ws.cell(r, 1, label), align="right")
    input_cell(ws[ref], fmt=fmt)
    ws.cell(r, 5).value = ""
    body(ws.cell(r, 5))
    c = ws.cell(r, 6, formula)
    body(c, fmt=MONEY, align="right")
    ws.row_dimensions[r].height = 24

ws.merge_cells("A18:E18")
body(ws["A18"], bold=True, align="right")
ws["A18"].value = "总计（含税/不含税需注明）"
c = ws["F18"]
c.value = "=F15+F16+F17"
body(c, fmt=MONEY, bold=True, align="right", size=12)
c.fill = SUB_FILL
for col in range(1, 7):
    ws.cell(18, col).border = TOP_LINE
ws.row_dimensions[18].height = 30

section(ws, 20, "付款计划", 6)
header_row(ws, 21, ["节点", "比例", "金额(元)", "触发条件 / 说明", "", ""])
ws.merge_cells("D21:F21")
plan = [
    ("预付款", 0.4, "合同签署后 3 个工作日内，未到账不开工"),
    ("中期款", 0.3, "可演示版本确认后 5 个工作日内"),
    ("验收款", 0.3, "验收通过后 5 个工作日内"),
    ("质保金", 0.0, "验收后 30 日（D 档建议 10%）"),
]
for i, (name, ratio, cond) in enumerate(plan):
    r = 22 + i
    body(ws.cell(r, 1, name), align="center")
    input_cell(ws.cell(r, 2), fmt=PCT)
    ws.cell(r, 2).value = ratio
    c = ws.cell(r, 3, f"=ROUND($F$18*B{r},0)")
    body(c, fmt=MONEY, align="right")
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
    body(ws.cell(r, 4, cond), wrap=True)
    ws.row_dimensions[r].height = 24

body(ws.cell(26, 1, "合计"), bold=True, align="center")
c = ws.cell(26, 2, "=SUM(B22:B25)")
body(c, fmt=PCT, bold=True, align="center")
c = ws.cell(26, 3, "=SUM(C22:C25)")
body(c, fmt=MONEY, bold=True, align="right")
ws.merge_cells("D26:F26")
c = ws.cell(26, 4, '=IF(ABS(B26-1)<0.001,"比例合计 100% ✓","比例合计不是 100% ✗")')
body(c, bold=True, align="left")

section(ws, 28, "报价说明（发给客户前逐条确认）", 6)
notes = [
    "1. 报价有效期 15 天，含 2 轮验收前修改；第 3 轮起或新增范围按 1,500 元/人天另计（最小 0.5 天）。",
    "2. 不含：第三方接口/模型的调用费用、服务器费用、客户系统改造、客户方数据清洗超过 ____ 小时的部分。",
    "3. 工期自预付款到账次日起算；客户资料/账号/接口权限延迟，工期顺延。",
    "4. 验收标准以本单「交付内容」列及附件为准，交付后 5 个工作日未书面异议视为通过。",
    "5. 交付后 30 天内免费修复约定范围内的明显缺陷；新需求与二次开发另议。",
    "6. 案例展示需另行取得书面授权，默认不展示客户名称与数据。",
]
for i, text in enumerate(notes):
    r = 29 + i
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    c = ws.cell(r, 1, text)
    body(c, wrap=True)
    c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 30

# ---------------- Sheet 2 成本测算 ----------------
ws2 = wb.create_sheet("02 成本测算")
ws2.sheet_view.showGridLines = False
widths(ws2, {"A": 20, "B": 12, "C": 13, "D": 14, "E": 12, "F": 10, "G": 18, "H": 15})
title(ws2, "内部成本测算（不外发）", 8)
section(ws2, 3, "假设（黄色格可改，改完下面全部自动重算）", 8)

assumptions = [
    ("内部成本人天（元/人天）", 800, MONEY),
    ("对外人天单价（元/人天）", 2000, MONEY),
    ("风险系数（1.0–1.5）", 1.2, "0.0"),
    ("目标毛利率", 0.4, PCT),
]
for i, (label, val, fmt) in enumerate(assumptions):
    r = 4 + i
    body(ws2.cell(r, 1, label), bold=True)
    ws2.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    input_cell(ws2.cell(r, 3), fmt=fmt)
    ws2.cell(r, 3).value = val

header_row(ws2, 9, ["档位", "工时\n(人天)", "保本价(元)", "建议报价(元)", "毛利(元)", "毛利率", "判断", "按人天价(元)"])
tiers = [
    ("A. 咨询（60 分钟）", 1.0, 399),
    ("A+. 深度诊断", 2.0, 1999),
    ("B. 小工具/脚本", 3.0, 2800),
    ("C. 单个智能体", 6.0, 9800),
    ("D. 完整系统", 20.0, 39800),
]
for i, (name, days, quote) in enumerate(tiers):
    r = 10 + i
    body(ws2.cell(r, 1, name), bold=True)
    input_cell(ws2.cell(r, 2), fmt="0.0")
    ws2.cell(r, 2).value = days
    c = ws2.cell(r, 3, f"=ROUND(B{r}*$C$4*$C$6,0)")
    body(c, fmt=MONEY, align="right")
    input_cell(ws2.cell(r, 4), fmt=MONEY)
    ws2.cell(r, 4).value = quote
    c = ws2.cell(r, 5, f"=D{r}-C{r}")
    body(c, fmt=MONEY, align="right")
    c = ws2.cell(r, 6, f"=IF(D{r}=0,0,E{r}/D{r})")
    body(c, fmt=PCT, align="right")
    c = ws2.cell(r, 7, f'=IF(ROW()<=11,"漏斗档，不按毛利判断",IF(F{r}>=$C$7,"可接","压范围或提价"))')
    body(c, align="center", bold=True)
    c = ws2.cell(r, 8, f"=ROUND(B{r}*$C$5,0)")
    body(c, fmt=MONEY, align="right")
    ws2.row_dimensions[r].height = 24

tips = [
    "保本价 = 工时 × 内部成本人天 × 风险系数；建议报价可改，改完毛利与判断自动重算。",
    "A / A+ 两档不要看毛利率：它们是漏斗，作用是换来后面的项目。A 档控制在 0.5 人天内，A+ 档控制在 1.5 人天内。",
    "B 档按 3 人天做，2,800 元是亏的（毛利 -80）。这个负数是真实的：平台挂牌价 1,500–1,999 已经把单流程自动化打穿。要么压到 1–2 人天，要么不接。",
    "D 档 20 人天是低值，完整系统通常 25–45 人天；超过 30 人天建议拆期或联合交付。",
    "风险系数超过 1.5 的活不要接：需求没冻结、接口没权限、决策人不在场，三者占一个就加 0.2。",
]
for i, text in enumerate(tips):
    r = 17 + i
    ws2.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    body(ws2.cell(r, 1, "· " + text), wrap=True)
    ws2.cell(r, 1).alignment = Alignment(vertical="center", wrap_text=True)
    ws2.row_dimensions[r].height = 32

# ---------------- Sheet 3 参考区间 ----------------
ws3 = wb.create_sheet("03 参考区间与出处")
ws3.sheet_view.showGridLines = False
widths(ws3, {"A": 18, "B": 38, "C": 12, "D": 12, "E": 14, "F": 12, "G": 14, "H": 62})
title(ws3, "四档参考区间与出处（对外讲价前先看这一页）", 8)
header_row(ws3, 3, ["档位", "交付物", "区间下限", "区间上限", "建议首单价", "工期", "来源等级", "出处 / 备注"], 34)

data = [
    ("A. 咨询", "60 分钟线上诊断，口头结论 + 3 条建议", 300, 600, 199, "当天", "平台", "在行官方帮助：多数行家初次定价 300 元上下；实现网 9 年全栈 1,000 元/8 小时。199 为首单引流价，可抵扣项目款。"),
    ("A+. 深度诊断", "半天访谈 + 书面现状梳理 + 方案 + 报价", 1500, 3000, 1999, "2–3 天", "判断", "无直接挂牌样本，按 1,500–2,000 元/人天 × 1 人天折算。属于推算，不是行情。"),
    ("B. 小工具 / 脚本", "1 条重复流程跑通，脚本 + 操作说明", 1500, 5000, 2800, "2–5 天", "报价", "猪八戒挂牌：基础版 1,888 / 1,999；AI 知识库基础版 1,500；闲鱼定制部署数百元。上限 5,000 为判断。"),
    ("C. 单个智能体", "单场景可用智能体，含提示词、评测、部署、1 次培训", 6000, 20000, 9800, "7–15 天", "报价", "猪八戒挂牌：标准版 5,999 / 6,888；高级版 15,000 / 18,888 / 19,999；企微接入 15,000。"),
    ("D. 完整系统", "多系统对接 + 权限 + 后台 + 部署 + 培训 + 30 天质保", 25000, 80000, 39800, "20–45 天", "判断（无出处）", "仅 AI 高级版 19,999 元可参照；「小程序定制 2 万–10 万」出自第三方博客，可信度低。此区间不可对客称「市场价」。"),
]
for i, row in enumerate(data):
    r = 4 + i
    body(ws3.cell(r, 1, row[0]), bold=True, wrap=True)
    body(ws3.cell(r, 2, row[1]), wrap=True)
    for col, val in ((3, row[2]), (4, row[3]), (5, row[4])):
        body(ws3.cell(r, col, val), fmt=MONEY, align="right")
    body(ws3.cell(r, 6, row[5]), align="center")
    body(ws3.cell(r, 7, row[6]), align="center", bold=True)
    body(ws3.cell(r, 8, row[7]), wrap=True)
    for col in range(1, 9):
        ws3.cell(r, col).fill = ZEBRA[i % 2]
    ws3.row_dimensions[r].height = 76

section(ws3, 10, "人天单价与维护", 8)
extra = [
    ("对外人天单价", "1,500–2,500 元/人天", "平台 / 判断", "程序员客栈帮助中心：日薪区间 300–2,000 元/天，开发者自设；首页样本 300/600/800/1,000。2,500 为有案例后的判断。"),
    ("内部成本人天", "800 元/人天", "判断", "时间机会成本 + 模型/服务器/工具开销，无公开数据。"),
    ("月度维护", "项目价 × 10%/月，最低 800 元/月", "未获取", "没有找到可信公开报价，这是定价建议，不要对外说「行价」。"),
    ("需求变更", "1,500 元/人天，最小 0.5 天", "判断", "参照猪八戒服务商条款「范围外需求另计周期与费用」。"),
    ("加急", "总价 +30%", "判断", "工期压缩 30% 以上时适用。"),
]
for i, (k, v, grade, note) in enumerate(extra):
    r = 11 + i
    body(ws3.cell(r, 1, k), bold=True, wrap=True)
    body(ws3.cell(r, 2, v), wrap=True)
    ws3.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
    body(ws3.cell(r, 3, grade), align="center")
    body(ws3.cell(r, 7, ""), align="center")
    ws3.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
    body(ws3.cell(r, 7, note), wrap=True)
    for col in range(1, 9):
        ws3.cell(r, col).fill = ZEBRA[(i + 1) % 2]
    ws3.row_dimensions[r].height = 40

# ---------------- Sheet 4 订单台账 ----------------
ws4 = wb.create_sheet("04 订单台账")
ws4.sheet_view.showGridLines = False
widths(ws4, {"A": 13, "B": 20, "C": 14, "D": 14, "E": 13, "F": 13, "G": 14, "H": 12, "I": 30})
title(ws4, "订单台账（每单一行，不复用行）", 9)
header_row(ws4, 3, ["日期", "客户 / 渠道", "档位", "合同额(元)", "已收(元)", "未收(元)", "当前节点", "状态", "备注"])

for r in range(4, 19):
    for col in range(1, 10):
        body(ws4.cell(r, col), fmt="yyyy-mm-dd" if col == 1 else None, wrap=(col == 9))
        ws4.cell(r, col).fill = ZEBRA[(r - 4) % 2]
    for col in (4, 5):
        ws4.cell(r, col).number_format = MONEY
        ws4.cell(r, col).fill = INPUT_FILL
    c = ws4.cell(r, 6, f'=IF(D{r}="","",D{r}-E{r})')
    body(c, fmt=MONEY, align="right")
    ws4.row_dimensions[r].height = 24

dv_tier = DataValidation(type="list", formula1='"A咨询,A+诊断,B小工具,C智能体,D系统"', allow_blank=True)
dv_status = DataValidation(type="list", formula1='"待报价,已报价,已付预付,开发中,待验收,已结清,已终止"', allow_blank=True)
ws4.add_data_validation(dv_tier)
ws4.add_data_validation(dv_status)
dv_tier.add("C4:C18")
dv_status.add("H4:H18")

body(ws4.cell(20, 1, "合计"), bold=True)
ws4.merge_cells("A20:C20")
for col, letter in ((4, "D"), (5, "E"), (6, "F")):
    c = ws4.cell(20, col, f"=SUM({letter}4:{letter}18)")
    body(c, fmt=MONEY, bold=True, align="right")
    c.border = TOP_LINE
body(ws4.cell(22, 1, "提示：走猪八戒/程序员客栈的单，平台技术服务费 5%–20%，记在备注里，算毛利时先扣掉。"), wrap=True)
ws4.merge_cells("A22:I22")
ws4["A22"].alignment = Alignment(vertical="center", wrap_text=True)
ws4.row_dimensions[22].height = 26

for sheet in (ws, ws2, ws3, ws4):
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0

wb.save(OUT)
print(OUT)
