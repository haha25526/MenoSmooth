#!/bin/bash
# MenoSmooth 服务启动脚本
set -e

LOG_DIR="/root/MenoSmooth/logs"
mkdir -p "$LOG_DIR"

SERVICES=(
    "meno-backend:8004:/root/MenoSmooth/backend:app.main:app"
)

is_running() {
    local port=$1
    ss -tlnp 2>/dev/null | grep -q ":${port} " && return 0 || return 1
}

get_pid() {
    local port=$1
    ss -tlnp 2>/dev/null | grep ":${port} " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1
}

start_service() {
    local name=$1 port=$2 dir=$3 module=$4
    if is_running $port; then
        echo "✓ $name (port $port) already running"
        return 0
    fi
    echo "Starting $name (port $port)..."
    cd "$dir"
    local today=$(date +%Y-%m-%d)
    nohup python3 -m uvicorn $module --host 0.0.0.0 --port $port >> "$LOG_DIR/${name}-${today}.log" 2>&1 &
    sleep 2
    if is_running $port; then echo "✓ $name started"; else echo "✗ $name failed"; fi
}

stop_service() {
    local name=$1 port=$2
    if ! is_running $port; then echo "○ $name not running"; return 0; fi
    local pid=$(get_pid $port)
    echo "Stopping $name (PID: $pid)..."
    kill $pid 2>/dev/null || true
    sleep 1
}

case "${1:-start}" in
    start)
        for svc in "${SERVICES[@]}"; do
            IFS=':' read -r name port dir module <<< "$svc"
            start_service "$name" "$port" "$dir" "$module"
        done
        ;;
    stop)
        for svc in "${SERVICES[@]}"; do
            IFS=':' read -r name port dir module <<< "$svc"
            stop_service "$name" "$port"
        done
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    status)
        for svc in "${SERVICES[@]}"; do
            IFS=':' read -r name port dir module <<< "$svc"
            if is_running $port; then
                echo "✓ $name (port $port) running, PID: $(get_pid $port)"
            else
                echo "○ $name (port $port) not running"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        ;;
esac
