"""
해외 자산변화그래프(usHistoryChart) 데이터 소스인
guide/data/portfolio_state_us.js 의 `history` 배열을 market_history.db 의
일별 종가로 채워 넣는 자동화 스크립트.

동작 방식:
  1. portfolio_state_us.js 의 마지막 history 날짜 이후로,
     보유 중인 모든 종목(holdings) + usdkrw 가 공통으로 존재하는
     market_history.db 의 거래일만 골라 breakdown을 계산한다.
  2. 계산에는 portfolio_state_us.js 에 기록된 "현재" holdings/shares 와
     deposit_usd 를 그대로 사용한다 — 즉 매매(trade_history 갱신)가 있었다면
     해당 매매 반영 이후 시점부터 이 스크립트를 실행해야 정확하다.
  3. 새 항목은 is_trade=false, note="일별 종가 반영 (환율: N원)" 로 추가된다.

GitHub Actions monitor.yml 에서 update_history.py --update 이후 실행되어
guide/data/portfolio_state_us.js 를 자동 커밋 대상에 포함시키는 용도로 사용한다.
"""
import json
import os
import sqlite3
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
US_STATE_PATH = os.path.join(CURRENT_DIR, "guide", "data", "portfolio_state_us.js")
DB_PATH = os.path.join(CURRENT_DIR, "guide", "data", "market_history.db")

PREFIX = "window.PORTFOLIO_STATE_US_DATA = "


def load_state():
    with open(US_STATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    body = content[len(PREFIX):].rstrip().rstrip(";").rstrip()
    return json.loads(body)


def save_state(data):
    out = PREFIX + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    with open(US_STATE_PATH, "w", encoding="utf-8") as f:
        f.write(out)


def main():
    data = load_state()
    history = data.get("history", [])
    if not history:
        print("history 배열이 비어 있습니다. 초기 데이터가 필요합니다.")
        return

    last_date = history[-1]["date"]
    holdings = {h["price_key"]: h["shares"] for h in data["holdings"]}
    deposit_usd = data["deposit_usd"]
    tickers = list(holdings.keys())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    date_sets = []
    for t in tickers:
        c.execute(
            "SELECT date FROM market_history WHERE code=? AND date > ? ORDER BY date",
            (t, last_date),
        )
        date_sets.append({r[0] for r in c.fetchall()})
    common_dates = sorted(set.intersection(*date_sets)) if date_sets else []

    if not common_dates:
        print(f"추가할 새 거래일이 없습니다 (마지막 기록일: {last_date}).")
        conn.close()
        return

    new_entries = []
    for d in common_dates:
        breakdown = {}
        for t in tickers:
            c.execute("SELECT price FROM market_history WHERE code=? AND date=?", (t, d))
            row = c.fetchone()
            if row is None:
                breakdown = None
                break
            breakdown[t] = round(holdings[t] * row[0], 2)
        if breakdown is None:
            print(f"[SKIP] {d}: 일부 종목 시세 누락")
            continue

        c.execute("SELECT price FROM market_history WHERE code='usdkrw' AND date=?", (d,))
        fx_row = c.fetchone()
        if fx_row is None:
            print(f"[SKIP] {d}: 환율(usdkrw) 데이터 누락")
            continue
        fx = fx_row[0]

        breakdown["deposit"] = deposit_usd
        total_usd = round(sum(breakdown.values()), 2)
        total_krw = round(total_usd * fx)

        new_entries.append({
            "date": d,
            "total_usd": total_usd,
            "fx_rate": fx,
            "total_krw": total_krw,
            "is_trade": False,
            "note": f"일별 종가 반영 (환율: {fx:.1f}원)",
            "breakdown": breakdown,
        })

    conn.close()

    if not new_entries:
        print("추가된 항목이 없습니다.")
        return

    data["history"].extend(new_entries)
    data["last_updated"] = new_entries[-1]["date"]
    save_state(data)

    print(f"[OK] {len(new_entries)}개 항목 추가됨: {new_entries[0]['date']} ~ {new_entries[-1]['date']}")


if __name__ == "__main__":
    sys.exit(main())
