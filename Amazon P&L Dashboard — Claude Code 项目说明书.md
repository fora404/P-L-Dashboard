# Amazon P&L Dashboard — Claude Code 项目说明书

2026-09-17 · 整理人：@ting

## 项目概述与目标

**FORA CARE Amazon P&L Dashboard** —— 一个多人可访问的在线数据看板，用于展示 Amazon 欧洲多个站点（DE/UK/IT/FR/ES/NL/PL）的月度/季度/YTD 损益（P&L）情况，包括净收入、净利润、广告花费、FBA/MFN 订单量、贡献利润率（Contribution Margin）以及详细的 P&L 分项表格。

**目标**：

- 把现有 Google Apps Script 里已经写好的计算逻辑，作为唯一的数据计算来源，**不改动其计算逻辑**，仅在此基础上做数据获取、缓存与可视化封装
- 用 Streamlit 重新实现已经设计好的 UI（深色侧边栏 + KPI 卡片 + 组合图 + 圆环图 + 分组明细表），风格参考见下方「UI 设计与页面结构」一节
- 免费部署到公网，供公司内多人访问（不止本人使用），不能装在本地服务器上
- 数据来源是 Google Drive 里的文件，且会随时更新；页面本身不自动轮询更新，而是默认使用缓存数据，用户点击「更新数据」按钮时才真正去拉取最新数据

## 技术架构总览

```
Google Apps Script（已有，负责计算，不可改动逻辑）
        │  输出计算结果（写入 Sheet / 生成 JSON 或 CSV 文件）
        ▼
Google Drive（存放 Apps Script 计算出的结果文件，随时更新）
        │  服务账号只读访问（Google Drive API）
        ▼
Streamlit 应用（Python，读取 Drive 文件 → 缓存 → 渲染 UI）
        │  部署在 Streamlit Community Cloud（免费公网托管）
        ▼
浏览器（多人可访问的公开链接）
```

**分层职责**：

- **计算层**（不可动）：现有 Google Apps Script，负责所有 P&L 计算逻辑（收入、退款、手续费、贡献利润率等）
- **数据层**：Apps Script 的计算结果落地到 Google Drive 的文件里（Sheet 导出或 JSON/CSV），作为 Streamlit 的唯一数据输入
- **应用层**：Streamlit 只做「读取 → 缓存 → 展示 → 按钮触发的手动刷新」，不重新实现任何计算逻辑
- **托管层**：GitHub 存代码，Streamlit Community Cloud 拉取仓库并运行

## 数据源：现有 Google Apps Script（计算逻辑不可更改）

**硬性约束：Claude Code 不得修改 Apps Script 里已有的任何计算逻辑**（收入/退款/手续费/贡献利润率等公式），只能在其输出结果的基础上做读取、缓存和展示。

**如何把现有 Apps Script 交给 Claude Code**（本人需要先手动导出）：

1. **首选方式：clasp 命令行导出（推荐，能完整保留代码结构）**
   - 本地安装：`npm install -g @google/clasp`
   - 登录：`clasp login`（会打开浏览器授权）
   - 打开目标 Apps Script 项目 → 右上角「项目设置」齿轮图标 → 复制「脚本 ID」（Script ID）
   - 拉取代码：`clasp clone <脚本ID>`，会在本地生成 `.gs`/`.js` 文件和 `appsscript.json`，把这个文件夹整个交给 Claude Code 参考
2. **备选方式：手动复制粘贴**
   - 打开 Google Sheet（或独立脚本项目）→ 「扩展程序」→「Apps Script」
   - 左侧每个 `.gs` 文件依次打开，全选复制内容，保存成本地同名 `.js` 文件
   - 适合脚本文件不多、想快速给 Claude Code 看逻辑的情况

**Streamlit 如何拿到 Apps Script 算出来的结果**，两种方案二选一：

- **方案 A（推荐）**：Apps Script 保持现状，只需确认它会把计算结果写出到一个 Google Drive 里的文件（Sheet 导出为 CSV/JSON，或直接写文件）。Streamlit 只用 Google Drive API 读这个「结果文件」，不接触 Apps Script 本身，也不重新计算
- **方案 B**：把 Apps Script 发布成 Web App（`doGet` 返回 JSON），Streamlit 用 `requests` 直接调用这个 URL 取数。这种方式实时性更好，但需要额外配置 Apps Script 的部署权限和访问控制

> 待确认：现有 Apps Script 目前是「写结果到 Drive 文件」还是「本身就是一个 Web App」？这决定了 Claude Code 具体怎么对接（见文末任务清单）。

## UI 设计与页面结构

参考截图：FORA CARE Amazon P&L Dashboard（本人已上传原型图，Claude Code 需按此还原）。

**左侧深色侧边栏**：

- 头像 + 「FORA CARE」标题 + 「Amazon P&L Dashboard」副标题
- Marketplace 列表：All Europe（汇总，高亮选中态）+ 各国站点（DE/GB/IT/FR/ES/NL/PL），每项右侧显示对应净利润数值，颜色随正负变化

**顶部区域**：

- 当前选中的 Marketplace 名称 + 面包屑（YTD · All Europe）
- 右上角 EN / 中文 语言切换按钮
- 时间维度胶囊按钮组：YTD / Q1 / Q2 / Jan…Jun（单选，选中态深色底白字）

**5 个 KPI 卡片**：Net Revenue / Net Profit / Ads Spend / FBA Orders / MFN Orders，每张卡片左侧一条彩色竖线、标题、大号数值、一行说明小字

**Shared Fixed Costs 提示条**：说明「工资和仓库费用是固定成本，只在这里统一扣除一次，不按站点单独分摊」，右侧列出各项固定成本明细

**图表区（左右各一）**：

- 左：按月份的组合图（净收入柱状 + Contribution Margin 折线/散点，双系列）
- 右：Contribution Margin 圆环图（当前 26%）

**底部 P&L 明细表**：

- 分组标题行（REVENUE / OTHER INCOME / AMAZON FEES 等）
- 各行项目按月显示（Jan–Jun）+ 最右侧 YTD 汇总列
- 正数绿色、负数红色、小计行加粗
- 右上角「Detail View」按钮

**技术实现要点**：

- 组合图和圆环图用 **Plotly**（`st.plotly_chart`），不要用 Streamlit 自带的 `st.bar_chart`
- KPI 卡片、Shared Fixed Costs 条、深色侧边栏配色，用自定义 CSS/HTML 通过 `st.markdown(unsafe_allow_html=True)` 实现
- 明细表如果 `st.dataframe` + pandas Styler 做不出「分组小标题穿插在数据行之间」的效果，允许改为纯 HTML `<table>` 手写渲染

## 数据刷新与缓存机制

**原则**：默认所有人看到的都是缓存数据，不做定时轮询；只有用户点击「更新数据」按钮时，才真正去 Drive 拉一次最新数据。

```python
import streamlit as st

@st.cache_data(show_spinner=False)  # 不设 ttl，永久缓存直到手动清除
def load_data(refresh_key):
    # refresh_key 只是用来让缓存判定「这是新一次调用」，函数内部不需要用它
    # 调用 Google Drive API 读取 Apps Script 生成的结果文件并解析
    ...
    return df

if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

with st.spinner("正在从 Google Drive 拉取最新数据..."):
    df = load_data(st.session_state.refresh_key)

if st.button("🔄 更新数据"):
    st.session_state.refresh_key += 1  # 改变入参，缓存判定为新调用，真正重新拉取
    st.rerun()
```

- Google Drive 连接对象（客户端）用 `@st.cache_resource` 缓存，避免每次重建连接
- 筛选参数（Marketplace、时间维度）作为取数函数的入参，Streamlit 会自动按参数区分缓存 key，不用手动管理
- Google 服务账号凭证放在 Streamlit Community Cloud 后台的 Secrets 里（TOML 格式），本地开发放在 `.streamlit/secrets.toml`（需加入 `.gitignore`），代码里用 `st.secrets["gcp_service_account"]` 读取
- 用 `st.spinner(...)` 包住取数调用，拉取新数据时会显示加载提示，用缓存数据时几乎不显示（因为很快），体验更友好

## 部署与托管方案

**代码托管**：GitHub 仓库（可私有，免费账号也支持连私有仓库部署）

**运行托管**：Streamlit Community Cloud（免费）

1. 登录 share.streamlit.io，用 GitHub 账号授权
2. 选择仓库、分支、入口文件（如 `app.py`）
3. 点击 Deploy，几分钟后得到一个 `xxx.streamlit.app` 的公开链接，团队所有人都能直接打开
4. 以后 `git push` 新代码会自动触发重新部署
5. Google 服务账号凭证在 App 设置的 Secrets 里配置，不进代码仓库

**成本**：GitHub + Streamlit Community Cloud + Google Drive API 正常用量下全部免费

## 本地开发环境搭建（虚拟环境 + clasp 导出）

建议的项目文件夹结构：

```
amazon-pnl-dashboard/
├── .venv/                  # Python 虚拟环境（不进 git）
├── apps_script/            # clasp clone 下来的现有 Apps Script 代码（只读参考，不改动）
├── .streamlit/
│   └── secrets.toml         # 本地测试用的凭证（不进 git）
├── app.py                  # Streamlit 入口
├── requirements.txt
└── .gitignore
```

**创建虚拟环境**（macOS / Linux）：

```bash
mkdir amazon-pnl-dashboard && cd amazon-pnl-dashboard
python3 -m venv .venv
source .venv/bin/activate
```

Windows（PowerShell）：

```powershell
mkdir amazon-pnl-dashboard; cd amazon-pnl-dashboard
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**安装依赖**：

```bash
pip install streamlit pandas plotly google-api-python-client google-auth
pip freeze > requirements.txt
```

**导出现有 Apps Script**（激活虚拟环境后，同一个项目文件夹里）：

```bash
npm install -g @google/clasp
clasp login
mkdir apps_script && cd apps_script
clasp clone <脚本ID>
cd ..
```

**`.gitignore` 内容**：

```
.venv/
.streamlit/secrets.toml
__pycache__/
*.pyc
```

**初始化仓库并推送到 GitHub**：

```bash
git init
git add .
git commit -m "Initial project scaffold"
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

这样交给 Claude Code 时，虚拟环境、Apps Script 参考代码、依赖清单都已经在项目文件夹里，它可以直接在 `.venv` 里继续装依赖、写 `app.py`，不用重新搭环境。

## 已知限制 / 风险点

- **Streamlit Community Cloud 内存约 1GB**（不同说法在 690MB–2.7GB 之间），12 小时无访问会休眠、下次打开有冷启动延迟；免费版只能有 1 个私有应用、无自定义域名
- 人多、数据量大、图表复杂时容易顶到内存上限被强制终止（OOMKill），上线后需要实测观察
- Google Drive API 免费配额宽松（每分钟每项目 100 万配额单位），正常用量不会触及，但需注意 Google 计划从 2026 年晚些时候起对**超出配额**的调用开始收费
- 底部 P&L 明细表（分组标题+加粗小计+滚动）用 Streamlit 原生表格组件较难 1:1 还原，可能需要手写 HTML `<table>`，这部分预计是开发工作量最大的地方
- 全局 CSS 覆盖依赖 Streamlit 内部的 `data-testid` 选择器，版本升级时可能失效，需要留意后续维护
- **前提假设待确认**：现有 Apps Script 的产出形式（写入 Drive 文件 vs. Web App）尚未最终确认，会影响 Streamlit 取数方式的具体实现（见「数据源」一节）

## 给 Claude Code 的任务清单

1. 阅读本人提供的 Apps Script 导出代码（clasp 或手动导出的文件），**只读不改**，理清它计算出哪些字段、输出到哪个 Drive 文件、什么格式（CSV/JSON/Sheet）
2. 用 Python 写一个读取该输出文件的函数，通过 Google Drive API（服务账号只读权限）获取数据并解析为 DataFrame
3. 按「UI 设计与页面结构」一节还原页面：侧边栏、KPI 卡片、时间维度胶囊按钮、Plotly 组合图与圆环图、底部分组明细表
4. 实现「数据刷新与缓存机制」一节里的 `st.cache_data` + 按钮刷新逻辑
5. 补充中英文文案切换（EN / 中文）
6. 写好 `requirements.txt`，本地用 `.streamlit/secrets.toml` 跑通后，推送到 GitHub 仓库
7. 协助本人完成 Streamlit Community Cloud 部署配置（Secrets 填写、入口文件指定）

> 待本人补充：Apps Script 计算结果目前具体落在哪个 Drive 文件/哪个 Sheet 里？字段名是什么？（Claude Code 需要这个信息才能对接第 2 步）
