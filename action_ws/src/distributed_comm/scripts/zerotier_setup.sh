#!/bin/bash
# ============================================================================
#  ZeroTier 分布式 ROS 网络配置脚本
#  支持局域网 + 内网穿透，自动检测当前机器并配置 ROS 环境变量
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/zt_config"

# 默认 ZeroTier Network ID
ZT_NETWORK_ID="${ZT_NETWORK_ID:-f3797ba7a828a818}"

[ -f "$CONFIG_FILE" ] && source "$CONFIG_FILE"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检测当前机器
HOSTNAME="$(hostname)"
if echo "$HOSTNAME" | grep -qi "nano\|jetson\|tegra"; then
    SIDE="jetson"
else
    SIDE="pc"
fi

check_zt() {
    if ! command -v zerotier-cli &>/dev/null; then
        echo -e "${RED}[ERROR] zerotier-cli not found${NC}"
        echo "Install: curl -s https://install.zerotier.com | sudo bash"
        return 1
    fi
    return 0
}

get_zt_ip() {
    sudo zerotier-cli listnetworks 2>/dev/null \
        | awk -v nid="$ZT_NETWORK_ID" '$0 ~ nid {split($NF,a,"/"); print a[1]}'
}

do_install() {
    echo -e "${YELLOW}Installing ZeroTier...${NC}"
    curl -s https://install.zerotier.com | sudo bash
    echo -e "${GREEN}Done.${NC}"
    echo "Next: ./$(basename "$0") join"
}

do_join() {
    check_zt || return 1
    echo -e "${YELLOW}Joining network: $ZT_NETWORK_ID${NC}"
    sudo zerotier-cli join "$ZT_NETWORK_ID"
    echo -e "${GREEN}Joined. Wait a moment...${NC}"
    sleep 3

    ZT_IP=$(get_zt_ip)
    if [ -n "$ZT_IP" ]; then
        echo -e "${GREEN}ZeroTier IP: $ZT_IP${NC}"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Go to https://my.zerotier.com/network/$ZT_NETWORK_ID${NC}"
        echo "  -> Find this device -> check the Auth box"
    else
        echo -e "${RED}[WARN] Not authorized yet.${NC}"
        echo "  Go to https://my.zerotier.com/network/$ZT_NETWORK_ID and authorize this device."
    fi
}

do_status() {
    check_zt || return 1
    sudo zerotier-cli listnetworks

    ZT_IP=$(get_zt_ip)
    if [ -n "$ZT_IP" ]; then
        echo ""
        ROS_MASTER_PORT=11311
        if nc -z -w2 "$ZT_IP" "$ROS_MASTER_PORT" 2>/dev/null; then
            echo -e "${GREEN}ROS port 11311 is reachable${NC}"
        else
            echo -e "${YELLOW}ROS port 11311 not reachable (roscore not running?)${NC}"
        fi
    fi
}

do_config() {
    echo ""
    echo "Current: $SIDE"
    echo "  ROS_MASTER_URI=$ROS_MASTER_URI"
    echo "  ROS_IP=$ROS_IP"
    echo ""

    ZT_IP=$(get_zt_ip)
    if [ -n "$ZT_IP" ]; then
        echo "Detected ZeroTier IP: $ZT_IP"
        echo ""
    fi

    if [ "$SIDE" = "jetson" ]; then
        read -p "Your ZeroTier IP [$ZT_IP]: " ip; [ -n "$ip" ] && ZT_IP="$ip"

        ROS_MASTER_URI="http://${ZT_IP}:11311"
        ROS_IP="$ZT_IP"
        ROS_HOSTNAME="$ZT_IP"

        EXPORT_STR="export ROS_MASTER_URI=$ROS_MASTER_URI
export ROS_IP=$ROS_IP
export ROS_HOSTNAME=$ROS_HOSTNAME"

        echo "$EXPORT_STR" >> ~/.bashrc
        echo -e "${GREEN}Appended to ~/.bashrc:${NC}"
        echo "$EXPORT_STR"
        echo ""
        echo "Next: source ~/.bashrc && roscore &"
    else
        read -p "Jetson ZeroTier IP [$JETSON_ZT_IP]: " jet_ip
        [ -n "$jet_ip" ] && JETSON_ZT_IP="$jet_ip"

        read -p "Your ZeroTier IP [$ZT_IP]: " my_ip
        [ -n "$my_ip" ] && ZT_IP="$my_ip"

        ROS_MASTER_URI="http://${JETSON_ZT_IP}:11311"
        ROS_IP="$ZT_IP"
        ROS_HOSTNAME="$ZT_IP"

        EXPORT_STR="export ROS_MASTER_URI=$ROS_MASTER_URI
export ROS_IP=$ROS_IP
export ROS_HOSTNAME=$ROS_HOSTNAME"

        echo "$EXPORT_STR" >> ~/.bashrc
        echo -e "${GREEN}Appended to ~/.bashrc:${NC}"
        echo "$EXPORT_STR"
        echo ""
        echo "    source ~/.bashrc && rosrun distributed_comm pc_bridge _pub_rate:=50"
    fi

    cat > "$CONFIG_FILE" << EOF
ZT_NETWORK_ID="$ZT_NETWORK_ID"
JETSON_ZT_IP="$ZT_IP"
EOF
    echo -e "${GREEN}Config saved to $CONFIG_FILE${NC}"
}

do_test() {
    echo -e "${YELLOW}Pinging Jetson via ZeroTier...${NC}"
    ping -c 3 "$JETSON_ZT_IP" 2>/dev/null && echo -e "${GREEN}OK${NC}" || echo -e "${RED}FAIL${NC}"
}

case "${1:-}" in
    install) do_install ;;
    join)    do_join ;;
    status)  do_status ;;
    config)  do_config ;;
    test)    do_test ;;
    *)
        echo ""
        echo "ZeroTier ROS Network Setup (current: $SIDE)"
        echo ""
        echo "  ./zerotier_setup.sh install    # 安装 ZeroTier (两台都要)"
        echo "  ./zerotier_setup.sh join       # 加入网络 (两台都要)"
        echo "  ./zerotier_setup.sh status     # 查看连接状态"
        echo "  ./zerotier_setup.sh config     # 配置 ROS 环境变量到 ~/.bashrc"
        echo "  ./zerotier_setup.sh test       # 测试 ZeroTier 连通性"
        echo ""
        echo "Quick start:"
        echo "  1. install -> join (both machines)"
        echo "  2. Authorize at https://my.zerotier.com"
        echo "  3. config (Jetson first, then PC)"
        echo "  4. Jetson: roscore &"
        echo "  5. PC: rosrun distributed_comm pc_bridge _pub_rate:=50"
        ;;
esac
