# 📋 `my-stock` 프로젝트 개발 백로그 (BACKLOG.md)

본 문서는 향후 진행할 아키텍처 고도화 및 데이터베이스 전면 마이그레이션 작업의 백로그 항목들을 기록·관리하는 문서입니다.

---

## 📌 [BACKLOG-01] 포트폴리오 상태 및 매매 일지의 SQLite 전면 마이그레이션

### 1. 배경 및 목적
* **현재 상태**:
  * `guide/data/portfolio_state.js`: 현재 주식 보유 수량 및 예수금 (JS 전역 변수)
  * `guide/data/portfolio_state_history_2026.js`: 과거 매매 집행 스냅샷 기록 (JS 배열)
  * `guide/매매일지.md`: 마크다운 텍스트 매매 기록
  * `guide/data/market_history.db`: 일별 시장 가격 히스토리 (SQLite DB)
* **목표**: 분산되어 있는 포트폴리오 상태 관리 체계를 **단일 SQLite 데이터베이스(`guide/data/my_stock.db`)**로 통합하여 데이터 무결성 및 SQL 기반 통계 분석 기능을 극대화합니다.

---

### 2. 목표 데이터베이스 스키마 설계 (안)

```sql
-- 1. 보유 계좌 및 자산 현황 테이블 (portfolio_state 대체)
CREATE TABLE IF NOT EXISTS account_state (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    deposit_krw INTEGER NOT NULL,
    min_trigger_gap REAL DEFAULT 8.0,
    updated_at TEXT NOT NULL
);

-- 2. 자산별 보유 수량 테이블
CREATE TABLE IF NOT EXISTS account_holdings (
    code TEXT PRIMARY KEY,
    shares INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

-- 3. 매매 거래 이력 테이블 (portfolio_state_history & 매매일지 대체)
CREATE TABLE IF NOT EXISTS trade_history (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,         -- YYYY-MM-DD
    trade_type TEXT NOT NULL,         -- REBALANCE, BUY, SELL, DEPOSIT, WITHDRAW
    note TEXT,
    samsung_shares INTEGER,
    hynix_shares INTEGER,
    deposit_krw INTEGER,
    created_at TEXT NOT NULL
);

-- 4. 시장 가격 히스토리 테이블 (현재 구축 완료)
CREATE TABLE IF NOT EXISTS market_history (
    date TEXT NOT NULL,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    price REAL NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (date, code)
);
```

---

### 3. 작업 항목 (Task Checklist)

- [ ] **Data Migration**: 기존 `portfolio_state.js` 및 `portfolio_state_history_2026.js` 데이터를 SQLite 테이블로 이관하는 마이그레이션 스크립트(`migrate_to_sqlite.py`) 개발
- [ ] **CLI / Update Tooling**: 매매 집행 후 터미널 또는 웹 UI에서 손쉽게 매매 내역을 SQLite에 INSERT할 수 있는 툴링 제공
- [ ] **Frontend Refactoring**: `index.html`에서 JS 파일 의존성을 제거하고, WASM SQL 쿼리(`SELECT ...`)로 현재 보유 비중 및 리밸런싱 주문을 계산하도록 로직 전환
- [ ] **Documentation Sync**: `AGENTS.md` 및 `README.md`의 데이터 갱신 가이드를 SQLite 기준으로 전면 개정

---

### 4. 마이그레이션 시 고려사항
* **정적 호스팅 호환성**: GitHub Pages 환경에서 프론트엔드가 DB를 읽기 전용(Read-only)으로 WASM 마운트하여 렌더링하는 현재 구조 유지.
* **하위 호환성 유지**: 마이그레이션 과도기 동안 레거시 JS 파일과 SQLite DB 간 동기화 브릿지 유지 고려.

---
*생성일: 2026-08-28*
