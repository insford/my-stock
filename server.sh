#!/usr/bin/env bash

# ==============================================================================
# my-stock Local Test Web Server Controller
# Usage: ./server.sh {start|stop|status|restart|logs}
# ==============================================================================

PORT=8000
PID_FILE=".server.pid"
LOG_FILE=".server.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

tail_log() {
    if [ ! -f "$LOG_FILE" ]; then
        touch "$LOG_FILE"
    fi
    echo ""
    echo "📋 실시간 로그 모니터링을 시작합니다 (종료: Ctrl+C | 서버는 백그라운드 유지)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # SIGINT (Ctrl+C) 수신 시 안내 메시지 출력 후 스크립트만 종료 (서버 프로세스는 계속 유지)
    trap 'echo -e "\n\n📌 실시간 로그 모니터링을 종료합니다. 로컬 웹서버는 백그라운드(PID: $(cat "$PID_FILE" 2>/dev/null))에서 계속 실행 중입니다.\n   (서버 종료: ./server.sh stop)"; exit 0' INT

    tail -f "$LOG_FILE"
}

start_server() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "⚠️  로컬 웹서버가 이미 실행 중입니다. (PID: $PID)"
        echo "🌐 접속 URL: http://localhost:$PORT"
        echo "📄 로그 파일: $LOG_FILE"
        tail_log
        return 0
    fi

    # 포트 충돌 여부 사전 확인
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ 포트 $PORT 번이 이미 다른 프로세스에 의해 사용 중입니다."
        echo "   'lsof -i :$PORT' 명령어로 점유 중인 프로세스를 확인해 주세요."
        return 1
    fi

    echo "🚀 로컬 웹서버를 시작합니다 (Port: $PORT)..."
    nohup python3 -m http.server "$PORT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "$PID" > "$PID_FILE"

    sleep 0.5
    if is_running; then
        echo "✅ 로컬 웹서버가 정상적으로 시작되었습니다! (PID: $PID)"
        echo "🌐 브라우저 접속 URL: http://localhost:$PORT"
        echo "📄 로그 파일: $LOG_FILE"
        
        # macOS의 경우 브라우저 자동 오픈
        if command -v open > /dev/null 2>&1; then
            open "http://localhost:$PORT"
        fi

        tail_log
    else
        echo "❌ 서버 시작에 실패했습니다. 로그를 확인해 주세요:"
        cat "$LOG_FILE"
        return 1
    fi
}

stop_server() {
    if ! is_running; then
        echo "ℹ️  실행 중인 로컬 웹서버가 없습니다."
        return 0
    fi

    PID=$(cat "$PID_FILE")
    echo "🛑 로컬 웹서버를 종료합니다 (PID: $PID)..."
    kill "$PID" 2>/dev/null
    
    # 2초간 종료 대기 후 강제 종료
    for _ in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 0.2
    done

    if ps -p "$PID" > /dev/null 2>&1; then
        kill -9 "$PID" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    echo "✅ 로컬 웹서버가 안전하게 종료되었습니다."
}

status_server() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "🟢 [RUNNING] 로컬 웹서버가 정상 실행 중입니다."
        echo "   • PID: $PID"
        echo "   • Port: $PORT"
        echo "   • URL: http://localhost:$PORT"
        echo "   • Log: $LOG_FILE"
    else
        echo "🔴 [STOPPED] 로컬 웹서버가 중지되어 있습니다."
    fi
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    status)
        status_server
        ;;
    restart)
        stop_server
        sleep 0.5
        start_server
        ;;
    logs|tail)
        tail_log
        ;;
    *)
        echo "📖 사용법: $0 {start|stop|status|restart|logs}"
        echo ""
        echo "  • start   : 로컬 웹서버 시작 + 브라우저 열기 + 실시간 로그 테일"
        echo "  • stop    : 실행 중인 로컬 웹서버 종료"
        echo "  • status  : 서버 실행 상태 및 PID 확인"
        echo "  • restart : 로컬 웹서버 재시작 + 실시간 로그 테일"
        echo "  • logs    : 실행 중인 서버의 실시간 로그 확인 (Ctrl+C로 종료 가능)"
        exit 1
        ;;
esac
