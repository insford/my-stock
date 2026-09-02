# 📝 변경 이력 (CHANGE_LOG.md)

본 문서는 `my-stock` 프로젝트의 버전별 신규 기능 추가, 아키텍처 개선, 버그 수정 및 보안 패치 내역을 기록하는 공식 변경 이력 문서입니다.  
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)의 규격을 준수합니다.

---

## [v1.2.1] - 2026-09-02

### 🎨 UX & UI Improvements (사용자 경험 개선)
* **계좌 동기화 뱃지 UI/UX 전면 개편 (`index.html`)**:
  * **3초 인지 원칙 적용**: 라벨을 `🗄️ 계좌DB:`로 직관화하고, 괄호 안에 `(매매: MM. DD. HH:MM)` 컨텍스트를 명시하여 좌측 실시간 시세 시간과의 인지 부조화(Mental Model Mismatch)를 완벽 해소.
  * **모바일 터치 어포던스 및 토스트 연동**: 모바일 환경에서 뱃지 탭(클릭) 시 계좌 매매 버전과 최신 시세 수집 일시를 하단 토스트로 안내하는 `showDbVersionToast()` 추가.
  * **반응형 텍스트 최적화**: 배포 진행 중 텍스트를 `⏳ 배포 동기화 중 (매매: 시간)`으로 슬림화하여 모바일 초소형 뷰포트에서의 불규칙한 줄바꿈 방지.

### 🛡️ Fixed & Code Quality (안정성 강화)
* **`formatUnixTimestamp` 비정상 입력값 방어**:
  * `ts`에 `Number()` 변환 및 `isNaN`, 음수 필터링을 추가하여 비정상 타임스탬프 파싱 시 `RangeError` 크래시 원천 차단.
* **Smart Merge 매매 직후/새로고침 툴팁 상세도 일원화 (DRY)**:
  * 매매 모달에서 매매 즉시 반영 시점과 새로고침 후 시점의 뱃지 툴팁 정보를 일치시켜 상태 전이의 일관성 확보.

---

## [v1.2.0] - 2026-08-28

### 🚀 Added (신규 기능)
* **단일 통합 SQLite 데이터베이스 전면 구축 (`guide/data/market_history.db`)**:
  * 계좌 상태(`account_state`), 보유 수량(`account_holdings`), 매매 이력(`trade_history`), 일별 시장 시세(`market_history`) 4대 테이블 통합.
  * 실시간 종목별 평가액 뷰(`v_account_valuation`) 및 전일 대비 등락률 뷰(`v_market_history`) 신설.
  * `idx_code_date`, `idx_trade_date` 최적화 인덱스 적용.
* **로컬 CLI 매매 기록 도구 (`trade_logger.py`) 신규 개발**:
  * 대화형 인터랙티브 마법사(`python trade_logger.py -i`) 지원.
  * 명령행 한 줄 거래 기록 (`buy`, `sell`, `rebalance`, `deposit`, `withdraw`) 및 자동 Git 커밋/푸시(`--commit --push`) 지원.
  * 포트폴리오 실시간 현황(`--status`) 및 과거 매매 이력(`--history`) 터미널 뷰어 제공.
* **웹 대시보드 매매 기록 및 GitHub 연동 엔진 (`index.html`)**:
  * 상단 `[⚙️ GitHub 연동 설정]` 모달: GitHub PAT를 브라우저 `localStorage`에 안전하게 보관 및 원클릭 연결 테스트 지원.
  * `[➕ 매매 기록 입력]` 모달: 실시간 시세 자동완성, 매수/매도/리밸런싱/입출금 탭, 실시간 비중 및 이탈 격차 프리뷰 제공.
  * GitHub REST Contents API를 통해 브라우저에서 직접 4대 파일(`market_history.db`, `portfolio_state.js`, `portfolio_state_history_2026.js`, `매매일지.md`)을 원클릭으로 0.5초 만에 커밋 & 푸시.
* **Smart Merge (스마트 머지) 엔진 구축**:
  * GitHub Pages CDN 배포 딜레이(15~45초) 중 브라우저 새로고침 시, 서버 DB와 로컬 DB의 `trade_history` (`MAX(trade_id)`, `COUNT(*)`)를 교차 비교.
  * 로컬 매매 기록을 100% 안전하게 보존하면서 서버의 최신 시세(`market_history`)만 인메모리 Upsert 병합하여 데이터 유실 원천 방지.
* **데이터 무손실 마이그레이션 스크립트 (`migrate_to_sqlite.py`) 개발**:
  * 기존 JS/MD 파일의 계좌 및 10건의 과거 매매 데이터를 SQLite DB로 100% 무손실 이관.
* **공식 데이터베이스 스키마 명세서 (`DB_SCHEMA.md`) 작성**:
  * Mermaid ER 다이어그램, DDL 스키마, 자산 코드 매핑, 주요 SQL 쿼리 예제 수록.

### 🛡️ Fixed & Security (버그 수정 및 무결성 강화)
* **[Critical] 정기 시세 수집 시 `PRAGMA user_version` 보존**:
  * `update_history.py`에서 `mode != "init"` 시 계좌 버전을 훼손하지 않도록 수정하여 로컬 매매 덮어쓰기 유실 결함 완벽 해결.
* **[High] 유령 현금(Ghost Cash) 생성 결함 차단**:
  * `index.html`에서 보유 수량 초과 매도 시 `Math.min(shares, currentHolding)` 클램프 적용 및 실제 체결 수량 기반으로만 예수금 가산.
* **[High] Fail-Safe 선제 스냅샷 롤백 파이프라인 구축**:
  * DB 수정 직전에 **메모리 상태, History 배열, WASM DB 바이너리, LocalStorage 캐시/버전 5종 스냅샷**을 선제 백업.
  * 원격 푸시 실패 시 `catch` 블록에서 메모리/DB/LocalStorage를 100% 원상태로 완전 롤백 복구.
* **[High] `trade_logger.py` 단일 트랜잭션 DB Lock 방지**:
  * `sync_legacy_files`에 기존 활성 `conn`을 전달하여 중복 연결 생성으로 인한 `database is locked` 오류 차단 및 원자적 롤백 결합.
  * `atomic_write_file` (.tmp ➔ atomic replace) 유틸리티 적용으로 파일 쓰기 중 크래시 방지.
* **[High] 4대 파일 일괄 동기화 무결성 확보**:
  * `portfolio_state_history_2026.js` 푸시 시 `[...dynamicHistoryList, rawSnapshot]` 직렬화로 신규 매매 누락 방지.
  * `매매일지.md` 커밋 단계의 `try-catch` swallow를 제거하여 4개 파일 중 하나라도 실패 시 전체 롤백되도록 트랜잭션 원자성 보장.
* **[Medium] 실시간 시세 로딩 지연 가드 (`isLiveMarketReady`)**:
  * 시세 API 통신 완료 전 0원/placeholder 단가로 매매가 집행되는 것을 모달 오픈 및 저장 실행 시점에 이중 차단.
* **[Medium] 리밸런싱 정수 제약 강제**:
  * HTML input 태그에 `step="1"` 부여 및 JS `parseInt(..., 10)` 적용으로 소수점 주식 수 저장 방지.
* **[Medium] 레거시 자산 청산 드롭다운 지원**:
  * 매매 입력 드롭다운에 `us10b`(KODEX 미국채10년액티브) 및 `fadu`(파두) 옵션 추가 및 시뮬레이션 계산 로직 편입.
* **[UX/UI] 에러 피드백 및 Empty State UI 복원**:
  * `updateDashboard` 예외 발생 시 사용자 안내 토스트 표출.
  * `renderHistoryTab`에서 데이터 부재 시 직관적인 Empty State 카드(`📭`) 표출 및 지표 0 초기화.
* **[Security] Stored/DOM XSS 방어**:
  * `escapeHtml()` 유틸리티 함수 도입으로 `item.note` 기반 XSS 및 GitHub PAT 탈취 위험 원천 차단.
* **[Encoding] 다국어 UTF-8 Base64 표준 인코딩**:
  * `utf8ToBase64()`, `base64ToUtf8()` 표준 TextEncoder/TextDecoder 구현으로 한글/특수문자 무손실 직렬화.

---

## [v1.1.0] - 2026-08-27

### 🚀 Added
* **SQLite-WASM (`sql.js`) 인메모리 데이터 엔진 도입**:
  * GitHub Pages 정적 환경에서 `guide/data/market_history.db` 바이너리를 직접 fetch하여 브라우저 메모리 내 SQLite 쿼리 실행.
* **50거래일 자산 히스토리 & 리밸런싱 타임라인 차트 (`index.html`)**:
  * Chart.js 기반 50일 연속 누적 스택 바 차트 구현.
  * 매매 집행 당일 깃발(🚩) 마커 및 툴팁 상세 매매 사유/금액 표시 기능.
  * 기간 필터 (`1M`, `3M`, `ALL`) 지원.
* **자동 시세 수집 배치 파이프라인 (`update_history.py`)**:
  * 네이버 금융 모바일 API 및 야후 파이낸스 API 기반 8대 종목/지수 일별 종가 자동 수집.
  * GitHub Actions 워크플로우(`.github/workflows/monitor.yml`) 연동 (평일 30분 주기 실행).

---

## [v1.0.0] - 2026-08-19

### 🚀 Added
* **국내주식 스마트 포트폴리오 리밸런싱 대시보드 최초 런칭**:
  * KOSPI 6,000 ~ 8,500 박스권 연동 7단계(L0~L6) 동적 목표 비중 매트릭스 전략 구현.
  * **Trigger-Relaxed (±8.0%p 갭)** 리밸런싱 알림 알고리즘 탑재.
* **핵심 자산 포트폴리오 구성**:
  * 반도체 코어 2종: 삼성전자 (55%), SK하이닉스 (45%)
  * 방어 및 헤지 5종: KODEX CD금리 (25%), TIGER SOFR (20%), ACE 미국30년국채 (20%), ACE KRX금현물 (20%), TIGER S&P500 (15%)
* **Glassmorphism Dark UI & 모바일 반응형 디자인**:
  * Zero-Build Vanilla JavaScript SPA 아키텍처.
  * 모바일 MTS 화면(360px~480px) 전용 카드 뷰 및 반응형 레이아웃 지원.
