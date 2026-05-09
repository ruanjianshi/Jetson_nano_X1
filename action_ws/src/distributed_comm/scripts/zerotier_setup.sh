#!/bin/bash
# ============================================================================
#  ROS 分布式网络切换脚本 — 局域网 / ZeroTier 内网穿透 一键切换
#  作者: Qi Xiao  邮箱: 2408128687@qq.com
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/zt_config"
ZT_NETWORK_ID="f3797ba7a828a818"

[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

HOSTNAME="$(hostname)"
if echo "$HOSTNAME" | grep -qi "nano\|jetson\|tegra"; then
    SIDE="jetson"
    LAN_IP="${LAN_IP:-10.88.168.44}"
    ZT_IP="${ZT_IP:-10.9.225.7}"
else
    SIDE="pc"
    LAN_IP="${LAN_IP:-10.88.168.60}"
    ZT_IP="${ZT_IP:-10.9.225.55}"
    JETSON_ZT_IP="${JETSON_ZT_IP:-10.9.225.7}"
    JETSON_LAN_IP="${JETSON_LAN_IP:-10.88.168.44}"
fi

get_zt_ip() {
    sudo zerotier-cli listnetworks 2>/dev/null \
        | awk -v nid="$ZT_NETWORK_ID" '$0 ~ nid {split($NF,a,"/"); print a[1]}'
}

do_config() {
    echo ""
    echo -e "Machine: ${BLUE}$SIDE${NC}"
    echo "  LAN IP: $LAN_IP"
    echo "  ZT  IP: $ZT_IP ($(get_zt_ip 2>/dev/null || echo 'offline'))"
    echo ""

    read -p "LAN IP [$LAN_IP]: " v; [ -n "$v" ] && LAN_IP="$v"
    read -p "ZT  IP [$ZT_IP]: "  v; [ -n "$v" ] && ZT_IP="$v"

    if [ "$SIDE" = "pc" ]; then
        read -p "Jetson LAN IP [$JETSON_LAN_IP]: " v; [ -n "$v" ] && JETSON_LAN_IP="$v"
        read -p "Jetson ZT  IP [$JETSON_ZT_IP]: "  v; [ -n "$v" ] && JETSON_ZT_IP="$v"
        cat > "$CONFIG_FILE" << EOF
LAN_IP="$LAN_IP"
ZT_IP="$ZT_IP"
JETSON_LAN_IP="$JETSON_LAN_IP"
JETSON_ZT_IP="$JETSON_ZT_IP"
EOF
    else
        cat > "$CONFIG_FILE" << EOF
LAN_IP="$LAN_IP"
ZT_IP="$ZT_IP"
EOF
    fi

    echo -e "${GREEN}Config saved.${NC}"
    echo ""
    echo "Next: ./$(basename "$0") switch lan    or    ./$(basename "$0") switch zt"
}

do_switch() {
    local mode="${1:-}"

    echo ""
    if [ "$mode" = "lan" ]; then
        if [ "$SIDE" = "jetson" ]; then
            MASTER="http://${LAN_IP}:11311"
            MY_IP="$LAN_IP"
        else
            MASTER="http://${JETSON_LAN_IP}:11311"
            MY_IP="$LAN_IP"
        fi
    elif [ "$mode" = "zt" ]; then
        if [ "$SIDE" = "jetson" ]; then
            MASTER="http://${ZT_IP}:11311"
            MY_IP="$ZT_IP"
        else
            MASTER="http://${JETSON_ZT_IP}:11311"
            MY_IP="$ZT_IP"
        fi
    else
        echo -e "${RED}Usage: ./$(basename "$0") switch [lan|zt]${NC}"
        return 1
    fi

    # 删除 ~/.bashrc 中旧的 ROS 网络配置行
    sed -i '/^export ROS_MASTER_URI=/d; /^export ROS_IP=/d; /^export ROS_HOSTNAME=/d' ~/.bashrc

    # 追加新的配置到末尾
    cat >> ~/.bashrc << EOF
export ROS_MASTER_URI=$MASTER
export ROS_IP=$MY_IP
export ROS_HOSTNAME=$MY_IP
EOF

    # 立即生效当前终端
    export ROS_MASTER_URI="$MASTER"
    export ROS_IP="$MY_IP"
    export ROS_HOSTNAME="$MY_IP"

    echo -e "${GREEN}Switched to ${BLUE}$mode${GREEN} mode${NC}"
    echo "  ROS_MASTER_URI=$ROS_MASTER_URI"
    echo "  ROS_IP=$ROS_IP"

    # 如果脚本是被 source 执行的，自动生效；否则提示用户 source
    if [ "${BASH_SOURCE[0]}" != "$0" ]; then
        source ~/.bashrc
        echo -e "${GREEN}Current terminal updated.${NC}"
    else
        echo ""
        echo -e "${YELLOW}Run: source ~/.bashrc  (or open new terminal)${NC}"
    fi
}

do_status() {
    echo ""
    echo -e "Machine: ${BLUE}$SIDE${NC}"
    echo -e "ZeroTier: $(sudo zerotier-cli listnetworks 2>/dev/null | grep "$ZT_NETWORK_ID" | awk '{print $5" "$9}' || echo 'offline')"
    echo ""
    echo -e "Current ROS config:"
    echo "  ROS_MASTER_URI=$ROS_MASTER_URI"
    echo "  ROS_IP=$ROS_IP"
    echo ""

    if echo "$ROS_MASTER_URI" | grep -q "10\.9\.225"; then
        echo -e "Mode: ${BLUE}ZeroTier 内网穿透${NC}"
    else
        echo -e "Mode: ${GREEN}局域网${NC}"
    fi
}

do_install() {
    curl -s https://install.zerotier.com | sudo bash
    echo -e "${GREEN}Done. Next: ./$(basename "$0") join${NC}"
}

do_join() {
    command -v zerotier-cli &>/dev/null || { echo "Install first: ./$(basename "$0") install"; return 1; }
    sudo zerotier-cli join "$ZT_NETWORK_ID"
    sleep 2
    ZT_IP=$(get_zt_ip)
    echo -e "${GREEN}Joined. ZT IP: $ZT_IP${NC}"
    echo -e "${YELLOW}Go to https://my.zerotier.com/network/$ZT_NETWORK_ID -> Auth${NC}"
}

do_test() {
    local target
    if [ "$SIDE" = "jetson" ]; then
        target="${PC_IP:-10.88.168.60}"
    else
        target="${JETSON_LAN_IP:-10.88.168.44}"
    fi
    echo "Pinging $target via current network..."
    ping -c 3 "$target" && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAIL${NC}"
}

case "${1:-}" in
    config)  do_config ;;
    switch)  do_switch "${2:-}" ;;
    status)  do_status ;;
    install) do_install ;;
    join)    do_join ;;
    test)    do_test ;;
    *)
        echo ""
        echo "ROS Network Switch — LAN / ZeroTier ($SIDE)"
        echo ""
        echo "  config                      Configure LAN and ZT IPs"
        echo " ROS Network Switch ($SIDE)"
        echo ""
        echo "  switch lan    # LAN mode"
        echo "  switch zt     # ZeroTier mode"
        echo ""
        echo "Tip: source the script for auto-refresh:"
        echo "  . ./zerotier_setup.sh switch zt"
        echo "  status                      Show current mode"
        echo "  install / join              ZeroTier setup"
        echo "  test                        Ping test"
        echo ""
        echo "Quick start:"
        echo "  1. config              (configure IPs)"
        echo "  2. switch zt           (switch to ZeroTier, auto-source)"
        echo "  3. switch lan          (switch back to LAN)"
        ;;
esac
