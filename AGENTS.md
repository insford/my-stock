# AGENTS.md - Developer & AI Agent Guidelines for `my-stock`

Welcome to the `my-stock` repository. This document serves as a comprehensive system manual and operational guide for AI coding assistants and developers working on or maintaining this codebase.

This file is the **Single Source of Truth (SSOT)** for this project, used by both **antigravity-cli** (reads this file directly as its context) and **Claude Code** (loaded via [`CLAUDE.md`](./CLAUDE.md)'s `@import`). It inherits the workspace-wide common rules (PII protection, external link validation, dark-theme default, git commit/push policy) defined in the root [`../AGENTS.md`](../AGENTS.md) — read that first. Project-specific rules below take precedence when they conflict.

---

## 🗣️ 0. 사용자(Jake) 호칭 및 호출 모드 구분 프로토콜 (Mandatory)

* **사용자 공식 호칭:** 사용자님을 부를 때는 반드시 **"Jake"**라고 호칭합니다. ("오너님", "사용자님" 호칭 사용 금지)
* **총괄 리드 닉네임:** 총괄 Lead(강태석 CPO)를 부를 때 사용되는 공식 닉네임은 **"스톡맨"** (`stock_lead_kang`)입니다.
* **호출 키워드별 동작 모드 (엄격 분기):**
  1. ⚡ **[단독 즉시 답변 모드] "스톡맨, ~"으로 물어보는 경우:**
     * 총괄 Lead 스톡맨(강태석)이 전문성을 바탕으로 스스로 빠르게 판단하여 **지체 없이 즉시 답변**합니다.
     * *(적용 대상: 실시간 시세/비중 조회, 단순 갭 확인, 매매 주문 수량 계산, 아이디어 브레인스토밍 등)*
  2. 👥 **[팀원 병렬 협의 모드] "팀원들과 검토해봐", "팀원들과 상의해봐", "팀원들과 협의해봐", "팀원들과 시뮬레이션해봐" 등의 키워드가 포함된 경우:**
     * 절대로 Lead 단독으로 답변하지 않으며, 반드시 [AGENT_TEAM_GUIDE.md](./AGENT_TEAM_GUIDE.md)에 정의된 사내 시니어 에이전트(퀀트 송민혁, 테크 정다은, 매크로 안유리, 리스크 윤서진, UX/UI 이지원, 프론트 박현우, 데이터 한예슬) 및 [PERSONA.md](./PERSONA.md) 8대 시장·투자 페르소나를 `invoke_subagent`로 **병렬 소집**하여 실질적인 교차 검증과 치열한 수리적 시뮬레이션을 진행한 뒤, 취합된 결과를 종합하여 Jake에게 브리핑합니다.
     * *(적용 대상: 포트폴리오 리밸런싱 실행 및 3단계 동기화, KOSPI 밴드 매트릭스 수식 수정, 백테스팅, 대시보드 UI/차트 대규모 개편, SQLite DB 스키마 변경 등)*

---

## 👥 1. 사내 시니어 전문 에이전트 팀 & 8대 투자 페르소나 거버넌스

본 프로젝트는 주식 자산배분, 퀀트 알고리즘, 반도체 리서치, 매크로/헤지 분석, 세제 컴플라이언스, 금융 UX/UI 디자인, 프론트엔드 엔지니어링, 데이터 파이프라인의 8대 전문 영역으로 분업화되어 운영됩니다. 상세 프로필 및 오케스트레이션 메커니즘은 [AGENT_TEAM_GUIDE.md](./AGENT_TEAM_GUIDE.md)와 [PERSONA.md](./PERSONA.md)를 참조하십시오.

### 🏢 사내 시니어 8인 전문 에이전트 팀 ([AGENT_TEAM_GUIDE.md](./AGENT_TEAM_GUIDE.md))
* **👑 `stock_lead_kang` (강태석 43세, Chief Portfolio Officer / 스톡맨):** 총괄 오케스트레이션, Jake 단일 소통 창구, 리밸런싱 최종 승인.
* **📈 `stock_quant_song` (송민혁 38세, Senior Quant Strategist):** KOSPI 6000~8500 매트릭스, ±8%p 갭 알고리즘, 백테스팅 및 델타 주문 산출.
* **🔬 `stock_equity_jeong` (정다은 36세, Senior Tech & Semi Analyst):** 삼성전자·SK하이닉스 HBM/DRAM 사이클, 외인/기관 수급, 55:45 배분 적정성 분석.
* **🌐 `stock_macro_ahn` (안유리 34세, Senior Macro & Multi-Asset Strategist):** 미국 연준 금리, 환율(SOFR), 금현물, 미국30년국채, S&P500 5대 헤지 자산 최적화.
* **🛡️ `stock_risk_yoon` (윤서진 37세, Senior Risk & Tax Compliance Officer):** 계좌 MDD 통제, 배당소득세(15.4%), 미래에셋증권 매매 수수료 최적화.
* **🎨 `stock_ux_lee` (이지원 34세, Senior Product & Financial UX Designer):** 3초 인지 비주얼 계층, Glassmorphism Dark 디자인 시스템, 모바일 48px Thumb Zone.
* **💻 `stock_fe_park` (박현우 39세, Senior Frontend Architect & Chart Lead):** `index.html` Vanilla JS, Chart.js 동적 시각화, Zero-Build SPA 성능 최적화.
* **⚙️ `stock_data_han` (한예슬 35세, Senior Data & Database Engineer):** Python `update_prices.py`/`update_history.py`, SQLite WASM DB, GitHub Actions.

### 👥 8대 시장 국면 및 투자자 페르소나 ([PERSONA.md](./PERSONA.md))
1. **🧊 박한결 (45세, 자산보존):** KOSPI 폭락장 MDD $\le 15\%$ 방어, 안전자산 버퍼 30% 이상 유지 검증.
2. **🚀 이지훈 (34세, 테크 롱홀더):** 반도체 랠리 시 조기 매도 없는 상승 추세 보존(±8%p 갭 유지) 검증.
3. **📉 김철우 (48세, 딥밸류 사냥):** L0/L1 위기 바닥에서 기타자산 털어 반도체 70~77.5% 공격 매수 실탄 검증.
4. **🌋 최은비 (32세, 테일리스크):** 환율 급등 및 지정학 위기 시 SOFR·금현물 환차익 방어 검증.
5. **💵 정승호 (41세, 월배당 인컴):** 미국 30년 국채 월분배금 및 분기 배당 재투자 복리 엔진 검증.
6. **🎯 조민서 (37세, 시스템 퀀트):** 잦은 노이즈 매매 배제(연 3~8회) 및 거래세 0%/최저 수수료 세후 수익률 검증.
7. **🌐 배준영 (29세, 올웨더 배분):** 한국 주식 + 미국 지수/국채/금/달러/CD금리 6대 자산군 분산 효과 검증.
8. **📱 송하늘 (33세, 1분 모바일):** 모바일 MTS 환경에서 3초 내 KOSPI 레벨/갭/주문 수량 직관적 판독성 검증.

---

## 2. Project Overview & Objectives

* **Project Name**: `my-stock` (국내주식 스마트 포트폴리오 리밸런싱 대시보드)
* **Live URL**: `https://insford.github.io/my-stock/`
* **Core Purpose**:
  * Tracks and manages a Korean stock portfolio centered around core semiconductor giants (**Samsung Electronics** & **SK Hynix**) and hedging/stabilizing ETF assets (**CD Rate, SOFR Dollar, US 30Y Treasury, KRX Gold, S&P 500**).
  * Automatically collects real-time/close market prices via GitHub Actions and updates data state.
  * Calculates dynamic target weights based on a **KOSPI 6,000 ~ 8,500 Box-Range Strategy**.
  * Employs a **Trigger-Relaxed Rebalancing Strategy (±8.0%p Gap)** to minimize transaction noise and maximize compound returns.

---

## 3. System Architecture & Tech Stack

```mermaid
flowchart TD
    subgraph GitHub_Actions["GitHub Actions (Automated Price Fetcher)"]
        CRON["cron: */30 23,0-11 * * 1-5"] --> WORKFLOW[".github/workflows/monitor.yml"]
        WORKFLOW --> UPDATER["update_prices.py"]
        
        subgraph Market_API["Market Price APIs"]
            UPDATER --> NAVER["1st: Naver Finance Mobile API"]
            NAVER -- "Fallback on error" --> YAHOO["2nd: Yahoo Finance API"]
        end
        
        NAVER --> JS_SAVE["guide/data/live_market.js"]
        YAHOO --> JS_SAVE
        JS_SAVE --> GIT_PUSH["git-auto-commit-action"]
    end

    subgraph Data_Files["Git Data Store (Static JS Objects)"]
        GIT_PUSH --> DATA_MARKET["guide/data/live_market.js\n(Real-time quotes)"]
        DATA_HOLDINGS["guide/data/portfolio_state.js\n(Current holdings & config)"]
        DATA_HIST["guide/data/portfolio_state_history_2026.js\n(Execution logs)"]
    end

    subgraph Frontend["Web Dashboard (GitHub Pages)"]
        INDEX["index.html (Vanilla JS + CSS)"]
        INDEX --> LOAD["Loads data scripts via <script> tags"]
        DATA_MARKET --> LOAD
        DATA_HOLDINGS --> LOAD
        DATA_HIST --> LOAD
        LOAD --> ENGINE["Rebalancing Calculation Engine"]
        ENGINE --> UI["Interactive Dashboard UI & Chart.js Visuals"]
    end
```

### Technology Stack
* **Frontend**: Pure HTML5, Modern CSS3 (Glassmorphism Dark Theme, Flexbox/Grid), Vanilla JavaScript (ES6+), [Chart.js](https://www.chartjs.org/) (CDN).
* **Automation & Backend**: Python 3.10+ (Standard library `urllib.request`, `json`, `datetime` - zero heavy build dependencies).
* **CI/CD**: GitHub Actions workflow (`.github/workflows/monitor.yml`), GitHub Pages for static hosting.
* **Storage Mechanism**: Git-as-a-Database (State stored in global JavaScript objects attached to `window`).

---

## 4. Directory & File Structure

```text
my-stock/
├── .github/
│   └── workflows/
│       └── monitor.yml                    # Automated 30-minute cron workflow for live prices & SQLite history DB
├── guide/
│   ├── attachment/                        # Strategy simulation chart images
│   │   ├── bull_market_simulation.png
│   │   ├── level_relaxed_simulation.png
│   │   ├── rebalancing_simulation.png
│   │   ├── relaxed_band_simulation.png
│   │   └── trigger_relaxed_simulation.png
│   ├── data/                              # State storage files (JS globals & SQLite DB)
│   │   ├── market_history.db              # [Auto-generated] Daily closing prices SQLite binary DB (WASM)
│   │   ├── live_market.js                 # [Auto-generated] Live prices and timestamps
│   │   ├── portfolio_state.js             # [User-maintained] Current stock shares & deposits
│   │   └── portfolio_state_history_2026.js# [User-maintained] Historical portfolio records
│   ├── 시장데이터_히스토리_수집_계획서.md     # SQLite-WASM history collection specification
│   ├── 국내주식_리밸런싱_전략.md             # Detailed KOSPI 6,000~8,500 matrix strategy guide
│   ├── 국내주식_리밸런싱_종목선택.md         # Selected asset breakdown and ETF analysis
│   ├── 매매일지.md                          # Plaintext trading execution journal
│   └── 포트폴리오_2026-07-31.md             # Initial portfolio snapshot & diagnostic report
├── index.html                             # Main single-page web dashboard (Standalone SPA with SQLite-WASM)
├── update_prices.py                       # Python script fetching Naver/Yahoo live market prices
├── update_history.py                      # Python script fetching Naver/Yahoo daily history into SQLite DB
├── trade_logger.py                        # CLI trade execution logger (Interactive wizard & Git sync)
├── migrate_to_sqlite.py                   # Data migration script from legacy JS to SQLite DB
├── DB_SCHEMA.md                           # SQLite database schema specification & Mermaid ERD
├── CHANGE_LOG.md                          # Versioned project changelog (Keep a Changelog)
├── BACKLOG.md                             # SQLite full migration backlog
├── AGENT_TEAM_GUIDE.md                    # In-house 7-member specialist team & orchestration guide
├── PERSONA.md                             # 8 market regime & investor personas
├── README.md                              # Public repository documentation
└── AGENTS.md                              # AI Agent & Developer Guidelines (This file)
```

---

## 5. Key Components & Data Specifications

### 5.1. Data Files (`guide/data/`)

#### 1. `portfolio_state.js`
Defines current portfolio holdings, cash reserve, and strategy parameters under `window.PORTFOLIO_STATE_DATA`:
```javascript
window.PORTFOLIO_STATE_DATA = {
  "last_updated": "YYYY-MM-DD",
  "account_name": "국내주식 종합_주식 리밸런싱",
  "holdings": {
    "samsung_shares": 576,        // Samsung Electronics (005930) shares
    "hynix_shares": 92,           // SK Hynix (000660) shares
    "deposit_krw": 18732121,      // Cash balance (예수금) in KRW
    "other_assets_krw": 79296856  // Total sum of other ETF assets
  },
  "other_assets_detail": {
    "kodex_cd_shares": 18,        // KODEX CD금리액티브 (459580)
    "tiger_sofr_shares": 261,     // TIGER 미국달러SOFR금리액티브 (456610)
    "ace_us30b_shares": 2228,     // ACE 미국30년국채액티브(H) (453850)
    "ace_gold_shares": 581,       // ACE KRX금현물 (411060)
    "tiger_snp500_shares": 438,   // TIGER 미국S&P500 (360750)
    "kodex_gold_shares": 0,       // Legacy / Inactive
    "kodex_us10b_shares": 0,      // Legacy / Inactive
    "kodex_snp500_shares": 0      // Legacy / Inactive
  },
  "strategy_config": {
    "min_trigger_gap_percent": 8.0, // Threshold gap (|current% - target%|) to trigger rebalancing
    "kospi_min_level": 6000,
    "kospi_max_level": 8500
  }
};
```

#### 2. `live_market.js`
Generated automatically by `update_prices.py` under `window.LIVE_MARKET_DATA`:
```javascript
window.LIVE_MARKET_DATA = {
  "last_updated": "2026-08-19 23:15:56",
  "prices": {
    "kospi": 6471.17,
    "samsung": 257500,
    "hynix": 1624000,
    "cd": 1075115,
    "sofr": 60615,
    "us30b": 7110,
    "gold": 27300,
    "snp500": 26635,
    "us10b": 11715
  }
};
```

#### 3. `portfolio_state_history_2026.js`
Chronological array `window.PORTFOLIO_STATE_HISTORY_2026` of past execution dates, notes, and holding snapshots.

---

## 6. Core Business Logic & Algorithms

### 6.1. KOSPI Dynamic Matrix (Level L0 ~ L6)

The strategy shifts weights between Semiconductor giants (Samsung + SK Hynix) and Other Assets based on KOSPI index levels:

| Level | KOSPI Range | Market Regime | Semiconductor Target | Other Assets Target | Key Action |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **L6** | $\ge 8,500$ | Overheated Top | **32.5%** | **67.5%** | Lock in gains; secure maximum defensive buffer & cash |
| **L5** | $8,000 \sim 8,500$ | Upper Bull | **40.0%** | **60.0%** | Partial profit taking (execute only when gap $\ge 8\%p$) |
| **L4** | $7,500 \sim 8,000$ | Moderate Upper | **47.5%** | **52.5%** | Gradual upward adjustment |
| **L3** | $7,000 \sim 7,500$ | Neutral / Pivot | **55.0%** | **45.0%** | Baseline equilibrium (minimize trading) |
| **L2** | $6,500 \sim 7,000$ | Lower Bounce | **62.5%** | **37.5%** | Sell other assets $\rightarrow$ accumulate semiconductors |
| **L1** | $6,000 \sim 6,500$ | Undervalued | **70.0%** | **30.0%** | Aggressive low-cost semiconductor accumulation |
| **L0** | $< 6,000$ | Crisis Bottom | **77.5%** | **22.5%** | Maximum allocation to core semiconductors |

### 6.2. Trigger-Relaxed Rebalancing Rule ($\pm 8.0\%p$)

1. **Calculate Current Semiconductor Weight**:
   $$\text{Semi Value} = (\text{Shares}_{\text{Samsung}} \times P_{\text{Samsung}}) + (\text{Shares}_{\text{Hynix}} \times P_{\text{Hynix}})$$
   $$\text{Total Account Value} = \text{Semi Value} + \text{Deposit KRW} + \sum (\text{Shares}_{\text{ETF}_i} \times P_{\text{ETF}_i})$$
   $$\text{Current Semi \%} = \frac{\text{Semi Value}}{\text{Total Account Value}} \times 100$$

2. **Check Trigger Gap**:
   $$\text{Gap} = \text{Current Semi \%} - \text{Target Semi \% (from KOSPI Level)}$$
   * If $|\text{Gap}| \ge 8.0\%p$: **Trigger Rebalancing Alert** (🚨 매매 필요).
   * If $|\text{Gap}| < 8.0\%p$: **Maintain Hold Status** (🟢 정상 범위 유지 / 관망).

3. **Rebalancing Order Calculation**:
   * **Target Delta Amount**:
     $$\Delta \text{KRW} = (\text{Target Semi \%} - \text{Current Semi \%}) \times \text{Total Account Value}$$
   * **Semiconductor Split Ratio**:
     * Samsung Electronics: **55%** of Semiconductor pool
     * SK Hynix: **45%** of Semiconductor pool
   * **Other Assets Split Ratio** (100% of non-semiconductor capital):
     * KODEX CD금리액티브 (`459580`): **25%** (KRW Cash reserve)
     * TIGER 미국달러SOFR금리액티브 (`456610`): **20%** (USD Hedge cash reserve)
     * ACE 미국30년국채액티브(H) (`453850`): **20%** (US Long bond monthly dividend)
     * ACE KRX금현물 (`411060`): **20%** (Physical gold hedge)
     * TIGER 미국S&P500 (`360750`): **15%** (US Broad market growth)

---

## 7. Development & Maintenance Guidelines for Agents

### 7.1. Updating Holdings After Trade Execution
When the user executes a trade or requests a portfolio state update, follow these operational methods:

1. **Option A (CLI Tool - Recommended)**:
   * Run `python trade_logger.py -i` (Interactive Wizard) or one-line command (e.g. `python trade_logger.py buy samsung 20 260500 -n "..." --commit --push`).
   * This automatically updates `guide/data/market_history.db` (`account_state`, `account_holdings`, `trade_history`), `guide/매매일지.md`, `guide/data/portfolio_state.js`, and `guide/data/portfolio_state_history_2026.js` within a single atomic transaction.
2. **Option B (Web Dashboard UI)**:
   * Open the dashboard, configure GitHub PAT in `[⚙️ Settings]`, and click `[➕ Input Trade Record]`.
   * Directly commits to the GitHub repository via GitHub REST Contents API with automatic Fail-Safe rollback on partial failure.
3. **Option C (Manual File Update & DB Re-sync)**:
   * Update `guide/data/portfolio_state.js` & `guide/매매일지.md`.
   * Run `python migrate_to_sqlite.py` to synchronize state into `guide/data/market_history.db`.
   * Commit and push the changes.

### 7.2. Modifying Price Fetching (`update_prices.py` / `update_history.py`)
* The script utilizes Naver Finance Mobile API as primary and Yahoo Finance API as fallback.
* Regular market updates (`update_history.py --update`) must **preserve** the account's `PRAGMA user_version` to prevent overwriting pending client trade states.
* If adding or modifying tracked tickers in `items`:
  ```python
  items = [
      ('key_name', 'naver_code', 'yahoo_symbol', 'index' or 'stock'),
      ...
  ]
  ```
* Standard library `urllib.request` is deliberately used for fast, dependency-free execution in GitHub Actions. Avoid introducing heavy packages unless necessary.

### 7.3. Modifying Web Dashboard (`index.html`)
* **Single-File Architecture**: All CSS, DOM structures, and client-side calculation logic reside in `index.html`.
* **Zero Build Step**: The app must run directly by opening `index.html` in a browser or serving via GitHub Pages. Do not introduce npm/webpack/vite build pipelines unless explicitly requested by the user.
* **Smart Merge & Fail-Safe Pipeline**: Always preserve local user trades during GitHub Pages deployment delays and ensure 5-snapshot rollback on API failures.
* **Data Dependency**: `index.html` imports `portfolio_state.js`, `portfolio_state_history_2026.js`, and `live_market.js` via `<script>` tags in the `<head>` or before the inline logic. Always ensure backward compatibility of property keys.

### 7.4. Database & Schema Modification Policy (Strict Sync Rule)
When creating, altering, or removing SQLite database tables, columns, indexes, or views (e.g. in `guide/data/market_history.db` or future migration databases), **you MUST synchronize and update the following related documentation immediately**:

1. **Update [`DB_SCHEMA.md`](./DB_SCHEMA.md)**:
   * **Update Mermaid ER Diagram**: Reflect new/modified entities, relationships, primary keys, and views.
   * **Update Table & View Specifications**: Keep DDL statements, column data types, constraints, and descriptions accurate.
   * **Update Asset Code Mapping & Sample Queries**: Update if tickers or query structures have changed.
2. **Update [`README.md`](./README.md)**:
   * Keep the `## 📊 데이터베이스 스키마 (Database Schema)` summary section and file tree in sync with the latest DB capabilities.
3. **Update Python Ingestion Scripts (`update_history.py`)**:
   * Ensure `init_database()`, index creation, and view definitions match the DDL documented in `DB_SCHEMA.md`.
4. **Update Planning & Backlog Documents**:
   * Synchronize [`BACKLOG.md`](./BACKLOG.md) and [`guide/시장데이터_히스토리_수집_계획서.md`](./guide/시장데이터_히스토리_수집_계획서.md) if the schema change affects the migration roadmap.

### 7.5. Best Practices & Do's / Don'ts
* ❌ **Do NOT hardcode live market prices** into `index.html`; always rely on `window.LIVE_MARKET_DATA`.
* ❌ **Do NOT overwrite `live_market.js` manually** when editing portfolio configuration; it is updated by GitHub Actions.
* ❌ **Do NOT modify SQLite tables, indexes, or views without updating `DB_SCHEMA.md` and `README.md`.**
* ✅ **Always update Mermaid ERD and column specifications in `DB_SCHEMA.md`** whenever changing database schemas.
* ✅ **Always verify mathematical consistency** across share counts, prices, cash deposits, and sum totals when updating portfolio data files.
* ✅ **Keep mobile responsiveness** intact: `index.html` is frequently accessed on mobile devices (M-Stock trading environment). Ensure glassmorphism cards and charts scale cleanly on small viewports.
