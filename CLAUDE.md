@../AGENTS.md
@AGENTS.md

---

## 🔀 Claude Code ↔ antigravity-cli 동시 작업 브리지

이 프로젝트(`my-stock`)는 **antigravity-cli**(Gemini 기반, `GEMINI.md`/`AGENTS.md`/`invoke_subagent` 체계)와 **Claude Code** 두 CLI로 병행 작업됩니다. 위 두 줄의 `@import`가 두 도구가 공유하는 단일 원본(Single Source of Truth)을 이 파일에 그대로 불러옵니다.

> ⚠️ **내용을 이 파일에 복사/재작성하지 마세요.** KOSPI 박스권 리밸런싱 전략, 데이터 파일 스펙, 개발 가이드라인 등 모든 실질 규칙은 [AGENTS.md](./AGENTS.md)에만 존재합니다. 수정이 필요하면 원본 문서를 고치세요 — 그래야 antigravity-cli 세션도 동일한 내용을 즉시 참조합니다.

### ⚠️ 동시 작업 시 상태 충돌 방지 (중요)
* `guide/data/live_market.js`는 **30분 주기 GitHub Actions 워크플로(`monitor.yml`)가 자동으로 갱신·커밋·푸시**하는 파일입니다. 이 파일을 직접 편집하지 말고, 작업 시작 전 `git status` / `git log -3`으로 Actions 자동 커밋 또는 다른 세션(특히 antigravity-cli)의 미반영 변경사항이 있는지 먼저 확인한 뒤 `git pull`로 최신 상태를 받습니다.
* `guide/data/portfolio_state.js`(보유 수량)와 `guide/data/portfolio_state_history_2026.js`(거래 이력)는 사용자 요청에 따라 AI가 수정하는 파일입니다. 수정 시 [AGENTS.md §6.1](./AGENTS.md#61-updating-holdings-after-trade-execution)의 3단계 동기화 절차(포트폴리오 상태 → 이력 → 매매일지)를 반드시 순서대로 따릅니다.
* Git 커밋/푸시는 [루트 AGENTS.md §5](../AGENTS.md#5-서브-프로젝트-작업-및-git-동기화-운영-원칙)와 동일하게 **사용자가 명시적으로 요청할 때만** 수행합니다 (Actions 자동 커밋은 예외).

### 🧩 서브에이전트(Sub-Agent) 매핑
이 프로젝트는 별도의 페르소나 팀이나 전용 `.claude/agents/*.md`를 두지 않는 단순 구조입니다. 데이터 검증(시세/보유 수량 정합성 확인)이나 다단계 리서치가 필요하면 `Agent` 도구의 `general-purpose` 타입을 사용하십시오.
