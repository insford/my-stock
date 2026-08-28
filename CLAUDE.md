@../AGENTS.md
@AGENTS.md

---

## 🔀 Claude Code ↔ antigravity-cli 동시 작업 브리지

이 프로젝트(`my-stock`)는 **antigravity-cli**(Gemini 기반, `GEMINI.md`/`AGENTS.md`/`invoke_subagent` 체계)와 **Claude Code** 두 CLI로 병행 작업됩니다. 위 두 줄의 `@import`가 두 도구가 공유하는 단일 원본(Single Source of Truth)을 이 파일에 그대로 불러옵니다.

> ⚠️ **내용을 이 파일에 복사/재작성하지 마세요.** KOSPI 박스권 리밸런싱 전략, 데이터 파일 스펙, 8대 투자 페르소나, 사내 8인 에이전트 팀 등 모든 실질 규칙은 [AGENTS.md](./AGENTS.md), [AGENT_TEAM_GUIDE.md](./AGENT_TEAM_GUIDE.md), [PERSONA.md](./PERSONA.md)에만 존재합니다. 수정이 필요하면 원본 문서를 고치세요 — 그래야 두 도구 세션이 동일한 내용을 즉시 참조합니다.

### 🗣️ 호칭 및 호출 모드
[AGENTS.md](./AGENTS.md) §0 규칙을 그대로 따릅니다:
* 사용자는 **Jake**로 호칭합니다.
* **"스톡맨, ~"** 형태의 단순 질의에는 총괄 Lead(강태석) 단독으로 즉시 답변합니다.
* **"팀원들과 검토해봐 / 상의해봐 / 협의해봐 / 시뮬레이션해봐"** 류의 지시에는 반드시 아래 병렬 협의 모드 매핑을 따라 개별 서브에이전트들을 병렬 소집하여 심층 검토 후 브리핑합니다.

### 👥 병렬 리뷰(팀원 협의) 모드 매핑

| 환경 (CLI) | 사내 8인 에이전트 및 8대 투자 페르소나 동작 방식 |
| :--- | :--- |
| **antigravity-cli** | • `invoke_subagent`로 [AGENT_TEAM_GUIDE.md](./AGENT_TEAM_GUIDE.md)에 등록된 고유 시스템 ID(`stock_lead_kang`, `stock_quant_song`, `stock_equity_jeong`, `stock_macro_ahn`, `stock_risk_yoon`, `stock_ux_lee`, `stock_fe_park`, `stock_data_han`)를 **독립된 개별 서브에이전트로 병렬 호출 (`Workspace: 'branch'`)**하여 검증 및 작업 수행. |
| **Claude Code** | • `Agent` 도구로 `general-purpose`를 병렬 호출하고, 프롬프트에 [AGENT_TEAM_GUIDE.md](./AGENT_TEAM_GUIDE.md)의 8인 전문 R&R 및 [PERSONA.md](./PERSONA.md)의 8대 투자 페르소나 검증 기준을 인용하여 개별 서브에이전트로 동작. |

두 도구 모두 **판단 기준은 반드시 `AGENTS.md` / `AGENT_TEAM_GUIDE.md` / `PERSONA.md` 원본을 그대로 인용**해야 하며, 임의로 수식이나 비중 밴드를 재해석하거나 완화하지 않습니다.

### ⚠️ 동시 작업 시 상태 충돌 방지 (중요)
* `guide/data/live_market.js`는 **30분 주기 GitHub Actions 워크플로(`monitor.yml`)가 자동으로 갱신·커밋·푸시**하는 파일입니다. 이 파일을 직접 편집하지 말고, 작업 시작 전 `git status` / `git log -3`으로 Actions 자동 커밋 또는 다른 세션의 미반영 변경사항이 있는지 먼저 확인한 뒤 `git pull`로 최신 상태를 받습니다.
* `guide/data/portfolio_state.js`(보유 수량), `guide/data/portfolio_state_history_2026.js`(거래 이력), `guide/매매일지.md`는 포트폴리오 변경 시 [AGENTS.md §7.1](./AGENTS.md#71-updating-holdings-after-trade-execution)의 **3단계 동기화 절차**를 반드시 동시에 지킵니다.
* Git 커밋/푸시는 [루트 AGENTS.md §5](../AGENTS.md#5-서브-프로젝트-작업-및-git-동기화-운영-원칙)와 동일하게 **Jake께서 명시적으로 요청할 때만** 수행합니다.
