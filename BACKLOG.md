# 📋 `my-stock` 프로젝트 개발 백로그 (BACKLOG.md)

본 문서는 향후 진행할 아키텍처 고도화 및 데이터베이스 전면 마이그레이션 작업의 백로그 항목들을 기록·관리하는 문서입니다.

---

## 📌 [BACKLOG-01] 포트폴리오 상태 및 매매 일지의 SQLite 전면 마이그레이션 (✅ 완료)

### 1. 배경 및 목적
* **기존 상태**:
  * `guide/data/portfolio_state.js`: 현재 주식 보유 수량 및 예수금 (JS 전역 변수)
  * `guide/data/portfolio_state_history_2026.js`: 과거 매매 집행 스냅샷 기록 (JS 배열)
  * `guide/매매일지.md`: 마크다운 텍스트 매매 기록
  * `guide/data/market_history.db`: 일별 시장 가격 히스토리 (SQLite DB)
* **완료된 목표**: 분산되어 있던 포트폴리오 상태 관리 체계를 **단일 통합 SQLite 데이터베이스(`guide/data/market_history.db`)**로 전면 마이그레이션하여 데이터 무결성, SQL 기반 집계 분석 및 서버리스 다이렉트 매매 기록 환경 구축 완료.

---

### 2. 구축 완료된 데이터베이스 스키마

```sql
-- 1. 보유 계좌 및 전략 설정 현황 테이블
CREATE TABLE IF NOT EXISTS account_state (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    deposit_krw INTEGER NOT NULL,
    min_trigger_gap REAL DEFAULT 8.0,
    kospi_min_level REAL DEFAULT 6000.0,
    kospi_max_level REAL DEFAULT 8500.0,
    updated_at TEXT NOT NULL
);

-- 2. 자산별 보유 수량 테이블
CREATE TABLE IF NOT EXISTS account_holdings (
    code TEXT PRIMARY KEY,
    shares INTEGER NOT NULL,
    target_ratio REAL DEFAULT 0.0,
    updated_at TEXT NOT NULL
);

-- 3. 매매 거래 이력 테이블
CREATE TABLE IF NOT EXISTS trade_history (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    note TEXT,
    kospi_point REAL,
    samsung_shares INTEGER NOT NULL DEFAULT 0,
    hynix_shares INTEGER NOT NULL DEFAULT 0,
    cd_shares INTEGER NOT NULL DEFAULT 0,
    sofr_shares INTEGER NOT NULL DEFAULT 0,
    us30b_shares INTEGER NOT NULL DEFAULT 0,
    gold_shares INTEGER NOT NULL DEFAULT 0,
    snp500_shares INTEGER NOT NULL DEFAULT 0,
    us10b_shares INTEGER NOT NULL DEFAULT 0,
    fadu_shares INTEGER NOT NULL DEFAULT 0,
    deposit_krw INTEGER NOT NULL DEFAULT 0,
    total_eval_krw INTEGER DEFAULT 0,
    raw_json TEXT,
    created_at TEXT NOT NULL
);

-- 4. 시장 가격 히스토리 테이블
CREATE TABLE IF NOT EXISTS market_history (
    date TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    price REAL NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (date, code)
);

-- 5. 실시간 계좌 평가 뷰
CREATE VIEW IF NOT EXISTS v_account_valuation AS
SELECT 
    h.code,
    COALESCE(m.name, h.code) AS name,
    h.shares,
    m.price AS latest_price,
    CAST(ROUND(h.shares * COALESCE(m.price, 0)) AS INTEGER) AS eval_krw,
    m.date AS price_date,
    h.updated_at AS holdings_updated_at
FROM account_holdings h
LEFT JOIN market_history m ON h.code = m.code
WHERE m.date = (SELECT MAX(date) FROM market_history WHERE code = h.code)
   OR m.date IS NULL;
```

---

### 3. 작업 항목 완료 결과 (Task Checklist)

- [x] **Data Migration**: 기존 `portfolio_state.js` 및 `portfolio_state_history_2026.js` 데이터를 SQLite 테이블로 완전 이관하는 마이그레이션 스크립트(`migrate_to_sqlite.py`) 개발 및 10건의 과거 거래 이력 무손실 적재 완료
- [x] **[방안 A] Web UI 매매 기록기 (GitHub REST API 연동)**:
  - `index.html` 상단에 `[⚙️ GitHub 연동 설정]` (GitHub PAT 등록/관리, `localStorage` 안전 보관) 및 `[➕ 매매 기록 입력]` 모달 팝업 구현
  - 종목 선택(삼성전자, SK하이닉스, ETF 등), 매수/매도/리밸런싱/입출금 구분, 체결 수량, 체결 단가(실시간가 자동완성), 예수금 변동 입력폼 제공
  - 브라우저 JS에서 변경된 보유 수량 및 시뮬레이션 비중 프리뷰 제공 후, **GitHub REST Contents API (`PUT /repos/.../contents/...`)를 호출하여 저장소에 직접 DB 및 상태 파일 Commit & Push** 실행 (서버리스 0.5초 완료)
  - 저장 완료 후 대시보드 실시간 자동 새로고침 및 성공 토스트 알림 표시
- [x] **[간단한 방안] 초간편 로컬 매매 기록 CLI 도구 (`trade_logger.py`)**:
  - 터미널에서 한 줄 명령어로 매매 내역을 즉시 기록하고 Git Push하는 간편 툴 제공 (`python trade_logger.py buy samsung 20 260500 -n "밴드 하단 추가 매수" --commit`)
  - 대화형 인터랙티브 마법사(`python trade_logger.py -i`) 지원
  - 현재 현황 조회(`--status`) 및 매매 이력 조회(`--history`) 지원
- [x] **Frontend Refactoring**: `index.html`에서 JS 파일 의존성을 제거하고, WASM SQL 쿼리(`SELECT ... FROM account_state / account_holdings / trade_history / market_history`)로 현재 보유 비중 및 타임라인 차트를 계산하도록 로직 전환
- [x] **Documentation Sync**: `DB_SCHEMA.md`, `README.md`, `AGENTS.md`의 데이터 갱신 가이드를 SQLite 및 웹 UI 기록기 기준으로 전면 개정

---

## 📌 [BACKLOG-02] 과거 시세 기반 리밸런싱 타임라인 & 백테스팅 시각화

### 1. 배경 및 목적
* SQLite DB에 축적된 50거래일 데이터를 활용하여 과거 특정 시점의 반도체 비중 추이 및 리밸런싱 트리거(±8.0%p Gap) 이탈 발생 시점을 타임라인 형태로 시각화합니다.

### 2. 작업 항목
- [ ] **Timeline Engine**: 일자별 반도체 비중 추이 및 밴드 이탈 여부 자동 계산 쿼리/로직 구현
- [ ] **Visual Chart**: 차트 툴팁 및 타임라인에 과거 리밸런싱 신호 발생 일자 강조 표시

---

## 📌 [BACKLOG-03] 모바일 MTS 거래 환경 UI/가독성 최적화

### 1. 배경 및 목적
* 주식 매매 앱(MTS) 웹뷰 또는 모바일 환경에서 분할 화면으로 조회 시 카드 패딩, 테이블 폰트 및 차트 렌더링 가독성을 극대화합니다.

### 2. 작업 항목
- [ ] **MTS Responsive Viewport**: 초소형 화면(360px 이하)에서의 레이아웃 깨짐 방지 및 터치 타깃 최적화
- [ ] **Table Density Toggle**: 데스크톱/모바일 요약 뷰 간 간결한 테이블 밀도 조절

---
*최종 갱신일: 2026-08-28*
