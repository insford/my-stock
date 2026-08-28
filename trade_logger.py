#!/usr/bin/env python3
"""
trade_logger.py - 국내주식 스마트 포트폴리오 매매 기록 CLI 도구

사용법:
  1. 대화형 인터랙티브 모드:
     python trade_logger.py -i
     python trade_logger.py --interactive

  2. 매수/매도 명령어:
     python trade_logger.py buy samsung 20 260500 --deposit 30622238 --note "밴드 하단 추가 매수"
     python trade_logger.py sell hynix 5 1700000 --deposit 44332238 --note "차익 실현"

  3. 예수금 입출금:
     python trade_logger.py deposit 10000000 --note "자금 추가 입금"
     python trade_logger.py withdraw 5000000 --note "생활비 출금"

  4. 현황 및 이력 조회:
     python trade_logger.py --status
     python trade_logger.py --history

  5. 깃 자동 커밋/푸시 옵션:
     --commit, --push 플래그 추가
"""

import os
import sys
import json
import sqlite3
import argparse
import datetime
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "guide", "data", "market_history.db")
PORTFOLIO_STATE_PATH = os.path.join(CURRENT_DIR, "guide", "data", "portfolio_state.js")
PORTFOLIO_HIST_PATH = os.path.join(CURRENT_DIR, "guide", "data", "portfolio_state_history_2026.js")
TRADE_LOG_MD_PATH = os.path.join(CURRENT_DIR, "guide", "매매일지.md")

ASSET_NAMES = {
    'samsung': '삼성전자',
    'hynix': 'SK하이닉스',
    'cd': 'KODEX CD금리액티브',
    'sofr': 'TIGER 미국달러SOFR금리액티브',
    'us30b': 'ACE 미국30년국채액티브(H)',
    'gold': 'ACE KRX금현물',
    'snp500': 'TIGER 미국S&P500',
    'us10b': 'KODEX 미국채10년액티브 (구)',
    'fadu': '파두'
}


def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run migrate_to_sqlite.py first.")
    conn = sqlite3.connect(DB_PATH)
    return conn


def get_latest_market_prices(conn):
    """DB에서 각 자산의 최신 종가 및 코스피 지수를 조회"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code, price FROM market_history
        WHERE (code, date) IN (
            SELECT code, MAX(date) FROM market_history GROUP BY code
        )
    """)
    prices = {row[0]: row[1] for row in cursor.fetchall()}
    return prices


def get_current_account_state(conn):
    """현재 계좌 상태 및 보유 수량 조회"""
    cursor = conn.cursor()
    cursor.execute("SELECT account_id, account_name, deposit_krw, min_trigger_gap, kospi_min_level, kospi_max_level, updated_at FROM account_state WHERE account_id = 'main'")
    acc = cursor.fetchone()
    if not acc:
        raise ValueError("account_state 'main' not found.")

    account = {
        'account_id': acc[0],
        'account_name': acc[1],
        'deposit_krw': acc[2],
        'min_trigger_gap': acc[3],
        'kospi_min_level': acc[4],
        'kospi_max_level': acc[5],
        'updated_at': acc[6]
    }

    cursor.execute("SELECT code, shares, target_ratio, updated_at FROM account_holdings")
    holdings = {row[0]: row[1] for row in cursor.fetchall()}

    return account, holdings


def print_status():
    """현재 포트폴리오 현황을 터미널에 깔끔하게 출력"""
    conn = get_db_connection()
    account, holdings = get_current_account_state(conn)
    prices = get_latest_market_prices(conn)

    print("\n=======================================================")
    print(f"📊 [{account['account_name']}] 포트폴리오 현황")
    print(f"🕒 최종 갱신일: {account['updated_at']}")
    print("=======================================================")

    semi_val = 0
    other_val = 0
    total_val = account['deposit_krw']

    print(f"\n[반도체 코어 자산]")
    for code in ['samsung', 'hynix']:
        shares = holdings.get(code, 0)
        price = prices.get(code, 0)
        val = int(shares * price)
        semi_val += val
        name = ASSET_NAMES.get(code, code)
        print(f"  • {name:<12}: {shares:>5} 주 | 현재가 {price:>10,f} 원 | 평가액 {val:>13,} 원")

    print(f"\n[기타 헤지 및 안전 자산]")
    for code in ['snp500', 'gold', 'us30b', 'sofr', 'cd', 'us10b', 'fadu']:
        shares = holdings.get(code, 0)
        if shares == 0 and code in ('us10b', 'fadu'):
            continue
        price = prices.get(code, 0)
        val = int(shares * price)
        other_val += val
        name = ASSET_NAMES.get(code, code)
        print(f"  • {name:<26}: {shares:>5} 주 | 현재가 {price:>10,f} 원 | 평가액 {val:>13,} 원")

    print(f"\n[현금 및 예수금]")
    print(f"  • 예수금 (KRW)                 : {account['deposit_krw']:>13,} 원")

    total_val += semi_val + other_val
    semi_ratio = (semi_val / total_val * 100) if total_val > 0 else 0
    kospi = prices.get('kospi', 0)

    # 목표 비중 계산
    if kospi >= 8500:
        target_ratio, lvl = 32.5, "L6"
    elif kospi >= 8000:
        target_ratio, lvl = 40.0, "L5"
    elif kospi >= 7500:
        target_ratio, lvl = 47.5, "L4"
    elif kospi >= 7000:
        target_ratio, lvl = 55.0, "L3"
    elif kospi >= 6500:
        target_ratio, lvl = 62.5, "L2"
    elif kospi >= 6000:
        target_ratio, lvl = 70.0, "L1"
    else:
        target_ratio, lvl = 77.5, "L0"

    gap = semi_ratio - target_ratio
    status_str = "🚨 리밸런싱 필요" if abs(gap) >= account['min_trigger_gap'] else "🟢 정상 범위 유지"

    print("\n-------------------------------------------------------")
    print(f"💰 총 평가 자산 : {total_val:>13,} 원 (약 {total_val / 100000000:.2f} 억 원)")
    print(f"📈 코스피 지수   : {kospi:,.2f} pt ({lvl} 구간)")
    print(f"⚖️ 반도체 비중  : {semi_ratio:.2f}% (목표: {target_ratio:.1f}%, 격차: {gap:+.2f}%p ➔ {status_str})")
    print("=======================================================\n")
    conn.close()


def print_history(limit=10):
    """최근 매매 이력 조회"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trade_id, trade_date, trade_type, note, samsung_shares, hynix_shares, deposit_krw, total_eval_krw
        FROM trade_history
        ORDER BY trade_date DESC, trade_id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    print(f"\n📜 최근 매매 이력 (최근 {len(rows)}건)")
    print("-" * 80)
    for r in rows:
        tid, tdate, ttype, note, sam, hyn, dep, tot = r
        print(f"[{tdate}] #{tid} {ttype:<9} | 삼전: {sam:>3}주 | 하닉: {hyn:>3}주 | 예수금: {dep:>11,}원 | 총자산: {tot/100000000:.2f}억")
        if note:
            print(f"  ➔ 사유: {note}")
    print("-" * 80 + "\n")


def execute_trade_record(trade_date, trade_type, note, changes, new_deposit=None, prices_override=None, commit_git=False, push_git=False):
    """
    매매 내역을 DB 및 동기화 파일들에 반영합니다.
    changes: dict of { 'code': delta_shares } e.g. {'samsung': 20, 'hynix': -5}
             또는 절대 수량 딕셔너리
    """
    conn = get_db_connection()
    account, holdings = get_current_account_state(conn)
    prices = get_latest_market_prices(conn)
    if prices_override:
        prices.update(prices_override)

    # 1. 새 보유 수량 및 예수금 계산
    new_holdings = dict(holdings)
    total_trade_amount = 0

    for code, delta in changes.items():
        if code not in new_holdings:
            new_holdings[code] = 0
        new_holdings[code] += delta
        if new_holdings[code] < 0:
            raise ValueError(f"보유 수량이 음수가 될 수 없습니다: {code} = {new_holdings[code]}")
        price = prices.get(code, 0)
        total_trade_amount += delta * price

    if new_deposit is not None:
        final_deposit = int(new_deposit)
    else:
        # 매수(delta > 0)면 예수금 감소, 매도(delta < 0)면 예수금 증가
        final_deposit = int(account['deposit_krw'] - total_trade_amount)

    if final_deposit < 0:
        print(f"⚠️ 경고: 예수금이 음수({final_deposit:,}원)가 됩니다. 필요 시 --deposit 인자로 정확한 잔액을 지정하세요.")

    # 2. 총 평가액 계산
    semi_tot = (new_holdings.get('samsung', 0) * prices.get('samsung', 0) +
                new_holdings.get('hynix', 0) * prices.get('hynix', 0))
    other_stock_tot = sum(new_holdings.get(c, 0) * prices.get(c, 0) for c in new_holdings if c not in ('samsung', 'hynix'))
    total_eval = int(semi_tot + other_stock_tot + final_deposit)

    # 3. DB 업데이트 (안전 트랜잭션)
    kst_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kospi_pt = prices.get('kospi', 0.0)
    raw_snapshot = {
        "date": trade_date,
        "note": note,
        "prices": prices,
        "holdings": {
            "samsung_shares": new_holdings.get('samsung', 0),
            "hynix_shares": new_holdings.get('hynix', 0),
            "deposit_krw": final_deposit,
            "other_assets_krw": int(other_stock_tot)
        },
        "other_assets_detail": {
            "kodex_cd_shares": new_holdings.get('cd', 0),
            "tiger_sofr_shares": new_holdings.get('sofr', 0),
            "ace_us30b_shares": new_holdings.get('us30b', 0),
            "ace_gold_shares": new_holdings.get('gold', 0),
            "tiger_snp500_shares": new_holdings.get('snp500', 0),
            "kodex_gold_shares": 0,
            "kodex_us10b_shares": new_holdings.get('us10b', 0),
            "kodex_snp500_shares": 0,
            "fadu_shares": new_holdings.get('fadu', 0)
        }
    }

    try:
        with conn:
            cursor = conn.cursor()
            # account_state
            cursor.execute("""
                UPDATE account_state
                SET deposit_krw = ?, updated_at = ?
                WHERE account_id = 'main'
            """, (final_deposit, trade_date))

            # account_holdings
            for code, shares in new_holdings.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO account_holdings (code, shares, target_ratio, updated_at)
                    VALUES (?, ?, 0.0, ?)
                """, (code, shares, trade_date))

            # trade_history insert
            cursor.execute("""
                INSERT INTO trade_history (
                    trade_date, trade_type, note, kospi_point,
                    samsung_shares, hynix_shares, cd_shares, sofr_shares,
                    us30b_shares, gold_shares, snp500_shares, us10b_shares,
                    fadu_shares, deposit_krw, total_eval_krw, raw_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_date, trade_type, note, kospi_pt,
                new_holdings.get('samsung', 0), new_holdings.get('hynix', 0),
                new_holdings.get('cd', 0), new_holdings.get('sofr', 0),
                new_holdings.get('us30b', 0), new_holdings.get('gold', 0),
                new_holdings.get('snp500', 0), new_holdings.get('us10b', 0),
                new_holdings.get('fadu', 0), final_deposit, total_eval,
                json.dumps(raw_snapshot, ensure_ascii=False), kst_now
            ))

            cursor.execute(f"PRAGMA user_version = {int(datetime.datetime.now().timestamp())}")

            # 4. 하위 호환용 JS 파일 및 매매일지.md 동기화 (트랜잭션 내부에서 검증)
            sync_legacy_files(trade_date, trade_type, note, new_holdings, final_deposit, int(other_stock_tot), raw_snapshot, changes, prices, conn=conn)
    except Exception as e:
        print(f"❌ [트랜잭션 롤백] 매매 기록 및 파일 동기화 중 오류 발생: {e}")
        conn.close()
        raise
    finally:
        conn.close()

    print(f"\n[+] SQLite DB 및 레거시 파일 동기화 완료 (거래일: {trade_date}, 유형: {trade_type})")

    # 5. Git commit & push (옵션)
    if commit_git or push_git:
        git_sync(trade_date, trade_type, note, push=push_git)

    print("\n✅ 매매 기록 및 파일 동기화가 성공적으로 완료되었습니다!")
    print_status()


def atomic_write_file(filepath, content):
    """임시 파일 생성 후 Atomic Replace를 통해 파일 손상 방지"""
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, filepath)


def sync_legacy_files(trade_date, trade_type, note, holdings, deposit_krw, other_assets_krw, raw_snapshot, changes, prices, conn=None):
    """하위 호환성을 위해 portfolio_state.js, portfolio_state_history_2026.js 및 매매일지.md 갱신"""
    # 1. portfolio_state.js 갱신
    state_obj = {
        "last_updated": trade_date,
        "account_name": "국내주식 종합_주식 리밸런싱",
        "holdings": {
            "samsung_shares": holdings.get('samsung', 0),
            "hynix_shares": holdings.get('hynix', 0),
            "deposit_krw": deposit_krw,
            "other_assets_krw": other_assets_krw
        },
        "other_assets_detail": {
            "kodex_cd_shares": holdings.get('cd', 0),
            "tiger_sofr_shares": holdings.get('sofr', 0),
            "ace_us30b_shares": holdings.get('us30b', 0),
            "ace_gold_shares": holdings.get('gold', 0),
            "tiger_snp500_shares": holdings.get('snp500', 0),
            "kodex_gold_shares": 0,
            "kodex_us10b_shares": holdings.get('us10b', 0),
            "kodex_snp500_shares": 0,
            "fadu_shares": holdings.get('fadu', 0)
        },
        "strategy_config": {
            "min_trigger_gap_percent": 8.0,
            "kospi_min_level": 6000,
            "kospi_max_level": 8500
        }
    }
    atomic_write_file(PORTFOLIO_STATE_PATH, "window.PORTFOLIO_STATE_DATA = " + json.dumps(state_obj, indent=2, ensure_ascii=False) + ";\n")
    print(f"[+] Synced {os.path.basename(PORTFOLIO_STATE_PATH)}")

    # 2. portfolio_state_history_2026.js 갱신 (전체 이력 로드 후 재작성)
    own_conn = False
    if conn is None:
        conn = get_db_connection()
        own_conn = True
    cursor = conn.cursor()
    cursor.execute("SELECT raw_json FROM trade_history ORDER BY trade_date ASC, trade_id ASC")
    all_hist = []
    for r in cursor.fetchall():
        if r[0]:
            try:
                all_hist.append(json.loads(r[0]))
            except Exception:
                pass
    if own_conn:
        conn.close()

    atomic_write_file(PORTFOLIO_HIST_PATH, "window.PORTFOLIO_STATE_HISTORY_2026 = " + json.dumps(all_hist, indent=2, ensure_ascii=False) + ";\n")
    print(f"[+] Synced {os.path.basename(PORTFOLIO_HIST_PATH)}")

    # 3. 매매일지.md 갱신 (섹션 추가)
    if os.path.exists(TRADE_LOG_MD_PATH):
        trade_lines = []
        for code, delta in changes.items():
            name = ASSET_NAMES.get(code, code)
            action = "매수" if delta > 0 else "매도"
            trade_lines.append(f"  * [{action}] {name} {abs(delta):,}주")

        trade_action_desc = "\n".join(trade_lines) if trade_lines else "  * 예수금/자산 변동"
        kospi_val = prices.get('kospi', 0)

        md_section = f"""
---

### [{trade_date}] {note} ({trade_type} 집행)
* **매매 사유**: {note}
* **당시 코스피**: {kospi_val:,.2f} pt
* **매매 내역**:
{trade_action_desc}
* **매매 후 잔고 상태**:
  * 삼성전자: **{holdings.get('samsung', 0):,} 주**
  * SK하이닉스: **{holdings.get('hynix', 0):,} 주**
  * TIGER 미국S&P500: **{holdings.get('snp500', 0):,} 주**
  * ACE KRX금현물: **{holdings.get('gold', 0):,} 주**
  * ACE 미국30년국채액티브(H): **{holdings.get('us30b', 0):,} 주**
  * TIGER 미국달러SOFR: **{holdings.get('sofr', 0):,} 주**
  * KODEX CD금리액티브: **{holdings.get('cd', 0):,} 주**
  * 예수금 (원화 현금): **{deposit_krw:,} 원**
* **작업 사항**: SQLite DB(`guide/data/market_history.db`) 및 상태 파일 동기화 완료
"""
        with open(TRADE_LOG_MD_PATH, "a", encoding="utf-8") as f:
            f.write(md_section)
        print(f"[+] Appended trade log to {os.path.basename(TRADE_LOG_MD_PATH)}")


def git_sync(trade_date, trade_type, note, push=False):
    """Git commit 및 push 실행"""
    try:
        msg = f"Record trade [{trade_date}] {trade_type}: {note}"
        subprocess.run(["git", "add", "guide/data/", "guide/매매일지.md"], check=True, cwd=CURRENT_DIR)
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=CURRENT_DIR)
        print(f"[+] Git committed: {msg}")
        if push:
            subprocess.run(["git", "push"], check=True, cwd=CURRENT_DIR)
            print("[+] Git pushed successfully.")
    except Exception as e:
        print(f"⚠️ Git 작업 중 오류 발생: {e}")


def interactive_wizard():
    """대화형 CLI 마법사"""
    print("\n=======================================================")
    print("🧙 [my-stock] 대화형 매매 기록 마법사")
    print("=======================================================")
    print_status()

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    date_input = input(f"📅 매매 일자 입력 (기본값: {today_str}): ").strip()
    trade_date = date_input if date_input else today_str

    print("\n선택 가능한 거래 유형:")
    print("  1. BUY (매수)")
    print("  2. SELL (매도)")
    print("  3. REBALANCE (리밸런싱 다중 매매)")
    print("  4. DEPOSIT (예수금 입금)")
    print("  5. WITHDRAW (예수금 출금)")
    choice = input("👉 번호 선택 (1-5, 기본값: 1): ").strip() or "1"

    type_map = {"1": "BUY", "2": "SELL", "3": "REBALANCE", "4": "DEPOSIT", "5": "WITHDRAW"}
    trade_type = type_map.get(choice, "BUY")

    changes = {}
    prices_override = {}
    conn = get_db_connection()
    account, holdings = get_current_account_state(conn)
    prices = get_latest_market_prices(conn)
    conn.close()

    if trade_type in ("BUY", "SELL"):
        print("\n종목 코드 목록:")
        for idx, (k, name) in enumerate(ASSET_NAMES.items(), 1):
            cur_s = holdings.get(k, 0)
            cur_p = prices.get(k, 0)
            print(f"  {idx}. {k:<8} ({name}) - 현재 보유: {cur_s}주, 시세: {cur_p:,.0f}원")

        code_input = input("👉 대상 종목 코드 또는 번호 입력 (예: samsung 또는 1): ").strip().lower()
        # 번호 입력 시 매핑
        if code_input.isdigit() and 1 <= int(code_input) <= len(ASSET_NAMES):
            code = list(ASSET_NAMES.keys())[int(code_input) - 1]
        else:
            code = code_input

        if code not in ASSET_NAMES:
            print(f"❌ 올바르지 않은 종목 코드입니다: {code}")
            return

        shares_str = input(f"👉 {'매수' if trade_type == 'BUY' else '매도'} 수량 입력: ").strip()
        shares = int(shares_str)
        delta = shares if trade_type == "BUY" else -shares
        changes[code] = delta

        price_input = input(f"👉 체결 단가 입력 (기본 시세 {cur_p:,.0f}원, 엔터 시 자동): ").strip()
        if price_input:
            prices_override[code] = float(price_input.replace(',', ''))

    elif trade_type == "REBALANCE":
        print("\n각 종목별 변동 수량을 입력하세요 (매수: 양수, 매도: 음수, 변동없음: Enter)")
        for k, name in ASSET_NAMES.items():
            if k in ('us10b', 'fadu') and holdings.get(k, 0) == 0:
                continue
            delta_str = input(f"  • {name} ({k}, 현재 {holdings.get(k, 0)}주) 변동 수량: ").strip()
            if delta_str:
                changes[k] = int(delta_str)

    deposit_str = input(f"\n💵 매매 후 최종 예수금(KRW) 입력 (현재: {account['deposit_krw']:,}원, 자동계산: Enter): ").strip()
    new_deposit = int(deposit_str.replace(',', '')) if deposit_str else None

    note = input("📝 매매 사유 및 메모 입력: ").strip()
    if not note:
        note = f"{trade_type} 매매 집행"

    git_ans = input("\n🚀 Git Commit 및 Push를 함께 진행할까요? (y/N): ").strip().lower()
    push_git = git_ans in ('y', 'yes')

    print("\n--- 입력 내용 확인 ---")
    print(f"일자: {trade_date} | 유형: {trade_type}")
    print(f"변동 수량: {changes}")
    print(f"사유: {note}")
    if new_deposit is not None:
        print(f"지정 예수금: {new_deposit:,}원")

    confirm = input("위 내용으로 기록을 진행할까요? (Y/n): ").strip().lower()
    if confirm in ('n', 'no'):
        print("❌ 취소되었습니다.")
        return

    execute_trade_record(trade_date, trade_type, note, changes, new_deposit=new_deposit, prices_override=prices_override, push_git=push_git, commit_git=push_git)


def main():
    parser = argparse.ArgumentParser(description="my-stock 매매 기록 CLI 도구")
    parser.add_argument("action", nargs="?", choices=["buy", "sell", "rebalance", "deposit", "withdraw"], help="거래 액션")
    parser.add_argument("code", nargs="?", help="종목 코드 (samsung, hynix, cd 등) 또는 입출금 금액")
    parser.add_argument("shares", nargs="?", type=int, help="거래 수량 또는 입출금 금액")
    parser.add_argument("price", nargs="?", type=float, help="체결 단가 (생략 시 최신 DB 시세 사용)")
    parser.add_argument("-i", "--interactive", action="store_true", help="대화형 마법사 실행")
    parser.add_argument("-s", "--status", action="store_true", help="현재 포트폴리오 현황 출력")
    parser.add_argument("-H", "--history", action="store_true", help="매매 이력 출력")
    parser.add_argument("-d", "--date", help="거래 일자 (YYYY-MM-DD, 기본값: 오늘)")
    parser.add_argument("-n", "--note", help="매매 사유 및 비고")
    parser.add_argument("--deposit", type=int, help="매매 후 최종 예수금 (KRW)")
    parser.add_argument("--commit", action="store_true", help="기록 후 Git commit 자동 실행")
    parser.add_argument("--push", action="store_true", help="기록 후 Git commit & push 자동 실행")

    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if args.history:
        print_history()
        return

    if args.interactive or not args.action:
        interactive_wizard()
        return

    trade_date = args.date or datetime.date.today().strftime("%Y-%m-%d")
    note = args.note or f"{args.action.upper()} 매매 집행"
    changes = {}
    prices_override = {}

    if args.action in ("buy", "sell"):
        if not args.code or args.shares is None:
            print("❌ 오류: buy/sell 액션에는 종목코드와 수량이 필수입니다. (예: python trade_logger.py buy samsung 20)")
            sys.exit(1)
        code = args.code.lower()
        if code not in ASSET_NAMES:
            print(f"❌ 오류: 지원하지 않는 종목 코드입니다 ({code}). 지원 코드: {list(ASSET_NAMES.keys())}")
            sys.exit(1)
        delta = args.shares if args.action == "buy" else -args.shares
        changes[code] = delta
        if args.price is not None:
            prices_override[code] = args.price

    elif args.action in ("deposit", "withdraw"):
        # 예수금 직접 입출금 인자 파싱 (shares 또는 code 위치에 금액 입력 지원)
        raw_amount = args.shares if args.shares is not None else (int(args.code) if args.code and args.code.isdigit() else None)
        if raw_amount is None:
            print("❌ 오류: 금액을 지정해 주세요. (예: python trade_logger.py deposit 10000000)")
            sys.exit(1)
        amount = raw_amount
        conn = get_db_connection()
        account, _ = get_current_account_state(conn)
        conn.close()
        new_dep = account['deposit_krw'] + amount if args.action == "deposit" else account['deposit_krw'] - amount
        execute_trade_record(trade_date, args.action.upper(), note, {}, new_deposit=new_dep, commit_git=args.commit, push_git=args.push)
        return

    execute_trade_record(
        trade_date, args.action.upper(), note, changes,
        new_deposit=args.deposit, prices_override=prices_override,
        commit_git=args.commit, push_git=args.push
    )


if __name__ == "__main__":
    main()
