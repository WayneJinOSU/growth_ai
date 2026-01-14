# Mahaney Growth Protocol (MGP) V3.2 - Python Implementation

**—— 从“错杀猎手”进化为“不对称收益捕手”**

这是一个基于马克·马哈尼（Mark Mahaney）成长股投资策略 **MGP V3.2** 的自动化分析系统。该版本移除了技术面分析，转而聚焦于基本面的深度挖掘与未来可能性的量化。它旨在寻找那些“既有坚实地板，又有无限天空，且导火索即将被点燃”的完美标的。

## 核心哲学 (Core Philosophy)
本策略依然根植于寻找 **DHQA (Dislocated High-Quality Assets)**，但 V3.2 版本引入了**风投（VC）思维**，致力于捕捉 **“不对称收益（Asymmetric Returns）”**：
1.  **下行有限**：由数学纪律（铁律）和估值地板保护。
2.  **上行无限**：由第二增长曲线（蓝天）和期权价值驱动。
3.  **引爆在即**：由特定催化剂事件点燃价值回归。

---

## 核心功能流水线

系统通过四个阶段的流水线自动处理股票分析：

### 1. Phase 1: 铁律与卫生检验 (The Iron Gate & Hygiene)
**目标**：用数学清洗名单。不仅要剔除伪成长，还要剔除“股东价值毁灭者”。
*   **增长铁律**：5年营收 CAGR (>20%) 或 季度增速 (>20%)。
*   **减速熔断**：增速由高位腰斩视为逻辑破损，直接淘汰。
*   **Dilution Shield (V3.2 新增)**：
    *   **SBC 警戒线**：股权激励支出 > 营收的 20% -> 淘汰。
    *   **每股含金量**：监控营收增长 vs. 股本增长，拒绝稀释换增长。
*   **盈利路径**：
    *   **已盈利**：PEG < 1.0 (极低估) 至 1.5 (合理)。
    *   **未盈利**：毛利率斜率 (Gross Margin Slope) 必须稳步提升，且具备运营杠杆。

    ```mermaid
    graph TD
        Start[Start Analysis] --> CheckGrowth{Growth Gate}
        
        CheckGrowth -- "CAGR > 15% OR Q_Growth > 20%" --> CheckDilution{Dilution Shield}
        CheckGrowth -- "Growth < Threshold" --> Reject[❌ Reject]
        
        CheckDilution -- "SBC/Rev > 20%" --> Reject
        CheckDilution -- "Pass" --> CheckProfit{Profitability}
        
        CheckProfit -- "Net Margin > 3%" --> PathA[Path A: Profitable]
        CheckProfit -- "Net Margin <= 3%" --> PathB[Path B: Unprofitable]
        
        PathA --> CheckPEG{PEG Check}
        CheckPEG -- "PEG < 2.0" --> Phase2[✅ Pass to Phase 2]
        CheckPEG -- "PEG > 2.0" --> Reject
        
        PathB --> CheckEfficiency{Efficiency Check}
        CheckEfficiency -- "Margin Improving & OpEx Leverage" --> Phase2
        CheckEfficiency -- "No Efficiency" --> Reject
    ```

### 2. Phase 2: DNA 识别 (The Identifier)
*   **商业模式分类**：SaaS、消费云、双边市场、广告等。
*   **KPI 锁定**：自动确定该模式下最重要的特异性指标（如 NDR, GMV, RPO）。

### 3. Phase 3: 蓝天与催化剂 (Blue Sky & Intelligence)
**目标**：量化“梦想”的价值与“时机”的把握。
*   **Blue Sky (期权价值)** (V3.2): 
    *   **R&D 含金量**：是否存在“进攻性研发”带来的第二增长曲线？
    *   **TAM 膨胀**：公司是否具备跨界打劫的能力？
*   **Catalyst Calendar (催化剂)** (V3.2):
    *   **硬事件**：财报日、产品发布会、S&P 500 纳入。
    *   **变异感知**：寻找华尔街预期 (Consensus) 与特异性数据之间的预期差。
*   **软实力画像**：管理层诚信度、护城河变化及内部人交易。

### 4. Phase 4: 最终审判 (The Tribunal)
**目标**：模拟 CIO 决策，输出最终评级。
*   **决策逻辑**：基于 卫生检查 -> 估值定位 -> Alpha 叠加 (期权+催化剂)。
*   **评级体系** (V3.2):
    *   **CONVICTION BUY**: 合理估值 + 高期权价值 + 明确催化剂。
    *   **ACCUMULATE**: 低估值 + 高期权价值 (等待风来)。
    *   **SPECULATIVE BUY**: 高估值 + 极高期权价值 + 强催化剂。
    *   **VALUE TRAP**: 低估值 + 无期权 + 无催化剂 (回避)。
    *   **WATCH/SELL**: 其他情况。

### 5. Phase 5 & 6: 动态监控与卖出策略 (The Exit Strategy)
**目标**：不仅仅是买入，还要会卖出。本系统建议定期（如每季度）运行以下逻辑：
*   **逻辑证伪 (Thesis Broken)**：如果第二曲线孵化失败，或特异性 KPI 连续两季度恶化 -> **无条件清仓**。
*   **预期兑现 (Realization)**：当催化剂事件发生后，如果股价透支（PEG > 2.5-3.0） -> **分批止盈**。
*   **机会成本 (Upgrade)**：如果发现 "CONVICTION BUY" 标的，而手头持有的是 "ACCUMULATE"，坚决**换仓**。

### 总结 (Summary)
**MGP V3.2** 是一套立体的作战体系：
*   **底线**：用 **V3.0** 的财务纪律保底（不亏大钱）。
*   **方向**：用 **V3.1** 的赛道识别避坑（不进死胡同）。
*   **爆发**：用 **V3.2** 的 **期权思维（赚大钱）** 和 **催化剂（快赚钱）** 追求卓越。

这套策略不再被动等待市场发现价值，而是主动出击，预判价值爆发的前夜。

---

## 环境要求

你需要以下 API Key 才能运行此系统：

*   **Financial Modeling Prep (FMP)**: 用于核心财务数据、SBC 数据、现金流分析。
*   **OpenAI API**: 用于逻辑分析、文本理解和决策生成。
*   **Tavily API**: 用于实时网络搜索、情报搜集和事件挖掘。

## 安装指南

1.  **克隆项目**
    ```bash
    git clone <repository_url>
    cd Growth
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境**
    创建 `.env` 文件并填入你的 API Key，或修改 `config.py`：
    ```bash
    FMP_API_KEY=your_fmp_key
    OPENAI_API_KEY=your_openai_key
    TAVILY_API_KEY=your_tavily_key
    ```

## 使用方法

运行 `main.py` 并指定股票代码：

```bash
# 分析单只股票
python main.py --tickers SNOW

# 分析多只股票
python main.py --tickers DDOG,CRWD,UBER

# 强制深度分析（忽略 Iron Gate 失败，强行看基本面）
python main.py --tickers META --force

# 生成中文报告 (默认开启)
python main.py --tickers DUOL --cn
```

## 输出结果

1.  **Markdown 研报 (`REPORT_{TICKER}_{DATE}.md`)**：
    *   包含 V3.2 标准的详细分析：Dilution Check, Blue Sky Analysis, Catalyst Calendar 等。
2.  **JSON 数据 (`results.json`)**：
    *   包含所有分析过程中的结构化数据。

## 项目结构

```
/
├── config.py             # 策略参数配置 (V3.2 阈值)
├── main.py               # CLI 入口 & 报告生成
├── core/                 # 数据模型 (Updated for V3.2)
├── tools/                # API 客户端 (FMP, OpenAI, Tavily)
└── phases/               # 策略核心逻辑
    ├── iron_gate.py      # Phase 1: 铁律 & 稀释盾
    ├── identifier.py     # Phase 2: 模式识别
    ├── intelligence.py   # Phase 3: 蓝天 & 催化剂
    └── tribunal.py       # Phase 4: V3.2 决策引擎
```

## 免责声明

本工具仅用于辅助研究和学习 MGP V3.2 策略，**不构成任何投资建议**。投资有风险，入市需谨慎。
