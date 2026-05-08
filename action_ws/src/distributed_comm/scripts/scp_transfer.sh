#!/bin/bash
# ============================================================================
#  PC <-> Jetson Nano SCP 文件传输脚本
#  自动检测运行在 PC 还是 Jetson 上，调整方向
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/scp_config"

# 默认值
JETSON_IP="${JETSON_IP:-10.88.168.44}"
JETSON_USER="${JETSON_USER:-jetson}"
PC_IP="${PC_IP:-10.88.168.60}"
PC_USER="${PC_USER:-xq}"

[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

# 自动检测当前在哪台机器
HOSTNAME="$(hostname)"
if echo "$HOSTNAME" | grep -qi "nano\|jetson\|tegra"; then
    SIDE="jetson"
    REMOTE_IP="$PC_IP"
    REMOTE_USER="$PC_USER"
    LOCAL_WS="$HOME/Desktop/Jetson_Nano/action_ws"
    REMOTE_WS="/home/$PC_USER/nano_distribute"   # PC工作空间根目录, 已含src/
else
    SIDE="pc"
    REMOTE_IP="$JETSON_IP"
    REMOTE_USER="$JETSON_USER"
    LOCAL_WS="$HOME/nano_distribute"
    REMOTE_WS="/home/$JETSON_USER/Desktop/Jetson_Nano/action_ws"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo ""
    echo "Usage (auto-detected: $SIDE):"
    echo "  ./scp_transfer.sh push <本地文件>   [远程路径]"
    echo "  ./scp_transfer.sh pull <远程文件>   [本地路径]"
    echo "  ./scp_transfer.sh sync-distributed  同步 distributed_comm"
    echo "  ./scp_transfer.sh sync-ws           同步 action_ws/src"
    echo "  ./scp_transfer.sh config            修改 IP 配置"
    echo ""
    echo "Config:"
    echo "  Jetson:  $JETSON_USER@$JETSON_IP"
    echo "  PC:      $PC_USER@$PC_IP"
    echo "  Local:   $LOCAL_WS"
    echo "  Remote:  $REMOTE_WS"
    echo ""
}

scp_do() {
    local dir=$1 src=$2 dst=$3
    echo -e "${YELLOW}$src${NC}"
    echo -e "  -> ${GREEN}${REMOTE_USER}@${REMOTE_IP}:${dst}${NC}"
    scp -r "$src" "${REMOTE_USER}@${REMOTE_IP}:${dst}"
    echo -e "${GREEN}Done.${NC}"
}

scp_pull() {
    local src=$1 dst=$2
    echo -e "${YELLOW}${REMOTE_USER}@${REMOTE_IP}:${src}${NC}"
    echo -e "  -> ${GREEN}${dst}${NC}"
    scp -r "${REMOTE_USER}@${REMOTE_IP}:${src}" "$dst"
    echo -e "${GREEN}Done.${NC}"
}

do_sync() {
    local pkg="${1:?}"
    local local_src="$LOCAL_WS/src/$pkg"
    local remote_dst="$REMOTE_WS/src/"
    local remote_src="$REMOTE_WS/action_ws/src/$pkg"
    local local_dst="$LOCAL_WS/src/"

    # backup and rm pycache on both sides to avoid permission issues
    find "$local_src" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

    [ -d "$local_src" ] || { echo -e "${RED}[ERROR] Not found: $local_src${NC}"; exit 1; }

    mkdir -p "$(dirname "$local_dst/$pkg")"
    scp_do push "$local_src" "$remote_dst"
}


do_config() {
    echo ""
    echo "Which machine do you want to edit?"
    echo "  1) Jetson IP:  $JETSON_IP"
    echo "  2) Jetson User:$JETSON_USER"
    echo "  3) PC IP:      $PC_IP"
    echo "  4) PC User:    $PC_USER"
    echo ""
    read -p "Edit [1-4 / Enter=done]: " C

    local v
    case $C in
        1) read -p "Jetson IP: " v; [ -n "$v" ] && JETSON_IP="$v" ;;
        2) read -p "Jetson User: " v; [ -n "$v" ] && JETSON_USER="$v" ;;
        3) read -p "PC IP: " v; [ -n "$v" ] && PC_IP="$v" ;;
        4) read -p "PC User: " v; [ -n "$v" ] && PC_USER="$v" ;;
    esac

    cat > "$CONFIG_FILE" << EOF
JETSON_IP="$JETSON_IP"
JETSON_USER="$JETSON_USER"
PC_IP="$PC_IP"
PC_USER="$PC_USER"
EOF
    echo -e "${GREEN}Saved: $CONFIG_FILE${NC}"
}

case "${1:-}" in
    push)
        SRC="${2:?src missing}"
        DST="${3:-$REMOTE_WS/}"
        scp_do push "$SRC" "$DST"
        ;;
    pull)
        SRC="${2:?remote src missing}"
        DST="${3:-./}"
        scp_pull "$SRC" "$DST"
        ;;
    sync-distributed) do_sync distributed_comm ;;
    sync-ws)          do_sync "" ;;
    config)           do_config ;;
    *)                usage ;;
esac
