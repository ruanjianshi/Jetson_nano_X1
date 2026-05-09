#!/bin/bash
# ============================================================================
#  ROS 分布式网络切换脚本 — LAN / ZeroTier / Tailscale 一键切换
#  作者: Qi Xiao  邮箱: 2408128687@qq.com
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/net_config"

[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

GREEN='\033[0;32m' YELLOW='\033[1;33m' RED='\033[0;31m' BLUE='\033[0;34m' NC='\033[0m'

HOSTNAME="$(hostname)"
if echo "$HOSTNAME" | grep -qi "nano\|jetson\|tegra"; then
    SIDE="jetson"
    LAN_IP="${LAN_IP:-10.88.168.44}"
    ZT_IP="${ZT_IP:-10.9.225.7}"
    TS_IP="${TS_IP:-}"
else
    SIDE="pc"
    LAN_IP="${LAN_IP:-10.88.168.60}"
    ZT_IP="${ZT_IP:-10.9.225.55}"
    TS_IP="${TS_IP:-}"
    JETSON_LAN_IP="${JETSON_LAN_IP:-10.88.168.44}"
    JETSON_ZT_IP="${JETSON_ZT_IP:-10.9.225.7}"
    JETSON_TS_IP="${JETSON_TS_IP:-}"
fi

get_ts_ip() { tailscale ip -4 2>/dev/null || echo ""; }

do_config() {
    echo ""
    echo -e "Machine: ${BLUE}$SIDE${NC}"
    echo ""

    read -p "LAN IP       [$LAN_IP]: " v; [ -n "$v" ] && LAN_IP="$v"
    read -p "ZeroTier IP  [$ZT_IP]: "  v; [ -n "$v" ] && ZT_IP="$v"
    TS_IP=$(get_ts_ip)
    [ -n "$TS_IP" ] && echo "Tailscale IP: $TS_IP (auto-detected)"
    read -p "Tailscale IP [$TS_IP]: " v; [ -n "$v" ] && TS_IP="$v"

    if [ "$SIDE" = "pc" ]; then
        read -p "Jetson LAN IP       [$JETSON_LAN_IP]: " v; [ -n "$v" ] && JETSON_LAN_IP="$v"
        read -p "Jetson ZeroTier IP  [$JETSON_ZT_IP]: "  v; [ -n "$v" ] && JETSON_ZT_IP="$v"
        read -p "Jetson Tailscale IP [$JETSON_TS_IP]: "  v; [ -n "$v" ] && JETSON_TS_IP="$v"
        cat > "$CONFIG_FILE" << EOF
LAN_IP="$LAN_IP"
ZT_IP="$ZT_IP"
TS_IP="$TS_IP"
JETSON_LAN_IP="$JETSON_LAN_IP"
JETSON_ZT_IP="$JETSON_ZT_IP"
JETSON_TS_IP="$JETSON_TS_IP"
EOF
    else
        cat > "$CONFIG_FILE" << EOF
LAN_IP="$LAN_IP"
ZT_IP="$ZT_IP"
TS_IP="$TS_IP"
EOF
    fi
    echo -e "${GREEN}Config saved.${NC}"
}

do_switch() {
    local mode="${1:-}"
    local master my_ip label

    case "$mode" in
        lan)
            label="LAN"
            if [ "$SIDE" = "jetson" ]; then master="http://${LAN_IP}:11311"; my_ip="$LAN_IP"
            else master="http://${JETSON_LAN_IP}:11311"; my_ip="$LAN_IP"; fi ;;
        zt)
            label="ZeroTier"
            if [ "$SIDE" = "jetson" ]; then master="http://${ZT_IP}:11311"; my_ip="$ZT_IP"
            else master="http://${JETSON_ZT_IP}:11311"; my_ip="$ZT_IP"; fi ;;
        ts)
            label="Tailscale"
            if [ "$SIDE" = "jetson" ]; then master="http://${TS_IP}:11311"; my_ip="$TS_IP"
            else master="http://${JETSON_TS_IP}:11311"; my_ip="$TS_IP"; fi ;;
        *)
            echo -e "${RED}Usage: ./$(basename "$0") switch [lan|zt|ts]${NC}"; return 1 ;;
    esac

    sed -i '/^export ROS_MASTER_URI=/d; /^export ROS_IP=/d; /^export ROS_HOSTNAME=/d' ~/.bashrc
    cat >> ~/.bashrc << EOF
export ROS_MASTER_URI=$master
export ROS_IP=$my_ip
export ROS_HOSTNAME=$my_ip
EOF

    export ROS_MASTER_URI="$master" ROS_IP="$my_ip" ROS_HOSTNAME="$my_ip"

    echo -e "${GREEN}Switched to ${BLUE}$label${GREEN} mode${NC}"
    echo "  ROS_MASTER_URI=$ROS_MASTER_URI"
    echo "  ROS_IP=$ROS_IP"

    if [ "${BASH_SOURCE[0]}" != "$0" ]; then
        source ~/.bashrc
        echo -e "${GREEN}Current terminal updated.${NC}"
    else
        echo -e "${YELLOW}Run: source ~/.bashrc${NC}"
    fi
}

do_status() {
    echo ""
    echo -e "Machine: ${BLUE}$SIDE${NC}"
    echo ""

    if command -v tailscale &>/dev/null; then
        echo "Tailscale: $(tailscale ip -4 2>/dev/null || echo 'offline')"
    fi
    if command -v zerotier-cli &>/dev/null; then
        echo "ZeroTier : $(sudo zerotier-cli listnetworks 2>/dev/null | grep -oP '10\.\d+\.\d+\.\d+' | head -1 || echo 'offline')"
    fi
    echo ""
    echo "ROS config:"
    echo "  ROS_MASTER_URI=$ROS_MASTER_URI"
    echo "  ROS_IP=$ROS_IP"
    echo ""

    if echo "$ROS_MASTER_URI" | grep -qE "^http://100\."; then
        echo -e "Mode: ${BLUE}Tailscale${NC}"
    elif echo "$ROS_MASTER_URI" | grep -q "10\.9\.225"; then
        echo -e "Mode: ${BLUE}ZeroTier${NC}"
    else
        echo -e "Mode: ${GREEN}LAN 局域网${NC}"
    fi
}

do_test() {
    local tgt
    case "${1:-}" in
        lan) tgt="${JETSON_LAN_IP:-10.88.168.44}" ;;
        ts)  tgt="${JETSON_TS_IP:-}" ;;
        *)   echo "Usage: ./$(basename "$0") test [lan|ts|zt]"; return 1 ;;
    esac
    echo "Pinging $tgt ..."
    ping -c 3 "$tgt" && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAIL${NC}"
}

case "${1:-}" in
    config)  do_config ;;
    switch)  do_switch "${2:-}" ;;
    status)  do_status ;;
    test)    do_test "${2:-}" ;;
    *)
        echo ""
        echo "ROS Network Switch ($SIDE)"
        echo ""
        echo "  config           Configure IPs (LAN / ZT / TS)"
        echo "  switch lan       局域网"
        echo "  switch zt        ZeroTier"
        echo "  switch ts        Tailscale"
        echo "  status           Show current mode"
        echo "  test [lan|ts]    Ping Jetson"
        echo ""
        echo "Tip: source for auto-refresh:"
        echo "  . ./network_switch.sh switch ts"
        ;;
esac
